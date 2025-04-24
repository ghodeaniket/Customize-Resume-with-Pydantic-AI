"""Resume customization API endpoints.

This module contains the API routes for resume customization.
"""

import time
from pathlib import Path
from typing import List, Optional

import httpx
from fastapi import (
    APIRouter, 
    BackgroundTasks,
    Depends, 
    File, 
    Form, 
    HTTPException, 
    Query,
    UploadFile, 
    status
)
from fastapi.responses import JSONResponse
from loguru import logger

from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.agents.strategist import customize_resume
from resume_customizer.api.dependencies import get_http_client, verify_api_key
from resume_customizer.api.responses import (
    JobRequirementsResponse,
    PerformanceResponse,
    ProfileResponse,
    ResumeCustomizationResponse,
    UploadResponse
)
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import (
    AgentError,
    DocumentProcessingError,
    ResumeCustomizerException,
    ValidationError
)
from resume_customizer.core.logging import app_logger as logger
from resume_customizer.services.document import DocumentProcessor


# Create router
router = APIRouter(prefix="/resumes", tags=["Resumes"])


# Utility function to measure performance
async def measure_performance(operation: str, func, *args, **kwargs):
    """Measure performance of a function.
    
    Args:
        operation: The name of the operation
        func: The function to measure
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        tuple: The function result and performance metrics
    """
    start_time = time.time()
    cache_hit = False
    
    # Check if we have a "_cache_hit" key in kwargs
    if "_cache_hit" in kwargs:
        cache_hit = kwargs.pop("_cache_hit")
    
    # Execute the function
    result = await func(*args, **kwargs)
    
    # Calculate metrics
    elapsed_time = time.time() - start_time
    performance = PerformanceResponse(
        elapsed_time=elapsed_time,
        timestamp=start_time,
        operation=operation,
        cache_hit=cache_hit
    )
    
    if settings.ENABLE_PERFORMANCE_LOGGING:
        logger.info(
            f"Performance: {operation} completed in {elapsed_time:.2f}s "
            f"(cache_hit={cache_hit})"
        )
    
    return result, performance


