"""Tests for the researcher agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.researcher import ResearcherAgent
from agents.models.job import JobRequirements
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager
from pydantic_ai import RunOutput


@pytest.mark.asyncio
async def test_researcher_agent_init(prompt_manager: PromptManager) -> None:
    """Test researcher agent initialization.
    
    Args:
        prompt_manager: Prompt manager instance
    """
    # Initialize researcher agent
    agent = ResearcherAgent(prompt_manager=prompt_manager)
    
    # Check agent properties
    assert agent.prompt_manager == prompt_manager
    assert agent.agent is not None


@pytest.mark.asyncio
async def test_researcher_get_system_prompt(prompt_manager: PromptManager) -> None:
    """Test getting system prompt.
    
    Args:
        prompt_manager: Prompt manager instance
    """
    # Add a template to the prompt manager
    prompt_manager.add_template(
        agent_name="researcher",
        template=MagicMock(
            version="1.0.0",
            template="Test researcher prompt",
            description="Test description"
        )
    )
    
    # Initialize researcher agent
    agent = ResearcherAgent(prompt_manager=prompt_manager)
    
    # Get system prompt
    prompt = agent._get_system_prompt()
    
    # Check prompt
    assert prompt == "Test researcher prompt"


@pytest.mark.asyncio
async def test_researcher_agent_analyze_job_description_with_mock(
    prompt_manager: PromptManager,
    sample_job_description: str,
    deps: ResumeCustomizerDeps
) -> None:
    """Test analyzing a job description with a mocked agent.
    
    Args:
        prompt_manager: Prompt manager instance
        sample_job_description: Sample job description content
        deps: Agent dependencies
    """
    # Initialize researcher agent
    agent = ResearcherAgent(prompt_manager=prompt_manager)
    
    # Create mock result
    mock_requirements = JobRequirements(
        company_profile="Tech company hiring for backend team",
        core_requirements=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        supplementary_attributes=["GraphQL", "Machine Learning"],
        hidden_expectations="Looking for a technical leader who can mentor others",
        application_strategy="Emphasize Python backend experience and FastAPI",
        keywords=["Python", "FastAPI", "microservices", "REST API", "PostgreSQL"],
        tech_stack=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "AWS"]
    )
    mock_result = RunOutput(output=mock_requirements)
    
    # Mock the agent run method
    with patch.object(agent.agent, 'run', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result
        
        # Analyze job description
        requirements = await agent.analyze_job_description(sample_job_description, deps)
        
        # Check that the agent was called with the right arguments
        mock_run.assert_called_once_with(
            sample_job_description,
            deps=deps,
            usage=None,
            usage_limits=None
        )
        
        # Check the result
        assert requirements == mock_requirements
        assert "FastAPI" in requirements.core_requirements
        assert "Python" in requirements.core_requirements
        assert "PostgreSQL" in requirements.core_requirements
