"""Researcher agent implementation for Resume Customizer."""
from typing import Dict, List, Optional, Union

from pydantic_ai import RunContext
from pydantic_ai.usage import Usage, UsageLimits

from agents.base import BaseAgent
from agents.models.job import JobRequirements
from infrastructure.ai_provider import ResumeCustomizerDeps, PromptManager


class ResearcherAgent(BaseAgent):
    """Agent for analyzing job descriptions to extract requirements."""
    
    def __init__(self, prompt_manager: PromptManager):
        """Initialize researcher agent.
        
        Args:
            prompt_manager: Manager for prompt templates
        """
        super().__init__(prompt_manager, "researcher", JobRequirements)
        
        # Tool for fetching job descriptions from URLs
        @self.agent.tool
        async def fetch_job_description(
            ctx: RunContext[ResumeCustomizerDeps], 
            url: str
        ) -> str:
            """Fetch job description content from a URL."""
            try:
                response = await ctx.deps.http_client.get(url)
                response.raise_for_status()
                return response.text
            except Exception as e:
                self.log_error(f"Error fetching job description: {str(e)}")
                return f"Error fetching job description: {str(e)}"
    
    def _get_fallback_prompt(self) -> str:
        """Get fallback system prompt for researcher agent.
        
        Returns:
            str: Fallback system prompt
        """
        return (
            "You are Eliza Chen, a Tech Job Description Strategist with 13+ years of "
            "experience in technical recruitment and talent acquisition at FAANG companies. "
            "\n\n"
            "Your task is to analyze job descriptions to extract key requirements and "
            "insights that will help candidates optimize their resumes. You focus on "
            "identifying both explicit requirements and implicit expectations. "
            "\n\n"
            "Extract all relevant job information and organize it into a structured "
            "requirements profile following the JobRequirements schema. Be specific, "
            "detailed, and focus on actionable insights that will help candidates "
            "tailor their applications."
        )
    
    async def analyze_job_description(
        self, 
        job_description: str,
        deps: ResumeCustomizerDeps,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None
    ) -> JobRequirements:
        """Analyze a job description and extract requirements.
        
        Args:
            job_description: Text content of the job description
            deps: Agent dependencies
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            
        Returns:
            JobRequirements: Structured requirements from the job description
        """
        return await self.run(
            job_description,
            deps=deps,
            usage=usage,
            usage_limits=usage_limits,
            extra_context={"operation": "analyze_job_description"}
        )
    
    async def analyze_job_url(
        self, 
        job_url: str,
        deps: ResumeCustomizerDeps,
        usage: Optional[Usage] = None,
        usage_limits: Optional[UsageLimits] = None
    ) -> JobRequirements:
        """Analyze a job description from URL and extract requirements.
        
        Args:
            job_url: URL of the job posting
            deps: Agent dependencies
            usage: Optional usage tracker
            usage_limits: Optional usage limits
            
        Returns:
            JobRequirements: Structured requirements from the job description
        """
        # Create a modified prompt instructing to fetch the URL
        modified_prompt = f"Fetch and analyze the job description from this URL: {job_url}"
        
        return await self.run(
            modified_prompt,
            deps=deps,
            usage=usage,
            usage_limits=usage_limits,
            extra_context={"operation": "analyze_job_url", "url": job_url}
        )
