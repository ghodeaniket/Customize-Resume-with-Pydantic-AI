"""Resume customization endpoints."""
import logging
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from agents.models.resume import CustomizationRequest, CustomizationResponse, ResumeFormat
from api.dependencies import get_resume_customizer_service, get_settings
from core.config import Settings
from core.exceptions import ResumeCustomizerError
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
        logger.info(f"File size: {len(file_content)} bytes")
        
        # Try to decode the first few bytes to see if it's text
        try:
            sample = file_content[:100].decode('utf-8')
            logger.info(f"First 100 chars: {sample}")
        except:
            logger.info("File is not UTF-8 text")
        
        # Use the correct file type based on the filename extension
        file_type = "text/plain"  # Default
        if resume_file.filename:
            if resume_file.filename.lower().endswith(".pdf"):
                file_type = "application/pdf"
            elif resume_file.filename.lower().endswith(".docx"):
                file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif resume_file.filename.lower().endswith(".txt"):
                file_type = "text/plain"
        
        logger.info(f"Determined file type: {file_type}")
        
        # Apply default token limit if not specified
        if max_tokens is None:
            max_tokens = settings.default_token_limit
        
        # Process request with direct text content for text files
        if file_type == "text/plain":
            # For plain text files, we'll just decode the content directly
            resume_content = file_content.decode('utf-8').strip()
            logger.info(f"Decoded text file content: {resume_content}")
            
            # Create a customization request directly
            request = CustomizationRequest(
                resume_content=resume_content,
                job_description=job_description,
                model_name=model_name,
                output_format=output_format,
                max_tokens=max_tokens
            )
            
            # Process the request directly
            return await service.customize_resume(request)
        else:
            # For other file types, use the service's file processing
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
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
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
    
    try:
        text_content = content.decode('utf-8')
    except:
        text_content = "Binary content"
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "content_sample": text_content[:100] if text_content else None,
        "headers": dict(file.headers)
    }
