"""Tests for the Strategist agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from pydantic_ai import AgentRunResult

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume, ResumeFormat, ResumeOptimizationSummary
from resume_customizer.agents.strategist import (
    customize_resume,
    get_job_insights,
    get_resume_insights,
    strategist_agent,
    set_strategist_model
)
from resume_customizer.core.exceptions import AgentError


class TestStrategistAgent:
    """Tests for the Strategist agent."""
    
    @pytest.mark.asyncio
    async def test_set_strategist_model(self, mock_agent_dependencies):
        """Test setting the strategist model."""
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Call the function
        result = await set_strategist_model(ctx)
        
        # Verify the result
        assert isinstance(result, str)
        assert mock_agent_dependencies.model_name in result
    
    @pytest.mark.asyncio
    async def test_get_job_insights(self, mock_agent_dependencies, mock_job_requirements):
        """Test getting job insights."""
        # Create sample job description
        job_description = "Sample job description"
        
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Patch analyze_job_description function
        with patch('resume_customizer.agents.strategist.analyze_job_description', 
                  AsyncMock(return_value=mock_job_requirements)) as mock_analyze:
            
            # Call the function
            result = await get_job_insights(ctx, job_description)
            
            # Verify the analyze function was called
            mock_analyze.assert_called_once_with(
                job_description=job_description,
                http_client=ctx.deps.http_client,
                model_name=ctx.deps.model_name
            )
            
            # Verify the result
            assert result == mock_job_requirements
    
    @pytest.mark.asyncio
    async def test_get_resume_insights(self, mock_agent_dependencies, mock_professional_profile):
        """Test getting resume insights."""
        # Create sample resume content
        resume_content = "Sample resume content"
        
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Patch analyze_resume function
        with patch('resume_customizer.agents.strategist.analyze_resume', 
                  AsyncMock(return_value=mock_professional_profile)) as mock_analyze:
            
            # Call the function
            result = await get_resume_insights(ctx, resume_content)
            
            # Verify the analyze function was called
            mock_analyze.assert_called_once_with(
                resume_content=resume_content,
                http_client=ctx.deps.http_client,
                model_name=ctx.deps.model_name
            )
            
            # Verify the result
            assert result == mock_professional_profile
    
    @pytest.mark.asyncio
    async def test_customize_resume_success(self, sample_resume_content, sample_job_description):
        """Test successful resume customization."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Create sample optimized resume content
        markdown_content = "# John Doe\n\nSenior Software Engineer"
        
        # Mock agent run result
        mock_result = MagicMock(spec=AgentRunResult)
        mock_result.output = markdown_content
        
        # Patch the agent run method
        with patch('resume_customizer.agents.strategist.strategist_agent.run', 
                  AsyncMock(return_value=mock_result)) as mock_run:
            
            # Call the function
            result = await customize_resume(
                resume_content=sample_resume_content,
                job_description=sample_job_description,
                http_client=mock_client
            )
            
            # Verify the agent was called
            mock_run.assert_called_once()
            
            # Verify the result
            assert isinstance(result, OptimizedResume)
            assert result.content == markdown_content
            assert result.format == ResumeFormat.MARKDOWN
            assert isinstance(result.optimization_summary, ResumeOptimizationSummary)
    
    @pytest.mark.asyncio
    async def test_customize_resume_agent_error(self, sample_resume_content, sample_job_description):
        """Test resume customization with agent error."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch the agent run method to raise an exception
        with patch('resume_customizer.agents.strategist.strategist_agent.run', 
                  AsyncMock(side_effect=Exception("Agent error"))) as mock_run:
            
            # Call the function and verify exception
            with pytest.raises(AgentError):
                await customize_resume(
                    resume_content=sample_resume_content,
                    job_description=sample_job_description,
                    http_client=mock_client
                )
