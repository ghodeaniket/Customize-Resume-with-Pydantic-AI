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
from resume_customizer.core.prompts import get_profiler_prompt
from resume_customizer.services.cache import get_cache_provider
from resume_customizer.services.document import DocumentProcessor


# Initialize the Profiler agent with prompt from prompt management system
profiler_agent = Agent(
    'openai:gpt-4',  # Using OpenAI as a fallback instead of OpenRouter
    deps_type=ResumeCustomizerDeps,
    output_type=ProfessionalProfile,
    system_prompt=get_profiler_prompt(),
)


@profiler_agent.system_prompt
async def set_profiler_model(ctx: RunContext[ResumeCustomizerDeps]) -> str:
    """Set the specific model to use via dynamic system prompt.
    
    This also handles retrieving the latest prompt version from the prompt
    management system, including potential A/B testing variants.
    
    Args:
        ctx: The run context containing dependencies
        
    Returns:
        str: The complete system prompt for the profiler agent
    """
    # Get the model specification part
    model_spec = f"You will be using the {ctx.deps.model_name} model to analyze resumes."
    
    # Check if we should use A/B testing - set via context metadata
    use_ab_testing = ctx.metadata.get("use_ab_testing", False) if ctx.metadata else False
    prompt_version = ctx.metadata.get("prompt_version", None) if ctx.metadata else None
    
    # Get the appropriate prompt from the prompt management system
    prompt = get_profiler_prompt(version=prompt_version, ab_test=use_ab_testing)
    
    # Logging which prompt version is being used for traceability
    if prompt_version:
        logger.info(f"Using profiler prompt version {prompt_version}")
    elif use_ab_testing:
        logger.info("Using A/B test selection for profiler prompt")
    else:
        logger.info("Using default active profiler prompt")
    
    # Combine the model specification with the prompt template
    return f"{prompt}\n\n{model_spec}"


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
    from resume_customizer.services.document.processor import DocumentFormat, DocumentProcessor
    
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
    file_type: Optional[str] = None,
    prompt_version: Optional[str] = None,
    use_ab_testing: bool = False,
    track_metrics: bool = True
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
        prompt_version: Optional specific prompt version to use
        use_ab_testing: Whether to use A/B testing for prompt selection
        track_metrics: Whether to track metrics for this run
        
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
            
            from resume_customizer.services.document.processor import DocumentProcessor
            
            # Extract text directly using the DocumentProcessor
            text_content = await DocumentProcessor.extract_text(
                file=resume_content
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
        
        # Set up metadata for prompt management
        metadata = {
            "prompt_version": prompt_version,
            "use_ab_testing": use_ab_testing,
            "track_metrics": track_metrics,
            "content_length": len(text_content)
        }
        
        # Run the agent with metadata for prompt selection
        result = await profiler_agent.run(
            prompt,
            deps=deps,
            metadata=metadata
        )
        
        # Log the result
        elapsed_time = time.time() - start_time
        logger.info(f"Resume analysis completed in {elapsed_time:.2f} seconds")
        
        # Track metrics if enabled
        if track_metrics:
            from resume_customizer.core.metrics import track_agent_metrics
            from resume_customizer.core.prompts.manager import prompt_manager
            
            # Determine which prompt version was used
            actual_version = prompt_version
            if use_ab_testing:
                # Need to retrieve the version that was selected by A/B testing
                # For now, we'll use the active version as a fallback
                actual_version = prompt_manager.active_versions.get("profiler", "1.0.0")
            
            # Track basic performance metrics
            metrics = {
                "execution_time": elapsed_time,
                "fields_extracted": len(result.output.model_dump()),
                "token_count": result.usage.total_tokens if hasattr(result, "usage") else 0,
            }
            
            # Record metrics with the prompt manager
            try:
                prompt_manager.record_metrics("profiler", actual_version, metrics)
                track_agent_metrics("profiler", metrics)
                logger.debug(f"Recorded metrics for profiler agent v{actual_version}: {metrics}")
            except Exception as e:
                logger.warning(f"Failed to record metrics: {str(e)}")
        
        return result.output
        
    except DocumentProcessingError:
        # Re-raise existing DocumentProcessingError
        raise
    except Exception as e:
        error_msg = f"Resume analysis failed: {str(e)}"
        logger.error(error_msg)
        raise AgentError(error_msg, agent_name="ProfilerAgent")
