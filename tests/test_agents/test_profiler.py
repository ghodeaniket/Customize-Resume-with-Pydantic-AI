"""Tests for the profiler agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.profiler import ProfilerAgent
from agents.models.profile import ProfessionalProfile
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager
from pydantic_ai import RunOutput


@pytest.mark.asyncio
async def test_profiler_agent_init(prompt_manager: PromptManager) -> None:
    """Test profiler agent initialization.
    
    Args:
        prompt_manager: Prompt manager instance
    """
    # Initialize profiler agent
    agent = ProfilerAgent(prompt_manager=prompt_manager)
    
    # Check agent properties
    assert agent.prompt_manager == prompt_manager
    assert agent.agent is not None


@pytest.mark.asyncio
async def test_profiler_get_system_prompt(prompt_manager: PromptManager) -> None:
    """Test getting system prompt.
    
    Args:
        prompt_manager: Prompt manager instance
    """
    # Add a template to the prompt manager
    prompt_manager.add_template(
        agent_name="profiler",
        template=MagicMock(
            version="1.0.0",
            template="Test profiler prompt",
            description="Test description"
        )
    )
    
    # Initialize profiler agent
    agent = ProfilerAgent(prompt_manager=prompt_manager)
    
    # Get system prompt
    prompt = agent._get_system_prompt()
    
    # Check prompt
    assert prompt == "Test profiler prompt"


@pytest.mark.asyncio
async def test_profiler_agent_analyze_resume_with_mock(
    prompt_manager: PromptManager,
    sample_resume: str,
    deps: ResumeCustomizerDeps
) -> None:
    """Test analyzing a resume with a mocked agent.
    
    Args:
        prompt_manager: Prompt manager instance
        sample_resume: Sample resume content
        deps: Agent dependencies
    """
    # Initialize profiler agent
    agent = ProfilerAgent(prompt_manager=prompt_manager)
    
    # Create mock result
    mock_profile = ProfessionalProfile(
        core_identity="Senior Software Engineer with full-stack expertise",
        technical_skills=["Python", "JavaScript", "TypeScript", "FastAPI", "React"],
        soft_skills=["Mentoring", "Leadership"],
        projects=[],
        contribution_patterns="Technical leadership and performance optimization",
        interests=["Software Architecture", "Cloud Computing"],
        work_style="Collaborative and mentorship-oriented",
        experience_level="Senior"
    )
    mock_result = RunOutput(output=mock_profile)
    
    # Mock the agent run method
    with patch.object(agent.agent, 'run', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result
        
        # Analyze resume
        profile = await agent.analyze_resume(sample_resume, deps)
        
        # Check that the agent was called with the right arguments
        mock_run.assert_called_once_with(
            sample_resume,
            deps=deps,
            usage=None,
            usage_limits=None
        )
        
        # Check the result
        assert profile == mock_profile
        assert profile.core_identity == "Senior Software Engineer with full-stack expertise"
        assert "Python" in profile.technical_skills
        assert "FastAPI" in profile.technical_skills
