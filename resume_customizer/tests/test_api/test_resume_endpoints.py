"""Tests for the resume API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import status
from fastapi.testclient import TestClient

from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.resume import OptimizedResume
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError


class TestResumeEndpoints:
    """Tests for the resume API endpoints."""
    
    def test_analyze_resume_success(self, client: TestClient, sample_resume_content, mock_professional_profile):
        """Test successful resume analysis endpoint."""
        # Mock the analyze_resume function
        with patch('resume_customizer.api.endpoints.resumes.analyze_resume',
                  AsyncMock(return_value=mock_professional_profile)) as mock_analyze:
            
            # Make the request
            response = client.post(
                "/api/v1/resumes/analyze",
                data={"resume_content": sample_resume_content},
                headers={"X-API-Key": "development-secret-key-change-in-production"}
            )
            
            # Verify the response
            assert response.status_code == status.HTTP_200_OK
            
            # Verify the response data
            data = response.json()
            assert "profile" in data
            assert data["profile"]["core_identity"] == mock_professional_profile.core_identity
            
            # Verify the function was called
            mock_analyze.assert_called_once()
    
    def test_analyze_resume_unauthorized(self, client: TestClient, sample_resume_content):
        """Test resume analysis endpoint with invalid API key."""
        # Make the request with invalid API key
        response = client.post(
            "/api/v1/resumes/analyze",
            data={"resume_content": sample_resume_content},
            headers={"X-API-Key": "invalid-key"}
        )
        
        # Verify the response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_analyze_resume_document_error(self, client: TestClient, sample_resume_content):
        """Test resume analysis endpoint with document processing error."""
        # Mock the analyze_resume function to raise DocumentProcessingError
        with patch('resume_customizer.api.endpoints.resumes.analyze_resume',
                  AsyncMock(side_effect=DocumentProcessingError("Document error"))) as mock_analyze:
            
            # Make the request
            response = client.post(
                "/api/v1/resumes/analyze",
                data={"resume_content": sample_resume_content},
                headers={"X-API-Key": "development-secret-key-change-in-production"}
            )
            
            # Verify the response
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            # Verify the error message
            data = response.json()
            assert "detail" in data
            assert "Document error" in data["detail"]
    
    def test_analyze_resume_agent_error(self, client: TestClient, sample_resume_content):
        """Test resume analysis endpoint with agent error."""
        # Mock the analyze_resume function to raise AgentError
        with patch('resume_customizer.api.endpoints.resumes.analyze_resume',
                  AsyncMock(side_effect=AgentError("Agent error", "ProfilerAgent"))) as mock_analyze:
            
            # Make the request
            response = client.post(
                "/api/v1/resumes/analyze",
                data={"resume_content": sample_resume_content},
                headers={"X-API-Key": "development-secret-key-change-in-production"}
            )
            
            # Verify the response
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Verify the error message
            data = response.json()
            assert "detail" in data
            assert "Agent error" in data["detail"]
    
    def test_analyze_job_success(self, client: TestClient, sample_job_description, mock_job_requirements):
        """Test successful job analysis endpoint."""
        # Mock the analyze_job_description function
        with patch('resume_customizer.api.endpoints.resumes.analyze_job_description',
                  AsyncMock(return_value=mock_job_requirements)) as mock_analyze:
            
            # Make the request
            response = client.post(
                "/api/v1/resumes/analyze-job",
                data={"job_description": sample_job_description},
                headers={"X-API-Key": "development-secret-key-change-in-production"}
            )
            
            # Verify the response
            assert response.status_code == status.HTTP_200_OK
            
            # Verify the response data
            data = response.json()
            assert "requirements" in data
            
            # Verify the function was called
            mock_analyze.assert_called_once()
    
    def test_customize_resume_success(self, client: TestClient, sample_resume_content, 
                               sample_job_description, mock_optimized_resume):
        """Test successful resume customization endpoint."""
        # Mock the customize_resume function
        with patch('resume_customizer.api.endpoints.resumes.customize_resume',
                  AsyncMock(return_value=mock_optimized_resume)) as mock_customize:
            
            # Make the request
            response = client.post(
                "/api/v1/resumes/customize",
                data={
                    "resume_content": sample_resume_content,
                    "job_description": sample_job_description,
                    "include_analysis": "false"
                },
                headers={"X-API-Key": "development-secret-key-change-in-production"}
            )
            
            # Verify the response
            assert response.status_code == status.HTTP_200_OK
            
            # Verify the response data
            data = response.json()
            assert "optimized_resume" in data
            assert "profile" not in data
            assert "requirements" not in data
            
            # Verify the function was called
            mock_customize.assert_called_once()
    
    def test_customize_resume_with_analysis(self, client: TestClient, sample_resume_content,
                                    sample_job_description, mock_optimized_resume,
                                    mock_professional_profile, mock_job_requirements):
        """Test resume customization endpoint with analysis."""
        # Mock the customize_resume function
        with patch('resume_customizer.api.endpoints.resumes.customize_resume',
                  AsyncMock(return_value=mock_optimized_resume)) as mock_customize:
            
            # Mock the analyze_resume function
            with patch('resume_customizer.api.endpoints.resumes.analyze_resume',
                      AsyncMock(return_value=mock_professional_profile)) as mock_analyze_resume:
                
                # Mock the analyze_job_description function
                with patch('resume_customizer.api.endpoints.resumes.analyze_job_description',
                          AsyncMock(return_value=mock_job_requirements)) as mock_analyze_job:
                    
                    # Make the request
                    response = client.post(
                        "/api/v1/resumes/customize",
                        data={
                            "resume_content": sample_resume_content,
                            "job_description": sample_job_description,
                            "include_analysis": "true"
                        },
                        headers={"X-API-Key": "development-secret-key-change-in-production"}
                    )
                    
                    # Verify the response
                    assert response.status_code == status.HTTP_200_OK
                    
                    # Verify the response data
                    data = response.json()
                    assert "optimized_resume" in data
                    assert "profile" in data
                    assert "requirements" in data
                    
                    # Verify the functions were called
                    mock_customize.assert_called_once()
                    mock_analyze_resume.assert_called_once()
                    mock_analyze_job.assert_called_once()
