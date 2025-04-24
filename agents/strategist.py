"""Strategist agent implementation for Resume Customizer."""
from typing import Dict, List, Optional, Union, Tuple

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import Usage, UsageLimits

from agents.models.job import JobRequirements
from agents.models.profile import ProfessionalProfile
from agents.models.resume import OptimizedResume, ResumeFormat
from agents.profiler import ProfilerAgent
from agents.researcher import ResearcherAgent
from core.logging import LoggerMixin
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager


class StrategistAgent(LoggerMixin):
    """Agent for optimizing resumes based on profiles and job analyses."""
    
    def __init__(
        self, 
        profiler_agent: ProfilerAgent,
        researcher_agent: ResearcherAgent,
        prompt_manager: PromptManager
    ):
        """Initialize strategist agent.
        
        Args:
            profiler_agent: Profiler agent instance
            researcher_agent: Researcher agent instance
            prompt_manager: Manager for prompt templates
        """
        self.profiler_agent = profiler_agent
        self.researcher_agent = researcher_agent
        self.prompt_manager = prompt_manager
        
        # Initialize the Pydantic AI agent
        self.agent = Agent(
            'test',  # Use test model for unit tests
            deps_type=ResumeCustomizerDeps,
            output_type=OptimizedResume,
            system_prompt=self._get_system_prompt(),
        )
        
        # Set dynamic system prompt for model configuration
        @self.agent.system_prompt
        async def set_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
            """Set the specific model to use via dynamic system prompt."""
            return f"You will be using the {ctx.deps.model_name} model to optimize resumes."
        
        # Tool for getting job insights from Researcher agent
        @self.agent.tool
        async def get_job_insights(
            ctx: RunContext[ResumeCustomizerDeps], 
            job_description: str
        ) -> JobRequirements:
            """Delegate job description analysis to the Researcher agent."""
            self.log_info("Delegating job analysis to Researcher agent")
            return await self.researcher_agent.analyze_job_description(
                job_description,
                deps=ctx.deps,
                usage=ctx.usage,
                usage_limits=ctx.usage_limits
            )
        
        # Tool for getting resume insights from Profiler agent
        @self.agent.tool
        async def get_resume_insights(
            ctx: RunContext[ResumeCustomizerDeps], 
            resume_content: str
        ) -> ProfessionalProfile:
            """Delegate resume analysis to the Profiler agent."""
            self.log_info("Delegating resume analysis to Profiler agent")
            return await self.profiler_agent.analyze_resume(
                resume_content,
                deps=ctx.deps,
                usage=ctx.usage,
                usage_limits=ctx.usage_limits
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the strategist agent.
        
        Returns:
            str: System prompt
        """
        try:
            return self.prompt_manager.get_template("strategist", "latest")
        except Exception:
            # Fallback to default prompt if template not found
            self.log_info("Using default strategist prompt")
            return (
                "You are CareerPeak, a world-class resume strategist with 15+ years of "
                "experience helping engineering leaders secure positions at top tech companies. "
                "\n\n"
                "Your task is to optimize a resume for a specific job description by analyzing "
                "both the candidate's profile and the job requirements, then creating a "
                "tailored resume that highlights the most relevant qualifications. "
                "\n\n"
                "First, use your tools to get insights about both the resume and job description. "
                "Then, create an optimized resume that aligns the candidate's experience with the "
                "job requirements. Follow these principles: "
                "\n"
                "1. Prioritize relevant skills and experiences "
                "2. Use keywords from the job description "
                "3. Quantify achievements where possible "
                "4. Remove irrelevant information "
                "5. Optimize for both human readers and ATS systems "
                "\n\n"
                "Return the optimized resume in the requested format along with metadata about "
                "your optimizations."
            )
    
    async def optimize_resume(
        self, 
        resume_content: str,
        job_description: str,
        deps: ResumeCustomizerDeps,
        output_format: ResumeFormat = ResumeFormat.MARKDOWN,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None
    ) -> OptimizedResume:
        """Optimize a resume for a specific job description.
        
        Args:
            resume_content: Text content of the resume
            job_description: Text content of the job description
            deps: Agent dependencies
            output_format: Desired output format
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            
        Returns:
            OptimizedResume: Optimized resume with metadata
        """
        self.log_info("Starting resume optimization process")
        
        prompt = (
            f"Optimize this resume for the provided job description. "
            f"Return the optimized resume in {output_format.value} format.\n\n"
            f"Resume content:\n{resume_content[:500]}...\n\n"
            f"Job description:\n{job_description[:500]}..."
        )
        
        result = await self.agent.run(
            prompt,
            deps=deps,
            usage=usage,
            usage_limits=usage_limits
        )
        
        optimized_resume = result.output
        
        # Ensure the format is set correctly
        if optimized_resume.format != output_format:
            optimized_resume.format = output_format
        
        self.log_info("Resume optimization complete")
        return optimized_resume
