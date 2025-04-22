"""Tests for the Researcher agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from pydantic_ai import AgentRunResult

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.job import JobRequirements, CompanyContext, PositionDetails
from resume_customizer.agents.researcher import (
    analyze_job_description,
    fetch_job_description,
    researcher_agent,
    set_researcher_model
)
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError


class TestResearcherAgent:
    """Tests for the Researcher agent."""
    
    @pytest.mark.asyncio
    async def test_set_researcher_model(self, mock_agent_dependencies):
        """Test setting the researcher model."""
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Call the function
        result = await set_researcher_model(ctx)
        
        # Verify the result
        assert isinstance(result, str)
        assert mock_agent_dependencies.model_name in result
    
    @pytest.mark.asyncio
    async def test_fetch_job_description_success(self, mock_agent_dependencies):
        """Test successful job description fetching."""
        # Create sample response
        mock_response = MagicMock()
        mock_response.text = "Sample job description"
        mock_response.raise_for_status = AsyncMock()
        
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        ctx.deps.http_client.get = AsyncMock(return_value=mock_response)
        
        # Call the function
        job_url = "https://example.com/job"
        result = await fetch_job_description(ctx, job_url)
        
        # Verify the result
        assert result == "Sample job description"
        ctx.deps.http_client.get.assert_called_once_with(
            job_url, follow_redirects=True, timeout=30.0
        )
    
    @pytest.mark.asyncio
    async def test_fetch_job_description_invalid_url(self, mock_agent_dependencies):
        """Test job description fetching with invalid URL."""
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Call the function with invalid URL and verify exception
        with pytest.raises(ValueError):
            await fetch_job_description(ctx, "invalid-url")
    
    @pytest.mark.asyncio
    async def test_fetch_job_description_http_error(self, mock_agent_dependencies):
        """Test job description fetching with HTTP error."""
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Mock HTTP error
        http_error = httpx.HTTPError("HTTP Error")
        ctx.deps.http_client.get = AsyncMock(side_effect=http_error)
        
        # Call the function and verify exception
        with pytest.raises(DocumentProcessingError):
            await fetch_job_description(ctx, "https://example.com/job")
    
    @pytest.mark.asyncio
    async def test_analyze_job_description_success(self, sample_job_description):
        """Test successful job description analysis."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Create sample job requirements
        mock_job_requirements = JobRequirements(
            company_profile=CompanyContext(
                name="TechInnovate",
                industry="Technology"
            ),
            position=PositionDetails(
                title="Senior Backend Engineer",
                responsibilities=["Design backend services"]
            ),
            core_requirements=[],
            supplementary_attributes=[],
            hidden_expectations=["Leadership potential"],
            application_strategy="Emphasize Python expertise",
            keywords=["Python", "FastAPI", "Backend"]
        )
        
        # Mock agent run result
        mock_result = MagicMock(spec=AgentRunResult)
        mock_result.output = mock_job_requirements
        
        # Patch the agent run method
        with patch('resume_customizer.agents.researcher.researcher_agent.run', 
                  AsyncMock(return_value=mock_result)) as mock_run:
            
            # Call the function
            result = await analyze_job_description(
                job_description=sample_job_description,
                http_client=mock_client
            )
            
            # Verify the agent was called
            mock_run.assert_called_once()
            
            # Verify the result
            assert isinstance(result, JobRequirements)
            assert result == mock_job_requirements
    
    @pytest.mark.asyncio
    async def test_analyze_job_description_agent_error(self, sample_job_description):
        """Test job description analysis with agent error."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch the agent run method to raise an exception
        with patch('resume_customizer.agents.researcher.researcher_agent.run', 
                  AsyncMock(side_effect=Exception("Agent error"))) as mock_run:
            
            # Call the function and verify exception
            with pytest.raises(AgentError):
                await analyze_job_description(
                    job_description=sample_job_description,
                    http_client=mock_client
                )
