"""API response models for the Resume Customizer application.

This module contains Pydantic models that define the structure of API responses.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume


class ErrorResponse(BaseModel):
    """Error response model.
    
    Attributes:
        error: Error message
        detail: Additional error details
        status_code: HTTP status code
    """
    error: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    status_code: int = Field(400, description="HTTP status code")


class HealthCheckResponse(BaseModel):
    """Health check response model.
    
    Attributes:
        status: Service status
        version: API version
    """
    status: str = Field("ok", description="Service status")
    version: str = Field(..., description="API version")


class ProfileResponse(BaseModel):
    """Response model for resume profile analysis.
    
    Attributes:
        profile: Professional profile extracted from resume
    """
    profile: ProfessionalProfile = Field(..., description="Professional profile extracted from resume")


class JobRequirementsResponse(BaseModel):
    """Response model for job requirements analysis.
    
    Attributes:
        requirements: Job requirements extracted from job description
    """
    requirements: JobRequirements = Field(..., description="Job requirements extracted from job description")


class ResumeCustomizationResponse(BaseModel):
    """Response model for resume customization.
    
    Attributes:
        optimized_resume: The optimized resume
        profile: The professional profile used for customization (optional)
        requirements: The job requirements used for customization (optional)
    """
    optimized_resume: OptimizedResume = Field(..., description="The optimized resume")
    profile: Optional[ProfessionalProfile] = Field(None, description="The professional profile used for customization")
    requirements: Optional[JobRequirements] = Field(None, description="The job requirements used for customization")
