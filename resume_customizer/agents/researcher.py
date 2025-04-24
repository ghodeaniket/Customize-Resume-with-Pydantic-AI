"""Researcher agent implementation for job description analysis.

This module contains the ResearcherAgent which is responsible for analyzing
job descriptions to extract key requirements.
"""

import time
from typing import Optional
import urllib.parse

from loguru import logger
import httpx
from pydantic_ai import Agent, RunContext

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError
from resume_customizer.core.prompts import get_researcher_prompt


# Initialize the Researcher agent with prompt from prompt management system
researcher_agent = Agent(
    'openai:gpt-4',  # Using OpenAI as a fallback instead of OpenRouter
    deps_type=ResumeCustomizerDeps,
    output_type=JobRequirements,
    system_prompt=get_researcher_prompt(),
)


@researcher_agent.system_prompt
async def set_researcher_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
    """Set the specific model to use via dynamic system prompt.
    
    This also handles retrieving the latest prompt version from the prompt
    management system, including potential A/B testing variants.
    
    Args:
        ctx: The run context containing dependencies
        
    Returns:
        str: The complete system prompt for the researcher agent
    """
    # Get the model specification part
    model_spec = f"You will be using the {ctx.deps.model_name} model to analyze job descriptions."
    
    # Check if we should use A/B testing - set via context metadata
    use_ab_testing = ctx.metadata.get("use_ab_testing", False) if ctx.metadata else False
    prompt_version = ctx.metadata.get("prompt_version", None) if ctx.metadata else None
    
    # Get the appropriate prompt from the prompt management system
    prompt = get_researcher_prompt(version=prompt_version, ab_test=use_ab_testing)
    
    # Logging which prompt version is being used for traceability
    if prompt_version:
        logger.info(f"Using researcher prompt version {prompt_version}")
    elif use_ab_testing:
        logger.info("Using A/B test selection for researcher prompt")
    else:
        logger.info("Using default active researcher prompt")
    
    # Combine the model specification with the prompt template
    return f"{prompt}\n\n{model_spec}"


@researcher_agent.tool
async def fetch_job_description(
    ctx: RunContext[ResumeCustomizerDeps],
    url: str
) -> str:
    """Fetch job description content from a URL.
    
    Args:
        ctx: The run context containing dependencies
        url: The URL of the job description
        
    Returns:
        str: The job description content
        
    Raises:
        DocumentProcessingError: If there's an error fetching the job description
    """
    try:
        logger.info(f"Fetching job description from URL: {url}")
        
        # Validate the URL
        parsed_url = urllib.parse.urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError(f"Invalid URL: {url}")
        
        # Fetch the content
        response = await ctx.deps.http_client.get(
            url,
            follow_redirects=True,
            timeout=30.0
        )
        response.raise_for_status()
        content = response.text
        
        if not content:
            raise ValueError("Job description content is empty")
        
        logger.debug(f"Job description fetched successfully ({len(content)} characters)")
        return content
        
    except httpx.HTTPError as e:
        error_msg = f"HTTP error fetching job description: {str(e)}"
        logger.error(error_msg)
        raise DocumentProcessingError(error_msg, document_type="job_description")
    except Exception as e:
        error_msg = f"Failed to fetch job description: {str(e)}"
        logger.error(error_msg)
        raise DocumentProcessingError(error_msg, document_type="job_description")


async def analyze_job_description(
    job_description: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None,
    prompt_version: Optional[str] = None,
    use_ab_testing: bool = False,
    track_metrics: bool = True
) -> JobRequirements:
    """Analyze a job description and extract key requirements.
    
    Args:
        job_description: The job description content or URL
        http_client: The HTTP client for making requests
        model_name: Optional override for the model name
        prompt_version: Optional specific prompt version to use
        use_ab_testing: Whether to use A/B testing for prompt selection
        track_metrics: Whether to track metrics for this run
        
    Returns:
        JobRequirements: The extracted job requirements
        
    Raises:
        AgentError: If there's an error in agent execution
    """
    start_time = time.time()
    logger.info(f"Starting job description analysis with model: {model_name or settings.DEFAULT_MODEL}")
    
    try:
        # Create dependencies
        deps = ResumeCustomizerDeps(
            http_client=http_client,
            model_name=model_name or settings.DEFAULT_MODEL
        )
        
        # Check if job_description is a URL
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        job_description_text = job_description
        if url_pattern.match(job_description):
            # It's a URL, fetch the content
            logger.info(f"Job description appears to be a URL, fetching content: {job_description}")
            try:
                job_description_text = await fetch_job_description(
                    ctx=RunContext(deps=deps),
                    url=job_description
                )
            except Exception as e:
                logger.warning(f"Failed to fetch job description from URL: {str(e)}")
                # Continue with the original text, assuming it's not actually a URL
                job_description_text = job_description
        
        # Prepare the prompt
        prompt = (
            f"Analyze the following job description thoroughly and extract key requirements "
            f"and insights:\n\n{job_description_text[:2000]}..."
            if len(job_description_text) > 2000 else job_description_text
        )
        
        # Set up metadata for prompt management
        metadata = {
            "prompt_version": prompt_version,
            "use_ab_testing": use_ab_testing,
            "track_metrics": track_metrics,
            "content_length": len(job_description_text)
        }
        
        # Run the agent with metadata for prompt selection
        result = await researcher_agent.run(
            prompt,
            deps=deps,
            metadata=metadata
        )
        
        # Log the result
        elapsed_time = time.time() - start_time
        logger.info(f"Job description analysis completed in {elapsed_time:.2f} seconds")
        
        # Track metrics if enabled
        if track_metrics:
            from resume_customizer.core.metrics import track_agent_metrics
            from resume_customizer.core.prompts.manager import prompt_manager
            
            # Determine which prompt version was used
            actual_version = prompt_version
            if use_ab_testing:
                # Need to retrieve the version that was selected by A/B testing
                # For now, we'll use the active version as a fallback
                actual_version = prompt_manager.active_versions.get("researcher", "1.0.0")
            
            # Track basic performance metrics
            metrics = {
                "execution_time": elapsed_time,
                "keywords_extracted": len(result.output.keywords),
                "core_requirements_extracted": len(result.output.core_requirements),
                "token_count": result.usage.total_tokens if hasattr(result, "usage") else 0,
            }
            
            # Record metrics with the prompt manager
            try:
                prompt_manager.record_metrics("researcher", actual_version, metrics)
                track_agent_metrics("researcher", metrics)
                logger.debug(f"Recorded metrics for researcher agent v{actual_version}: {metrics}")
            except Exception as e:
                logger.warning(f"Failed to record metrics: {str(e)}")
        
        return result.output
        
    except Exception as e:
        error_msg = f"Job description analysis failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="ResearcherAgent")
