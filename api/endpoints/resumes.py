"""Resume customization endpoints."""
import logging
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from agents.models.resume import CustomizationRequest, CustomizationResponse, ResumeFormat
from api.dependencies import get_resume_customizer_service, get_settings
from core.config import Settings
from core.exceptions import ResumeCustomizerError, DocumentProcessingError
from core.utils.file_detection import detect_file_type, TEXT_MIME_TYPE
from services.customizer import ResumeCustomizerService


router = APIRouter(prefix="/resumes", tags=["resumes"])
logger = logging.getLogger(__name__)


@router.post(
    "/customize", 
    response_model=CustomizationResponse,
    summary="Customize a resume for a job description",
    description="Customize a resume based on a specific job description"
)
async def customize_resume(
    request: CustomizationRequest,
    service: ResumeCustomizerService = Depends(get_resume_customizer_service),
    settings: Settings = Depends(get_settings)
) -> CustomizationResponse:
    """Customize a resume for a specific job description.
    
    Args:
        request: Customization request
        service: Resume customizer service
        settings: Application settings
        
    Returns:
        CustomizationResponse: Customization response with optimized resume
        
    Raises:
        HTTPException: If an error occurs during customization
    """
    try:
        # Apply default token limit if not specified
        if request.max_tokens is None:
            request.max_tokens = settings.default_token_limit
        
        # Process request
        response = await service.customize_resume(request)
        return response
        
    except ResumeCustomizerError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.error(f"Error in customize_resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Error customizing resume: {str(e)}"}
        )


@router.post(
    "/customize-upload", 
    response_model=CustomizationResponse,
    summary="Customize a resume from file upload",
    description="Customize a resume from file upload based on a specific job description"
)
async def customize_resume_upload(
    job_description: str = Form(...),
    resume_file: UploadFile = File(...),
    model_name: str = Form("deepseek/deepseek-r1-distill-llama-70b"),
    output_format: ResumeFormat = Form(ResumeFormat.MARKDOWN),
    max_tokens: Optional[int] = Form(None),
    service: ResumeCustomizerService = Depends(get_resume_customizer_service),
    settings: Settings = Depends(get_settings)
) -> CustomizationResponse:
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
        CustomizationResponse: Customization response with optimized resume
        
    Raises:
        HTTPException: If an error occurs during customization
    """
    try:
        # Enhanced logging for debugging
        logger.info(f"Received file: {resume_file.filename}, "
                   f"Content type: {resume_file.content_type}, "
                   f"Headers: {resume_file.headers}")
        
        # Read file content
        file_content = await resume_file.read()
        if not file_content or len(file_content) == 0:
            logger.error("Empty file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Empty file uploaded"}
            )
            
        logger.info(f"File size: {len(file_content)} bytes")
        
        # Use the centralized file detection utility
        file_type = detect_file_type(file_content, resume_file.content_type, resume_file.filename)
        logger.info(f"Detected file type: {file_type}")
        
        # Apply default token limit if not specified
        if max_tokens is None:
            max_tokens = settings.default_token_limit
        
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
                return await service.customize_resume(request)
            except UnicodeDecodeError:
                logger.warning("Failed to decode as text, will use document processor")
        
        # For all file types (or if text decoding failed), use the document processor
        logger.info(f"Processing file as {file_type}")
        response = await service.customize_resume_from_file(
            file_content=file_content,
            file_type=file_type,
            job_description=job_description,
            model_name=model_name,
            output_format=output_format,
            max_tokens=max_tokens
        )
        
        return response
        
    except ResumeCustomizerError as e:
        logger.error(f"Resume customizer error: {e.message}", exc_info=True)
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.error(f"Unexpected error in customize_resume_upload: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Error customizing resume: {str(e)}"}
        )


# Simple endpoint for testing file upload
@router.post("/upload-test")
async def upload_test(
    file: UploadFile = File(...)
):
    """Test endpoint for file upload.
    
    Args:
        file: Uploaded file
        
    Returns:
        dict: File information
    """
    content = await file.read()
    text_content = None
    
    # Use the centralized file detection utility
    detected_type = detect_file_type(content, file.content_type, file.filename)
    
    try:
        text_content = content.decode('utf-8')
    except:
        text_content = "Binary content"
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "detected_type": detected_type,
        "size": len(content),
        "content_sample": text_content[:100] if text_content else None,
        "headers": dict(file.headers)
    }
