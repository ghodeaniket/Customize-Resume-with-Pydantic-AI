"""Strategist agent implementation for Resume Customizer."""
from typing import Dict, List, Optional, Union, Tuple

from pydantic_ai import RunContext
from pydantic_ai.usage import Usage, UsageLimits

from agents.base import BaseAgent
from agents.models.job import JobRequirements
from agents.models.profile import ProfessionalProfile
from agents.models.resume import OptimizedResume, ResumeFormat
from agents.profiler import ProfilerAgent
from agents.researcher import ResearcherAgent
from core.logging import LoggerMixin
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager


class StrategistAgent(BaseAgent):
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
        super().__init__(prompt_manager, "strategist", OptimizedResume)
        self.profiler_agent = profiler_agent
        self.researcher_agent = researcher_agent
        
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
                usage=ctx.usage if hasattr(ctx, 'usage') else None,
                usage_limits=ctx.usage_limits if hasattr(ctx, 'usage_limits') else None
            )
        
        # Tool for getting resume insights from Profiler agent
        @self.agent.tool
        async def get_resume_insights(
            ctx: RunContext[ResumeCustomizerDeps], 
            resume_content: str
        ) -> ProfessionalProfile:
            """Delegate resume analysis to the Profiler agent."""
            self.log_info("Delegating resume analysis to Profiler agent")
            
            # Validate input
            if not resume_content or not isinstance(resume_content, str):
                self.log_error(f"Invalid resume_content: {type(resume_content)}")
                raise ValueError("resume_content must be a non-empty string")
                
            # Process the resume
            try:
                profile = await self.profiler_agent.analyze_resume(
                    resume_content,
                    deps=ctx.deps,
                    usage=ctx.usage if hasattr(ctx, 'usage') else None,
                    usage_limits=ctx.usage_limits if hasattr(ctx, 'usage_limits') else None
                )
                self.log_info("Resume analysis complete")
                return profile
            except Exception as e:
                self.log_error(f"Error analyzing resume: {str(e)}")
                raise e
    
    def _get_fallback_prompt(self) -> str:
        """Get fallback system prompt for strategist agent.
        
        Returns:
            str: Fallback system prompt
        """
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
    
    @LoggerMixin.log_operation("resume_optimization")
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
        prompt = (
            f"Optimize this resume for the provided job description. "
            f"Return the optimized resume in {output_format.value} format.\n\n"
            f"Resume content:\n{resume_content[:500]}...\n\n"
            f"Job description:\n{job_description[:500]}..."
        )
        
        # Run the agent
        optimized_resume = await self.run(
            prompt,
            deps=deps,
            usage=usage,
            usage_limits=usage_limits,
            extra_context={
                "operation": "optimize_resume",
                "output_format": output_format.value,
                "resume_length": len(resume_content),
                "job_description_length": len(job_description)
            }
        )
        
        # Ensure the format is set correctly
        if optimized_resume.format != output_format:
            optimized_resume.format = output_format
        
        return optimized_resume
