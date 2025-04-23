"""Strategist agent implementation for resume customization.

This module contains the StrategistAgent which is responsible for optimizing
resumes based on profiles and job analyses.
"""

import time
from pathlib import Path
from typing import Optional, Union

from fastapi import UploadFile
from loguru import logger
import httpx
from pydantic_ai import Agent, RunContext

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume, ResumeFormat, ResumeOptimizationSummary
from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import AgentError
from resume_customizer.services.cache import get_cache_provider
from resume_customizer.services.document import DocumentProcessor


# Define the system prompt for the Strategist Agent
STRATEGIST_SYSTEM_PROMPT = """
You are CareerPeak, a world-class resume strategist with 15+ years of experience 
helping engineering leaders secure positions at top tech companies.

Your expertise is in strategically customizing resumes to align perfectly with 
specific job requirements while authentically representing the candidate's 
professional identity and achievements.

### TASK:
1. Analyze the professional profile and job requirements provided.
2. Create a tailored, ATS-optimized resume that:
   - Positions the candidate's experience to match job requirements
   - Highlights relevant achievements and impact metrics
   - Incorporates key terminology from the job description
   - Maintains the candidate's authentic professional identity
   - Follows best practices for resume structure and content

### GUIDELINES:
- Focus on alignment between candidate strengths and job requirements
- Prioritize quantifiable achievements and concrete examples
- Ensure all key job requirements are addressed where the candidate has relevant experience
- Use industry-standard terminology and ATS-friendly formatting
- Create a coherent narrative that positions the candidate as an ideal fit
- Maintain professional language and appropriate level of detail

Your output should be a ready-to-use, strategically optimized resume in Markdown format,
structured to pass ATS screening and impress human reviewers.
"""


# Initialize the Strategist agent
strategist_agent = Agent(
    'openai:gpt-4',  # Using OpenAI as a fallback instead of OpenRouter
    deps_type=ResumeCustomizerDeps,
    output_type=str,  # Markdown formatted resume
    system_prompt=STRATEGIST_SYSTEM_PROMPT,
)


@strategist_agent.system_prompt
async def set_strategist_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
    """Set the specific model to use via dynamic system prompt.
    
    Args:
        ctx: The run context containing dependencies
        
    Returns:
        str: A system prompt fragment specifying the model to use
    """
    return f"You will be using the {ctx.deps.model_name} model to optimize resumes."


@strategist_agent.tool
async def get_job_insights(
    ctx: RunContext[ResumeCustomizerDeps],
    job_description: str
) -> JobRequirements:
    """Delegate job description analysis to the Researcher agent.
    
    Args:
        ctx: The run context containing dependencies
        job_description: The job description content
        
    Returns:
        JobRequirements: The extracted job requirements
    """
    logger.info("Strategist delegating to Researcher agent for job analysis")
    
    job_requirements = await analyze_job_description(
        job_description=job_description,
        http_client=ctx.deps.http_client,
        model_name=ctx.deps.model_name
    )
    
    logger.info("Received job insights from Researcher agent")
    return job_requirements


@strategist_agent.tool
async def get_resume_insights(
    ctx: RunContext[ResumeCustomizerDeps],
    resume_content: str
) -> ProfessionalProfile:
    """Delegate resume analysis to the Profiler agent.
    
    Args:
        ctx: The run context containing dependencies
        resume_content: The resume content
        
    Returns:
        ProfessionalProfile: The extracted professional profile
    """
    logger.info("Strategist delegating to Profiler agent for resume analysis")
    
    professional_profile = await analyze_resume(
        resume_content=resume_content,
        http_client=ctx.deps.http_client,
        model_name=ctx.deps.model_name
    )
    
    logger.info("Received professional profile from Profiler agent")
    return professional_profile


# Initialize cache provider
cache_provider = get_cache_provider()


@cache_provider.cached(prefix="resume_customization", ttl=settings.CACHE_TTL)
async def customize_resume(
    resume_content: Union[str, bytes, UploadFile, Path],
    job_description: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None,
    file_type: Optional[str] = None
) -> OptimizedResume:
    """Customize a resume for a specific job description.
    
    This function supports various input types for resume_content:
    - str: Raw resume text content or file path
    - bytes: Raw file content (requires file_type)
    - UploadFile: FastAPI uploaded file
    - Path: File path
    
    Args:
        resume_content: The resume content (in one of the supported forms)
        job_description: The job description content
        http_client: The HTTP client for making requests
        model_name: Optional override for the model name
        file_type: MIME type (required if resume_content is bytes)
        
    Returns:
        OptimizedResume: The optimized resume
        
    Raises:
        AgentError: If there's an error in agent execution
    """
    start_time = time.time()
    logger.info(f"Starting resume customization with model: {model_name or settings.DEFAULT_MODEL}")
    
    try:
        # Create dependencies
        deps = ResumeCustomizerDeps(
            http_client=http_client,
            model_name=model_name or settings.DEFAULT_MODEL
        )
        
        # Extract text if resume_content is not a string
        if not isinstance(resume_content, str):
            resume_text = await analyze_resume(
                resume_content=resume_content,
                http_client=http_client,
                model_name=model_name,
                file_type=file_type
            )
            # Use the professional profile from analyze_resume, but we need the raw text
            # For demonstration purposes, we'll use a placeholder approach here
            # In a real implementation, this would need to be handled more carefully
            resume_text_content = str(resume_text)
        else:
            resume_text_content = resume_content
        
        # Prepare the prompt
        prompt = (
            f"Customize the provided resume for the provided job description. "
            f"Use the get_resume_insights and get_job_insights tools to analyze the inputs, "
            f"and then create an optimized resume in Markdown format. "
            f"Ensure the resume is tailored to match the job requirements while "
            f"highlighting the candidate's relevant skills and experiences."
        )
        
        # Run the agent
        result = await strategist_agent.run(
            prompt,
            deps=deps,
            resume_content=resume_text_content,
            job_description=job_description
        )
        
        # Parse the result
        markdown_content = result.output
        
        # Extract key insights from the job description for the summary
        job_insights = await get_job_insights(
            ctx=RunContext(deps=deps),
            job_description=job_description
        )
        
        # Create a more detailed optimization summary based on job insights
        optimization_summary = ResumeOptimizationSummary(
            key_changes=[
                "Restructured resume to highlight relevant skills and experiences",
                "Added keywords from job description for ATS optimization",
                "Quantified achievements to demonstrate impact",
                f"Emphasized alignment with {job_insights.company_profile}"
            ],
            alignment_points=[
                f"Aligned skills section with core requirements: {', '.join(job_insights.core_requirements[:3])}",
                "Emphasized relevant project experience",
                "Highlighted achievements that demonstrate required competencies",
                f"Addressed key expectations: {job_insights.hidden_expectations}"
            ],
            ats_optimization=[
                f"Incorporated key terminology: {', '.join(job_insights.keywords[:5])}",
                "Used standard section headings",
                "Avoided complex formatting that could confuse ATS",
                f"Applied recommended strategy: {job_insights.application_strategy}"
            ]
        )
        
        # Create the optimized resume object
        optimized_resume = OptimizedResume(
            content=markdown_content,
            format=ResumeFormat.MARKDOWN,
            optimization_summary=optimization_summary
        )
        
        # Log the result
        elapsed_time = time.time() - start_time
        logger.info(f"Resume customization completed in {elapsed_time:.2f} seconds")
        
        return optimized_resume
        
    except Exception as e:
        error_msg = f"Resume customization failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="StrategistAgent")
