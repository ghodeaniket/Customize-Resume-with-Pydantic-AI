"""Tests for the customizer service."""

import pytest
from unittest.mock import AsyncMock, patch

import httpx

from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume
from resume_customizer.core.exceptions import ResumeCustomizerException
from resume_customizer.services.customizer import CustomizerService


class TestCustomizerService:
    """Tests for the customizer service."""
    
    @pytest.fixture
    def customizer_service(self):
        """Fixture for the customizer service."""
        return CustomizerService()
    
    @pytest.mark.asyncio
    async def test_analyze_resume_success(self, customizer_service, sample_resume_content, 
                                   mock_professional_profile):
        """Test successful resume analysis."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch analyze_resume function
        with patch('resume_customizer.services.customizer.analyze_resume', 
                  AsyncMock(return_value=mock_professional_profile)) as mock_analyze:
            
            # Call the function
            result = await customizer_service.analyze_resume(
                resume_content=sample_resume_content,
                http_client=mock_client
            )
            
            # Verify the analyze function was called
            mock_analyze.assert_called_once_with(
                resume_content=sample_resume_content,
                http_client=mock_client,
                model_name=None
            )
            
            # Verify the result
            assert result == mock_professional_profile
    
    @pytest.mark.asyncio
    async def test_analyze_resume_error(self, customizer_service, sample_resume_content):
        """Test resume analysis with error."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch analyze_resume function to raise an exception
        with patch('resume_customizer.services.customizer.analyze_resume', 
                  AsyncMock(side_effect=Exception("Analysis error"))) as mock_analyze:
            
            # Call the function and verify exception
            with pytest.raises(ResumeCustomizerException):
                await customizer_service.analyze_resume(
                    resume_content=sample_resume_content,
                    http_client=mock_client
                )
    
    @pytest.mark.asyncio
    async def test_analyze_job_success(self, customizer_service, sample_job_description, 
                                mock_job_requirements):
        """Test successful job analysis."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch analyze_job_description function
        with patch('resume_customizer.services.customizer.analyze_job_description', 
                  AsyncMock(return_value=mock_job_requirements)) as mock_analyze:
            
            # Call the function
            result = await customizer_service.analyze_job(
                job_description=sample_job_description,
                http_client=mock_client
            )
            
            # Verify the analyze function was called
            mock_analyze.assert_called_once_with(
                job_description=sample_job_description,
                http_client=mock_client,
                model_name=None
            )
            
            # Verify the result
            assert result == mock_job_requirements
    
    @pytest.mark.asyncio
    async def test_analyze_job_error(self, customizer_service, sample_job_description):
        """Test job analysis with error."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch analyze_job_description function to raise an exception
        with patch('resume_customizer.services.customizer.analyze_job_description', 
                  AsyncMock(side_effect=Exception("Analysis error"))) as mock_analyze:
            
            # Call the function and verify exception
            with pytest.raises(ResumeCustomizerException):
                await customizer_service.analyze_job(
                    job_description=sample_job_description,
                    http_client=mock_client
                )
    
    @pytest.mark.asyncio
    async def test_customize_success(self, customizer_service, sample_resume_content, 
                             sample_job_description, mock_optimized_resume):
        """Test successful resume customization."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch customize_resume function
        with patch('resume_customizer.services.customizer.customize_resume', 
                  AsyncMock(return_value=mock_optimized_resume)) as mock_customize:
            
            # Call the function
            optimized_resume, profile, requirements = await customizer_service.customize(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                http_client=mock_client,
                include_analysis=False
            )
            
            # Verify the customize function was called
            mock_customize.assert_called_once_with(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                http_client=mock_client,
                model_name=None
            )
            
            # Verify the result
            assert optimized_resume == mock_optimized_resume
            assert profile is None
            assert requirements is None
    
    @pytest.mark.asyncio
    async def test_customize_with_analysis(self, customizer_service, sample_resume_content, 
                                    sample_job_description, mock_optimized_resume,
                                    mock_professional_profile, mock_job_requirements):
        """Test resume customization with analysis."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch customize_resume function
        with patch('resume_customizer.services.customizer.customize_resume', 
                  AsyncMock(return_value=mock_optimized_resume)) as mock_customize:
            
            # Patch analyze_resume function
            with patch('resume_customizer.services.customizer.CustomizerService.analyze_resume', 
                      AsyncMock(return_value=mock_professional_profile)) as mock_analyze_resume:
                
                # Patch analyze_job function
                with patch('resume_customizer.services.customizer.CustomizerService.analyze_job', 
                          AsyncMock(return_value=mock_job_requirements)) as mock_analyze_job:
                    
                    # Call the function
                    optimized_resume, profile, requirements = await customizer_service.customize(
                        resume_content=sample_resume_content,
                        job_description=sample_job_description,
                        http_client=mock_client,
                        include_analysis=True
                    )
                    
                    # Verify all functions were called
                    mock_customize.assert_called_once()
                    mock_analyze_resume.assert_called_once()
                    mock_analyze_job.assert_called_once()
                    
                    # Verify the result
                    assert optimized_resume == mock_optimized_resume
                    assert profile == mock_professional_profile
                    assert requirements == mock_job_requirements
    
    @pytest.mark.asyncio
    async def test_customize_error(self, customizer_service, sample_resume_content, 
                           sample_job_description):
        """Test resume customization with error."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch customize_resume function to raise an exception
        with patch('resume_customizer.services.customizer.customize_resume', 
                  AsyncMock(side_effect=Exception("Customization error"))) as mock_customize:
            
            # Call the function and verify exception
            with pytest.raises(ResumeCustomizerException):
                await customizer_service.customize(
                    resume_content=sample_resume_content,
                    job_description=sample_job_description,
                    http_client=mock_client
                )
