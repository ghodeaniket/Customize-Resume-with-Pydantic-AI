"""Resume customization endpoints."""
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from agents.models.resume import CustomizationRequest, CustomizationResponse, ResumeFormat
from api.dependencies import get_resume_customizer_service, get_settings
from core.config import Settings
from core.exceptions import ResumeCustomizerError
from services.customizer import ResumeCustomizerService


router = APIRouter(prefix="/resumes", tags=["resumes"])


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
        # Read file content
        file_content = await resume_file.read()
        
        # Apply default token limit if not specified
        if max_tokens is None:
            max_tokens = settings.default_token_limit
        
        # Process request
        response = await service.customize_resume_from_file(
            file_content=file_content,
            file_type=resume_file.content_type,
            job_description=job_description,
            model_name=model_name,
            output_format=output_format,
            max_tokens=max_tokens
        )
        
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
