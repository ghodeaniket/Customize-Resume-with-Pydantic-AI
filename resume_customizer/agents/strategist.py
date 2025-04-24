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
from resume_customizer.core.prompts import get_strategist_prompt
from resume_customizer.services.cache import get_cache_provider
from resume_customizer.services.document import DocumentProcessor


# Initialize the Strategist agent with prompt from prompt management system
strategist_agent = Agent(
    'openai:gpt-4',  # Using OpenAI as a fallback instead of OpenRouter
    deps_type=ResumeCustomizerDeps,
    output_type=str,  # Markdown formatted resume
    system_prompt=get_strategist_prompt(), 
)


@strategist_agent.system_prompt
async def set_strategist_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
    """Set the specific model to use via dynamic system prompt.
    
    This also handles retrieving the latest prompt version from the prompt
    management system, including potential A/B testing variants.
    
    Args:
        ctx: The run context containing dependencies
        
    Returns:
        str: The complete system prompt for the strategist agent
    """
    # Get the model specification part
    model_spec = f"You will be using the {ctx.deps.model_name} model to optimize resumes."
    
    # Check if we should use A/B testing - set via context metadata
    use_ab_testing = ctx.metadata.get("use_ab_testing", False) if ctx.metadata else False
    prompt_version = ctx.metadata.get("prompt_version", None) if ctx.metadata else None
    
    # Get the appropriate prompt from the prompt management system
    prompt = get_strategist_prompt(version=prompt_version, ab_test=use_ab_testing)
    
    # Logging which prompt version is being used for traceability
    if prompt_version:
        logger.info(f"Using strategist prompt version {prompt_version}")
    elif use_ab_testing:
        logger.info("Using A/B test selection for strategist prompt")
    else:
        logger.info("Using default active strategist prompt")
    
    # Combine the model specification with the prompt template
    return f"{prompt}\n\n{model_spec}"


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


from resume_customizer.core.error_handling import with_retry, with_fallback
from resume_customizer.core.evaluation import evaluate_agent_output


@cache_provider.cached(prefix="resume_customization", ttl=settings.CACHE_TTL)
@with_fallback(agent_name="strategist")
@with_retry(max_retries=settings.MAX_RETRY_ATTEMPTS)
async def customize_resume(
    resume_content: Union[str, bytes, UploadFile, Path],
    job_description: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None,
    file_type: Optional[str] = None,
    prompt_version: Optional[str] = None,
    use_ab_testing: bool = False,
    track_metrics: bool = True,
    evaluate_output: bool = True
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
        prompt_version: Optional specific prompt version to use
        use_ab_testing: Whether to use A/B testing for prompt selection
        track_metrics: Whether to track metrics for this run
        evaluate_output: Whether to evaluate the quality of the output
        
    Returns:
        OptimizedResume: The optimized resume
        
    Raises:
        AgentError: If there's an error in agent execution and recovery fails
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
            # If it's an UploadFile, extract the text directly
            if isinstance(resume_content, UploadFile):
                from resume_customizer.services.document.processor import DocumentProcessor
                resume_text_content = await DocumentProcessor.extract_text(resume_content)
            else:
                # For other types (bytes, Path), use analyze_resume
                resume_profile = await analyze_resume(
                    resume_content=resume_content,
                    http_client=http_client,
                    model_name=model_name,
                    file_type=file_type
                )
                
                # Get the original text through a secondary extraction
                if isinstance(resume_content, bytes):
                    from resume_customizer.services.document.processor import DocumentProcessor, DocumentFormat
                    format_type = None
                    if file_type == "application/pdf":
                        format_type = DocumentFormat.PDF
                    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        format_type = DocumentFormat.DOCX
                    elif file_type == "text/plain":
                        format_type = DocumentFormat.TXT
                    else:
                        format_type = DocumentFormat.TXT
                    
                    resume_text_content = await DocumentProcessor.extract_text(resume_content, format_type)
                elif isinstance(resume_content, Path):
                    with open(resume_content, 'r', encoding='utf-8') as f:
                        resume_text_content = f.read()
                else:
                    # Fallback if we can't get original text
                    resume_text_content = str(resume_profile)
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
        
        # Set up metadata for prompt management
        metadata = {
            "prompt_version": prompt_version,
            "use_ab_testing": use_ab_testing,
            "track_metrics": track_metrics,
            "job_description_length": len(job_description),
            "resume_content_length": len(resume_text_content)
        }
        
        # Run the agent with metadata for prompt selection
        result = await strategist_agent.run(
            prompt,
            deps=deps,
            metadata=metadata,
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
        
        # Track metrics if enabled
        if track_metrics:
            from resume_customizer.core.metrics import track_agent_metrics
            from resume_customizer.core.prompts.manager import prompt_manager
            
            # Determine which prompt version was used
            actual_version = prompt_version
            if use_ab_testing:
                # Need to retrieve the version that was selected by A/B testing
                # This would normally be tracked in the result metadata
                # For now, we'll use the active version as a fallback
                actual_version = prompt_manager.active_versions.get("strategist", "1.0.0")
            
            # Track basic performance metrics
            metrics = {
                "execution_time": elapsed_time,
                "output_length": len(markdown_content),
                "token_count": result.usage.total_tokens if hasattr(result, "usage") else 0,
            }
            
            # Record metrics with the prompt manager
            try:
                prompt_manager.record_metrics("strategist", actual_version, metrics)
                track_agent_metrics("strategist", metrics)
                logger.debug(f"Recorded metrics for strategist agent v{actual_version}: {metrics}")
            except Exception as e:
                logger.warning(f"Failed to record metrics: {str(e)}")
        
        # Evaluate output quality if enabled
        if evaluate_output:
            try:
                # Prepare evaluation metadata
                eval_metadata = {
                    "agent": "strategist",
                    "prompt_version": actual_version if track_metrics else prompt_version,
                    "model_name": model_name or settings.DEFAULT_MODEL,
                    "execution_time": elapsed_time,
                    "token_count": result.usage.total_tokens if hasattr(result, "usage") else 0,
                    "resume_length": len(resume_text_content),
                    "job_description_length": len(job_description),
                    "output_length": len(markdown_content),
                }
                
                # Evaluate the output
                evaluation_result = await evaluate_agent_output(
                    agent_name="strategist",
                    output=markdown_content,
                    prompt_version=actual_version if track_metrics else prompt_version or "unknown",
                    metadata=eval_metadata
                )
                
                # Log the evaluation result
                logger.info(f"Strategist output evaluation: score={evaluation_result.overall_score:.2f}")
                
                # If quality is below threshold, log a warning
                threshold = settings.EVALUATION_SCORE_THRESHOLD
                if evaluation_result.overall_score < threshold:
                    logger.warning(
                        f"Strategist output quality below threshold: {evaluation_result.overall_score:.2f} < {threshold}"
                    )
                    
                    # Add evaluation result to the output metadata for the client
                    optimized_resume.metadata["quality_score"] = evaluation_result.overall_score
                    optimized_resume.metadata["quality_threshold"] = threshold
                    optimized_resume.metadata["quality_passed"] = False
                else:
                    # Add positive evaluation result
                    optimized_resume.metadata["quality_score"] = evaluation_result.overall_score
                    optimized_resume.metadata["quality_threshold"] = threshold
                    optimized_resume.metadata["quality_passed"] = True
                
            except Exception as e:
                logger.warning(f"Failed to evaluate strategist output: {str(e)}")
        
        return optimized_resume
        
    except Exception as e:
        error_msg = f"Resume customization failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="StrategistAgent")
