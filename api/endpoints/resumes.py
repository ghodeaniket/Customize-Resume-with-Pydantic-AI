"""Resume customization endpoints."""
import logging
import time
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from agents.models.resume import CustomizationRequest, CustomizationResponse, ResumeFormat
from api.decorators import handle_api_errors, add_request_metrics
from api.dependencies import get_resume_customizer_service, get_settings
from api.utils import APIUtils, structure_response
from core.cache import cache_response
from core.config import Settings
from core.utils.file_detection import TEXT_MIME_TYPE
from services.customizer import ResumeCustomizerService


router = APIRouter(prefix="/resumes", tags=["resumes"])
logger = logging.getLogger(__name__)


@router.post(
    "/customize", 
    response_model=CustomizationResponse,
    summary="Customize a resume for a job description",
    description="Customize a resume based on a specific job description"
)
@handle_api_errors
@add_request_metrics
@cache_response("customize_resume", ttl_seconds=3600)  # Cache for 1 hour
async def customize_resume(
    request: CustomizationRequest,
    service: ResumeCustomizerService = Depends(get_resume_customizer_service),
    settings: Settings = Depends(get_settings)
) -> Dict:
    """Customize a resume for a specific job description.
    
    Args:
        request: Customization request
        service: Resume customizer service
        settings: Application settings
        
    Returns:
        Dict: Structured response with customization data and metadata
    """
    # Apply default token limit if not specified
    if request.max_tokens is None:
        request.max_tokens = settings.default_token_limit
    
    # Process request
    start_time = time.time()
    response = await service.customize_resume(request)
    processing_time_ms = round((time.time() - start_time) * 1000, 2)
    
    # Structure response with metadata
    return structure_response(
        data=response,
        extra_metadata={
            "processing_time_ms": processing_time_ms,
            "model_used": request.model_name,
            "output_format": request.output_format.value
        }
    )


@router.post(
    "/customize-upload", 
    response_model=CustomizationResponse,
    summary="Customize a resume from file upload",
    description="Customize a resume from file upload based on a specific job description"
)
@handle_api_errors
@add_request_metrics
async def customize_resume_upload(
    job_description: str = Form(...),
    resume_file: UploadFile = File(...),
    model_name: str = Form("deepseek/deepseek-r1-distill-llama-70b"),
    output_format: ResumeFormat = Form(ResumeFormat.MARKDOWN),
    max_tokens: Optional[int] = Form(None),
    service: ResumeCustomizerService = Depends(get_resume_customizer_service),
    settings: Settings = Depends(get_settings)
) -> Dict:
    """Customize a resume from file upload for a specific job description.
    
    Args:
        job_description: Job description text
        resume_file: Resume file
        model_name: AI model name
        output_format: Output format
        max_tokens: Maximum tokens
        service: Resume customizer service
        settings: Application settings
        
    Returns:
        Dict: Structured response with customization data and metadata
    """
    # Process uploaded file
    file_content, file_type = await APIUtils.process_uploaded_file(resume_file)
    
    # Apply default token limit if not specified
    if max_tokens is None:
        max_tokens = settings.default_token_limit
    
    start_time = time.time()
    
    # For plain text files, extract content directly
    if file_type == TEXT_MIME_TYPE:
        try:
            resume_content = file_content.decode('utf-8').strip()
            logger.info(f"Extracted text content (first 100 chars): {resume_content[:100]}")
            
            # Create a customization request
            request = CustomizationRequest(
                resume_content=resume_content,
                job_description=job_description,
                model_name=model_name,
                output_format=output_format,
                max_tokens=max_tokens
            )
            
            # Process the request
            response = await service.customize_resume(request)
        except UnicodeDecodeError:
            logger.warning("Failed to decode as text, using document processor")
            response = await service.customize_resume_from_file(
                file_content=file_content,
                file_type=file_type,
                job_description=job_description,
                model_name=model_name,
                output_format=output_format,
                max_tokens=max_tokens,
                filename=resume_file.filename
            )
    else:
        # Process non-text files with document processor
        logger.info(f"Processing file as {file_type}")
        response = await service.customize_resume_from_file(
            file_content=file_content,
            file_type=file_type,
            job_description=job_description,
            model_name=model_name,
            output_format=output_format,
            max_tokens=max_tokens,
            filename=resume_file.filename
        )
    
    processing_time_ms = round((time.time() - start_time) * 1000, 2)
    
    # Structure response with metadata
    return structure_response(
        data=response,
        extra_metadata={
            "processing_time_ms": processing_time_ms,
            "model_used": model_name,
            "file_type": file_type,
            "file_size": len(file_content),
            "output_format": output_format.value
        }
    )


# Simple endpoint for testing file upload
@router.post("/upload-test")
@handle_api_errors
async def upload_test(
    file: UploadFile = File(...)
) -> Dict:
    """Test endpoint for file upload.
    
    Args:
        file: Uploaded file
        
    Returns:
        dict: File information
    """
    file_content, detected_type = await APIUtils.process_uploaded_file(file)
    
    # Try to extract text content
    try:
        text_content = file_content.decode('utf-8')[:100]
    except UnicodeDecodeError:
        text_content = "Binary content"
    
    return structure_response(
        data={
            "filename": file.filename,
            "content_type": file.content_type,
            "detected_type": detected_type,
            "size": len(file_content),
            "content_sample": text_content
        },
        extra_metadata={
            "headers": dict(file.headers),
            "cached": False
        }
    )
