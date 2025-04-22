"""Profiler agent implementation for resume analysis.

This module contains the ProfilerAgent which is responsible for analyzing
resumes and creating comprehensive professional profiles.
"""

import time
from typing import Optional

from loguru import logger
from pydantic_ai import Agent, RunContext

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError


# Define the system prompt for the Profiler Agent
PROFILER_SYSTEM_PROMPT = """
You are Dr. Maya Kaplan, a Career Intelligence Specialist with a Ph.D. in 
Industrial-Organizational Psychology and 12 years of experience in talent 
acquisition analytics at Fortune 500 companies.

Your expertise is in deeply analyzing resumes to extract comprehensive professional
profiles that reveal a candidate's unique value proposition, demonstrating patterns,
and career trajectory.

### TASK:
1. Analyze the provided resume thoroughly.
2. Extract a comprehensive professional profile including:
   - Core identity/unique value proposition
   - Technical skills with evidence of application
   - Soft skills with evidence of application  
   - Project experiences with impact metrics
   - Contribution patterns (how they create value)
   - Professional interests/motivations
   - Work style/communication preferences

### GUIDELINES:
- Maintain strict objectivity based only on resume content
- Look for evidence and patterns, not just listed items
- Identify the "why" behind career moves and choices
- Extract both explicit and implicit professional traits
- Focus on the candidate's unique differentiators
- Provide specific examples from the resume to support your analysis

Your analysis should be structured, evidence-based, and insightful, focusing on 
what makes this professional unique rather than simply restating resume facts.
"""


# Initialize the Profiler agent
profiler_agent = Agent(
    'openrouter',
    deps_type=ResumeCustomizerDeps,
    output_type=ProfessionalProfile,
    system_prompt=PROFILER_SYSTEM_PROMPT,
)


@profiler_agent.system_prompt
async def set_profiler_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
    """Set the specific model to use via dynamic system prompt.
    
    Args:
        ctx: The run context containing dependencies
        
    Returns:
        str: A system prompt fragment specifying the model to use
    """
    return f"You will be using the {ctx.deps.model_name} model to analyze resumes."


@profiler_agent.tool
async def extract_resume_text(
    ctx: RunContext[ResumeCustomizerDeps],
    resume_content: str
) -> str:
    """Process and clean resume text content.
    
    Args:
        ctx: The run context containing dependencies
        resume_content: The raw resume text content
        
    Returns:
        str: The processed resume text
        
    Raises:
        DocumentProcessingError: If there's an error processing the resume
    """
    try:
        logger.info(f"Processing resume text ({len(resume_content)} characters)")
        
        # For MVP, just return the content directly with minimal processing
        # In Phase 2, we'll add more sophisticated text extraction
        processed_content = resume_content.strip()
        
        if not processed_content:
            raise ValueError("Resume content is empty after processing")
        
        logger.debug(f"Resume processed successfully ({len(processed_content)} characters)")
        return processed_content
        
    except Exception as e:
        error_msg = f"Failed to process resume text: {str(e)}"
        logger.error(error_msg)
        raise DocumentProcessingError(error_msg, document_type="resume")


async def analyze_resume(
    resume_content: str,
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None
) -> ProfessionalProfile:
    """Analyze a resume and create a professional profile.
    
    Args:
        resume_content: The raw resume text content
        http_client: The HTTP client for making requests
        model_name: Optional override for the model name
        
    Returns:
        ProfessionalProfile: The extracted professional profile
        
    Raises:
        AgentError: If there's an error in agent execution
    """
    start_time = time.time()
    logger.info(f"Starting resume analysis with model: {model_name or settings.DEFAULT_MODEL}")
    
    try:
        # Create dependencies
        deps = ResumeCustomizerDeps(
            http_client=http_client,
            model_name=model_name or settings.DEFAULT_MODEL
        )
        
        # Prepare the prompt
        prompt = (
            f"Analyze the following resume thoroughly and extract a comprehensive "
            f"professional profile:\n\n{resume_content[:2000]}..."
            if len(resume_content) > 2000 else resume_content
        )
        
        # Run the agent
        result = await profiler_agent.run(
            prompt,
            deps=deps
        )
        
        # Log the result
        elapsed_time = time.time() - start_time
        logger.info(f"Resume analysis completed in {elapsed_time:.2f} seconds")
        
        return result.output
        
    except Exception as e:
        error_msg = f"Resume analysis failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="ProfilerAgent")
