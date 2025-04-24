"""Tests for the Profiler agent."""

import sys
import os

# Add the mock directory to the Python path
test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../tests'))
if test_dir not in sys.path:
    sys.path.insert(0, test_dir)

# Import AgentRunResult from our mock instead of real pydantic_ai
from mocks.pydantic_ai import AgentRunResult

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.profiler import (
    analyze_resume,
    extract_resume_text,
    profiler_agent,
    set_profiler_model
)
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError


class TestProfilerAgent:
    """Tests for the Profiler agent."""
    
    @pytest.mark.asyncio
    async def test_set_profiler_model(self, mock_agent_dependencies):
        """Test setting the profiler model."""
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Call the function
        result = await set_profiler_model(ctx)
        
        # Verify the result
        assert isinstance(result, str)
        assert mock_agent_dependencies.model_name in result
    
    @pytest.mark.asyncio
    async def test_extract_resume_text_success(self, mock_agent_dependencies):
        """Test successful resume text extraction."""
        # Create sample resume
        resume_content = "Sample resume text"
        
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Call the function
        result = await extract_resume_text(ctx, resume_content)
        
        # Verify the result
        assert result == resume_content
    
    @pytest.mark.asyncio
    async def test_extract_resume_text_error_empty(self, mock_agent_dependencies):
        """Test resume text extraction with empty content."""
        # Create empty resume
        resume_content = ""
        
        # Create run context
        ctx = MagicMock()
        ctx.deps = mock_agent_dependencies
        
        # Call the function and verify exception
        with pytest.raises(DocumentProcessingError):
            await extract_resume_text(ctx, resume_content)
    
    @pytest.mark.asyncio
    async def test_analyze_resume_success(self, sample_resume_content):
        """Test successful resume analysis."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Mock the agent run method
        mock_profile = ProfessionalProfile(
            core_identity="Software Engineer with backend expertise",
            technical_skills=[],
            soft_skills=[],
            work_experience=[],
            projects=[],
            education=[],
            contribution_patterns="Focuses on performance optimization",
            interests=["Software Engineering", "Backend Development"],
            work_style="Collaborative and detail-oriented",
            career_highlights=[]
        )
        
        mock_result = MagicMock(spec=AgentRunResult)
        mock_result.output = mock_profile
        
        # Patch the agent run method
        with patch('resume_customizer.agents.profiler.profiler_agent.run', 
                  AsyncMock(return_value=mock_result)) as mock_run:
            
            # Call the function
            result = await analyze_resume(
                resume_content=sample_resume_content,
                http_client=mock_client
            )
            
            # Verify the agent was called
            mock_run.assert_called_once()
            
            # Verify the result
            assert isinstance(result, ProfessionalProfile)
            assert result == mock_profile
    
    @pytest.mark.asyncio
    async def test_analyze_resume_agent_error(self, sample_resume_content):
        """Test resume analysis with agent error."""
        # Mock the HTTP client
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # Patch the agent run method to raise an exception
        with patch('resume_customizer.agents.profiler.profiler_agent.run', 
                  AsyncMock(side_effect=Exception("Agent error"))) as mock_run:
            
            # Call the function and verify exception
            with pytest.raises(AgentError):
                await analyze_resume(
                    resume_content=sample_resume_content,
                    http_client=mock_client
                )
