"""Tests for the strategist agent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.strategist import StrategistAgent
from agents.profiler import ProfilerAgent
from agents.researcher import ResearcherAgent
from agents.models.profile import ProfessionalProfile
from agents.models.job import JobRequirements
from agents.models.resume import OptimizedResume, ResumeFormat
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager, PromptTemplate


@pytest.mark.asyncio
async def test_strategist_agent_init(
    profiler_agent: ProfilerAgent,
    researcher_agent: ResearcherAgent,
    prompt_manager: PromptManager
) -> None:
    """Test strategist agent initialization.
    
    Args:
        profiler_agent: Profiler agent instance
        researcher_agent: Researcher agent instance
        prompt_manager: Prompt manager instance
    """
    # Initialize strategist agent
    agent = StrategistAgent(
        profiler_agent=profiler_agent,
        researcher_agent=researcher_agent,
        prompt_manager=prompt_manager
    )
    
    # Check agent properties
    assert agent.profiler_agent == profiler_agent
    assert agent.researcher_agent == researcher_agent
    assert agent.prompt_manager == prompt_manager
    assert agent.agent is not None


@pytest.mark.asyncio
async def test_strategist_get_system_prompt(
    profiler_agent: ProfilerAgent,
    researcher_agent: ResearcherAgent,
    prompt_manager: PromptManager
) -> None:
    """Test getting system prompt.
    
    Args:
        profiler_agent: Profiler agent instance
        researcher_agent: Researcher agent instance
        prompt_manager: Prompt manager instance
    """
    # Add a template to the prompt manager
    prompt_manager.add_template(
        agent_name="strategist",
        template=PromptTemplate(
            version="1.0.0",
            template="Test strategist prompt",
            description="Test description"
        )
    )
    
    # Initialize strategist agent
    agent = StrategistAgent(
        profiler_agent=profiler_agent,
        researcher_agent=researcher_agent,
        prompt_manager=prompt_manager
    )
    
    # Get system prompt
    prompt = agent._get_system_prompt()
    
    # Check prompt
    assert prompt == "Test strategist prompt"


@pytest.mark.asyncio
async def test_strategist_agent_optimize_resume_with_mock(
    profiler_agent: ProfilerAgent,
    researcher_agent: ResearcherAgent,
    prompt_manager: PromptManager,
    sample_resume: str,
    sample_job_description: str,
    deps: ResumeCustomizerDeps
) -> None:
    """Test optimizing a resume with a mocked agent.
    
    Args:
        profiler_agent: Profiler agent instance
        researcher_agent: Researcher agent instance
        prompt_manager: Prompt manager instance
        sample_resume: Sample resume content
        sample_job_description: Sample job description content
        deps: Agent dependencies
    """
    # Initialize strategist agent
    agent = StrategistAgent(
        profiler_agent=profiler_agent,
        researcher_agent=researcher_agent,
        prompt_manager=prompt_manager
    )
    
    # Create mock result
    mock_optimized_resume = OptimizedResume(
        content="# Jane Smith\n\n## Senior Software Engineer\n\n...",
        format=ResumeFormat.MARKDOWN,
        sections=[],
        optimizations=[
            "Emphasized Python and FastAPI experience",
            "Highlighted microservices architecture experience",
            "Added PostgreSQL optimization details"
        ],
        keywords_included=["Python", "FastAPI", "microservices", "PostgreSQL"],
        ats_score=95.0
    )
    
    # Create a mock result object
    class MockRunResult:
        def __init__(self, output):
            self.output = output
    
    mock_result = MockRunResult(output=mock_optimized_resume)
    
    # Mock the agent run method
    with patch.object(agent.agent, 'run', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result
        
        # Optimize resume
        optimized = await agent.optimize_resume(
            resume_content=sample_resume,
            job_description=sample_job_description,
            deps=deps
        )
        
        # Check that the agent was called
        assert mock_run.called
        
        # Check the result
        assert optimized == mock_optimized_resume
        assert optimized.format == ResumeFormat.MARKDOWN
        assert "Emphasized Python and FastAPI experience" in optimized.optimizations
        assert "Python" in optimized.keywords_included
        assert "FastAPI" in optimized.keywords_included