# File upload endpoint
@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a resume file",
    description="Upload a resume file (PDF, DOCX, or TXT) for processing."
)
async def upload_resume(
    file: UploadFile = File(..., description="The resume file to upload"),
    extract_text: bool = Form(False, description="Whether to extract text from the file"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Upload a resume file for processing.
    
    Args:
        file: The resume file to upload
        extract_text: Whether to extract text from the file
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        UploadResponse: Information about the uploaded file
    """
    try:
        logger.info(f"Received file upload: {file.filename} ({file.content_type})")
        
        # Validate file
        if not await DocumentProcessor.is_valid_file(file):
            raise ValidationError(
                f"Invalid file: {file.filename}. Must be PDF, DOCX, or TXT under "
                f"{settings.MAX_UPLOAD_SIZE/1024/1024:.1f}MB"
            )
        
        # Save the file
        file_path = await DocumentProcessor.save_file(file)
        
        # Create response
        response = UploadResponse(
            filename=file.filename,
            file_id=file_path.name,
            file_type=file.content_type,
            file_size=file.file.tell()
        )
        
        # Extract text if requested
        if extract_text:
            text = await DocumentProcessor.extract_text(file)
            response.extract_count = len(text)
        
        return response
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DocumentProcessingError as e:
        error_msg = f"Document processing error: {str(e)}"
        logger.error(error_msg)
        
        # Provide more specific error messages based on the exception
        if "Could not decode" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File format error: The file could not be processed. Please check that it's a valid {e.document_type} file."
            )
        elif "empty" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Empty content: The file appears to be empty or contains no extractable text."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to process file: {str(e)}"
            )
        
    except ResumeCustomizerException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application error: {str(e)}"
        )
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/analyze", 
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a resume and create a professional profile",
    description="Analyze a resume and extract a comprehensive professional profile."
)
async def analyze_resume_endpoint(
    resume_content: str = Form(..., description="The resume content"),
    model_name: Optional[str] = Form(None, description="The model to use for analysis"),
    include_performance: bool = Form(False, description="Whether to include performance metrics"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Analyze a resume and create a professional profile.
    
    Args:
        resume_content: The resume content
        model_name: Optional override for the model name
        include_performance: Whether to include performance metrics
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        ProfileResponse: The extracted professional profile
    """
    try:
        logger.info("Received request to analyze resume")
        
        # Analyze the resume with performance measurement
        if include_performance:
            profile, performance = await measure_performance(
                "analyze_resume",
                analyze_resume,
                resume_content=resume_content,
                http_client=http_client,
                model_name=model_name
            )
            
            # Return the profile with performance metrics
            return ProfileResponse(profile=profile, performance=performance)
        else:
            # Analyze without performance metrics
            profile = await analyze_resume(
                resume_content=resume_content,
                http_client=http_client,
                model_name=model_name
            )
            
            # Return the profile
            return ProfileResponse(profile=profile)
    
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process resume: {str(e)}"
        )
    
    except AgentError as e:
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}"
        )
    
    except ResumeCustomizerException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application error: {str(e)}"
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/analyze-file", 
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a resume file and create a professional profile",
    description="Upload and analyze a resume file (PDF, DOCX, or TXT) to extract a comprehensive professional profile."
)
async def analyze_resume_file_endpoint(
    file: UploadFile = File(..., description="The resume file to analyze"),
    model_name: Optional[str] = Form(None, description="The model to use for analysis"),
    include_performance: bool = Form(False, description="Whether to include performance metrics"),
    save_file: bool = Form(True, description="Whether to save the file after processing"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Upload and analyze a resume file.
    
    Args:
        file: The resume file to analyze
        model_name: Optional override for the model name
        include_performance: Whether to include performance metrics
        save_file: Whether to save the file after processing
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        ProfileResponse: The extracted professional profile
    """
    try:
        logger.info(f"Received request to analyze resume file: {file.filename}")
        
        # Validate file
        if not await DocumentProcessor.is_valid_file(file):
            raise ValidationError(
                f"Invalid file: {file.filename}. Must be PDF, DOCX, or TXT under "
                f"{settings.MAX_UPLOAD_SIZE/1024/1024:.1f}MB"
            )
        
        # Save the file if requested
        if save_file:
            await DocumentProcessor.save_file(file)
        
        # Analyze the resume with performance measurement
        if include_performance:
            profile, performance = await measure_performance(
                "analyze_resume_file",
                analyze_resume,
                resume_content=file,
                http_client=http_client,
                model_name=model_name
            )
            
            # Return the profile with performance metrics
            return ProfileResponse(profile=profile, performance=performance)
        else:
            # Analyze without performance metrics
            profile = await analyze_resume(
                resume_content=file,
                http_client=http_client,
                model_name=model_name
            )
            
            # Return the profile
            return ProfileResponse(profile=profile)
    
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process resume: {str(e)}"
        )
    
    except AgentError as e:
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resume: {str(e)}"
        )
    
    except ResumeCustomizerException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application error: {str(e)}"
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/analyze-job", 
    response_model=JobRequirementsResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a job description and extract requirements",
    description="Analyze a job description and extract key requirements and insights."
)
async def analyze_job_endpoint(
    job_description: str = Form(..., description="The job description content"),
    model_name: Optional[str] = Form(None, description="The model to use for analysis"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Analyze a job description and extract requirements.
    
    Args:
        job_description: The job description content
        model_name: Optional override for the model name
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        JobRequirementsResponse: The extracted job requirements
    """
    try:
        logger.info("Received request to analyze job description")
        
        # Analyze the job description
        requirements = await analyze_job_description(
            job_description=job_description,
            http_client=http_client,
            model_name=model_name
        )
        
        # Return the requirements
        return JobRequirementsResponse(requirements=requirements)
    
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process job description: {str(e)}"
        )
    
    except AgentError as e:
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze job description: {str(e)}"
        )
    
    except ResumeCustomizerException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application error: {str(e)}"
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/customize", 
    response_model=ResumeCustomizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Customize a resume for a specific job",
    description="Customize a resume based on job requirements to maximize alignment and ATS compatibility."
)
async def customize_resume_endpoint(
    resume_content: str = Form(..., description="The resume content"),
    job_description: str = Form(..., description="The job description content"),
    model_name: Optional[str] = Form(None, description="The model to use for customization"),
    include_analysis: bool = Form(False, description="Whether to include full analysis in the response"),
    include_performance: bool = Form(False, description="Whether to include performance metrics"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Customize a resume for a specific job.
    
    Args:
        resume_content: The resume content
        job_description: The job description content
        model_name: Optional override for the model name
        include_analysis: Whether to include full analysis in the response
        include_performance: Whether to include performance metrics
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        ResumeCustomizationResponse: The customized resume
    """
    try:
        logger.info("Received request to customize resume")
        
        # Measure customization performance
        if include_performance:
            optimized_resume, performance = await measure_performance(
                "customize_resume",
                customize_resume,
                resume_content=resume_content,
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            # Create the response
            response = ResumeCustomizationResponse(
                optimized_resume=optimized_resume,
                performance=performance
            )
        else:
            # Customize without performance metrics
            optimized_resume = await customize_resume(
                resume_content=resume_content,
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            # Create the response
            response = ResumeCustomizationResponse(
                optimized_resume=optimized_resume
            )
        
        # Add analysis if requested
        if include_analysis:
            # Analyze the resume
            profile = await analyze_resume(
                resume_content=resume_content,
                http_client=http_client,
                model_name=model_name
            )
            
            # Analyze the job description
            requirements = await analyze_job_description(
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            # Add to response
            response.profile = profile
            response.requirements = requirements
        
        # Return the response
        return response
    
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process document: {str(e)}"
        )
    
    except AgentError as e:
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to customize resume: {str(e)}"
        )
    
    except ResumeCustomizerException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application error: {str(e)}"
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post(
    "/customize-file", 
    response_model=ResumeCustomizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Customize a resume file for a specific job",
    description="Upload and customize a resume file (PDF, DOCX, or TXT) based on job requirements."
)
async def customize_resume_file_endpoint(
    resume_file: UploadFile = File(..., description="The resume file to customize"),
    job_description: str = Form(..., description="The job description content"),
    model_name: Optional[str] = Form(None, description="The model to use for customization"),
    include_analysis: bool = Form(False, description="Whether to include full analysis in the response"),
    include_performance: bool = Form(False, description="Whether to include performance metrics"),
    save_file: bool = Form(True, description="Whether to save the file after processing"),
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Upload and customize a resume file for a specific job.
    
    Args:
        resume_file: The resume file to customize
        job_description: The job description content
        model_name: Optional override for the model name
        include_analysis: Whether to include full analysis in the response
        include_performance: Whether to include performance metrics
        save_file: Whether to save the file after processing
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        ResumeCustomizationResponse: The customized resume
    """
    try:
        logger.info(f"Received request to customize resume file: {resume_file.filename}")
        
        # Validate file
        if not await DocumentProcessor.is_valid_file(resume_file):
            raise ValidationError(
                f"Invalid file: {resume_file.filename}. Must be PDF, DOCX, or TXT under "
                f"{settings.MAX_UPLOAD_SIZE/1024/1024:.1f}MB"
            )
        
        # Save the file if requested
        if save_file:
            await DocumentProcessor.save_file(resume_file)
        
        # Measure customization performance
        if include_performance:
            optimized_resume, performance = await measure_performance(
                "customize_resume_file",
                customize_resume,
                resume_content=resume_file,
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            # Create the response
            response = ResumeCustomizationResponse(
                optimized_resume=optimized_resume,
                performance=performance
            )
        else:
            # Customize without performance metrics
            optimized_resume = await customize_resume(
                resume_content=resume_file,
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            # Create the response
            response = ResumeCustomizationResponse(
                optimized_resume=optimized_resume
            )
        
        # Add analysis if requested
        if include_analysis:
            # Extract text from file
            file_content = await resume_file.read()
            await resume_file.seek(0)  # Reset file position
            
            # Analyze the resume
            profile = await analyze_resume(
                resume_content=resume_file,
                http_client=http_client,
                model_name=model_name
            )
            
            # Analyze the job description
            requirements = await analyze_job_description(
                job_description=job_description,
                http_client=http_client,
                model_name=model_name
            )
            
            # Add to response
            response.profile = profile
            response.requirements = requirements
        
        # Return the response
        return response
    
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except DocumentProcessingError as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process document: {str(e)}"
        )
    
    except AgentError as e:
        logger.error(f"Agent error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to customize resume: {str(e)}"
        )
    
    except ResumeCustomizerException as e:
        logger.error(f"Application error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application error: {str(e)}"
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
