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


# Define the system prompt for the Researcher Agent
RESEARCHER_SYSTEM_PROMPT = """
You are Eliza Chen, a Tech Job Description Strategist with 13+ years of experience 
in technical recruitment and talent acquisition at FAANG companies.

Your expertise is in deeply analyzing job descriptions to extract the real requirements, 
hidden expectations, and strategic insights that help candidates optimize their 
applications for specific roles.

### TASK:
1. Analyze the provided job description thoroughly.
2. Extract key requirements and insights including:
   - Company context and position details
   - Core requirements (must-have skills and qualifications)
   - Supplementary attributes (nice-to-have skills and qualities)
   - Hidden expectations (reading between the lines)
   - Application strategy (areas to emphasize and address)
   - Keywords for ATS optimization

### GUIDELINES:
- Distinguish between essential requirements and nice-to-haves
- Look beyond explicit statements to identify implicit expectations
- Identify technical skills, soft skills, and experience levels required
- Note company culture indicators and how they affect requirements
- Extract specific terminology that would help with ATS optimization
- Provide strategic advice on how to position oneself for this role

Your analysis should be structured, insightful, and actionable, giving candidates 
clear direction on how to tailor their application for maximum impact.
"""


# Initialize the Researcher agent
researcher_agent = Agent(
    'openai:gpt-4',  # Using OpenAI as a fallback instead of OpenRouter
    deps_type=ResumeCustomizerDeps,
    output_type=JobRequirements,
    system_prompt=RESEARCHER_SYSTEM_PROMPT,
)


@researcher_agent.system_prompt
async def set_researcher_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
    """Set the specific model to use via dynamic system prompt.
    
    Args:
        ctx: The run context containing dependencies
        
    Returns:
        str: A system prompt fragment specifying the model to use
    """
    return f"You will be using the {ctx.deps.model_name} model to analyze job descriptions."


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
    model_name: Optional[str] = None
) -> JobRequirements:
    """Analyze a job description and extract key requirements.
    
    Args:
        job_description: The job description content
        http_client: The HTTP client for making requests
        model_name: Optional override for the model name
        
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
        
        # Prepare the prompt
        prompt = (
            f"Analyze the following job description thoroughly and extract key requirements "
            f"and insights:\n\n{job_description[:2000]}..."
            if len(job_description) > 2000 else job_description
        )
        
        # Run the agent
        result = await researcher_agent.run(
            prompt,
            deps=deps
        )
        
        # Log the result
        elapsed_time = time.time() - start_time
        logger.info(f"Job description analysis completed in {elapsed_time:.2f} seconds")
        
        return result.output
        
    except Exception as e:
        error_msg = f"Job description analysis failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="ResearcherAgent")
