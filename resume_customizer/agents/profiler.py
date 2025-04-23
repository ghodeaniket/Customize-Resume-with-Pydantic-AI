"""Profiler agent implementation for resume analysis.

This module contains the ProfilerAgent which is responsible for analyzing
resumes and creating comprehensive professional profiles.
"""

import io
import os
import time
from pathlib import Path
from typing import Optional, Union

import httpx
from fastapi import UploadFile
from loguru import logger
from pydantic_ai import Agent, RunContext

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError
from resume_customizer.services.cache import get_cache_provider
from resume_customizer.services.document import DocumentProcessor


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


# Initialize cache provider
cache_provider = get_cache_provider()


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
        
        # Apply basic text cleaning
        processed_content = resume_content.strip()
        
        if not processed_content:
            raise ValueError("Resume content is empty after processing")
        
        logger.debug(f"Resume processed successfully ({len(processed_content)} characters)")
        return processed_content
        
    except Exception as e:
        error_msg = f"Failed to process resume text: {str(e)}"
        logger.error(error_msg)
        raise DocumentProcessingError(error_msg, document_type="resume")


@profiler_agent.tool
@cache_provider.cached(prefix="resume_extraction", ttl=settings.CACHE_TTL)
async def extract_resume_from_file(
    ctx: RunContext[ResumeCustomizerDeps],
    file_content: bytes,
    file_type: str,
    filename: Optional[str] = None
) -> str:
    """Extract text from a resume file.
    
    Args:
        ctx: The run context containing dependencies
        file_content: The raw file content
        file_type: The MIME type of the file
        filename: Optional filename (for extension-based format detection)
        
    Returns:
        str: The extracted text
        
    Raises:
        DocumentProcessingError: If there's an error extracting text
    """
    from resume_customizer.services.document.processor import DocumentFormat
    
    start_time = time.time()
    logger.info(f"Extracting text from resume file ({len(file_content)} bytes, type: {file_type})")
    
    try:
        # Create a virtual UploadFile for format detection if filename is provided
        format_type = None
        if filename:
            mock_file = UploadFile(
                filename=filename,
                content_type=file_type,
                file=io.BytesIO(file_content)
            )
            format_type = DocumentProcessor.get_format(mock_file)
        
        # Map MIME type to DocumentFormat
        if format_type is None:
            if file_type == "application/pdf":
                format_type = DocumentFormat.PDF
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                format_type = DocumentFormat.DOCX
            elif file_type == "text/plain":
                format_type = DocumentFormat.TXT
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        
        # Extract text
        text = await DocumentProcessor.extract_text(file_content, format_type)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Resume extraction completed in {elapsed_time:.2f} seconds")
        
        return text
        
    except Exception as e:
        error_msg = f"Failed to extract text from resume file: {str(e)}"
        logger.error(error_msg)
        raise DocumentProcessingError(error_msg, document_type="resume")


@cache_provider.cached(prefix="resume_analysis", ttl=settings.CACHE_TTL)
async def analyze_resume(
    resume_content: Union[str, bytes, UploadFile, Path],
    http_client: httpx.AsyncClient,
    model_name: Optional[str] = None,
    file_type: Optional[str] = None
) -> ProfessionalProfile:
    """Analyze a resume and create a professional profile.
    
    This function supports various input types:
    - str: Raw resume text content or file path
    - bytes: Raw file content (requires file_type)
    - UploadFile: FastAPI uploaded file
    - Path: File path
    
    Args:
        resume_content: The resume content (in one of the supported forms)
        http_client: The HTTP client for making requests
        model_name: Optional override for the model name
        file_type: MIME type (required if resume_content is bytes)
        
    Returns:
        ProfessionalProfile: The extracted professional profile
        
    Raises:
        AgentError: If there's an error in agent execution
        DocumentProcessingError: If there's an error processing the document
    """
    start_time = time.time()
    logger.info(f"Starting resume analysis with model: {model_name or settings.DEFAULT_MODEL}")
    
    try:
        # Create dependencies
        deps = ResumeCustomizerDeps(
            http_client=http_client,
            model_name=model_name or settings.DEFAULT_MODEL
        )
        
        # Extract text based on input type
        text_content = ""
        
        if isinstance(resume_content, str):
            if os.path.exists(resume_content):
                # It's a file path
                text_content = await DocumentProcessor.extract_text(Path(resume_content))
            else:
                # It's already text
                text_content = resume_content
        
        elif isinstance(resume_content, bytes):
            # It's raw file content
            if not file_type:
                raise ValueError("file_type is required when resume_content is bytes")
            
            text_content = await extract_resume_from_file(
                ctx=RunContext(deps=deps),
                file_content=resume_content,
                file_type=file_type
            )
        
        elif isinstance(resume_content, UploadFile):
            # It's an uploaded file
            file_content = await resume_content.read()
            await resume_content.seek(0)  # Reset file position
            
            text_content = await extract_resume_from_file(
                ctx=RunContext(deps=deps),
                file_content=file_content,
                file_type=resume_content.content_type or "application/octet-stream",
                filename=resume_content.filename
            )
        
        elif isinstance(resume_content, Path):
            # It's a file path
            text_content = await DocumentProcessor.extract_text(resume_content)
        
        else:
            raise TypeError(f"Unsupported resume_content type: {type(resume_content)}")
        
        if not text_content:
            raise ValueError("Failed to extract text content from resume")
        
        # Prepare the prompt
        prompt = (
            f"Analyze the following resume thoroughly and extract a comprehensive "
            f"professional profile:\n\n{text_content[:5000]}..."
            if len(text_content) > 5000 else text_content
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
        
    except DocumentProcessingError:
        # Re-raise existing DocumentProcessingError
        raise
    except Exception as e:
        error_msg = f"Resume analysis failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="ProfilerAgent")
