"""Resume customization API endpoints.

This module contains the API routes for resume customization.
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse

from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.agents.strategist import customize_resume
from resume_customizer.api.dependencies import get_http_client, verify_api_key
from resume_customizer.api.responses import (
    JobRequirementsResponse,
    ProfileResponse,
    ResumeCustomizationResponse
)
from resume_customizer.core.exceptions import (
    AgentError,
    DocumentProcessingError,
    ResumeCustomizerException
)
from resume_customizer.core.logging import app_logger as logger


# Create router
router = APIRouter(prefix="/resumes", tags=["Resumes"])


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
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Analyze a resume and create a professional profile.
    
    Args:
        resume_content: The resume content
        model_name: Optional override for the model name
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        ProfileResponse: The extracted professional profile
    """
    try:
        logger.info("Received request to analyze resume")
        
        # Analyze the resume
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
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Customize a resume for a specific job.
    
    Args:
        resume_content: The resume content
        job_description: The job description content
        model_name: Optional override for the model name
        include_analysis: Whether to include full analysis in the response
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        ResumeCustomizationResponse: The customized resume
    """
    try:
        logger.info("Received request to customize resume")
        
        # Customize the resume
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
