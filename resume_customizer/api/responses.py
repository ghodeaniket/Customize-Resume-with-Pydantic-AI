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
        performance: Performance metrics for the operation (optional)
    """
    profile: ProfessionalProfile = Field(..., description="Professional profile extracted from resume")
    performance: Optional[PerformanceResponse] = Field(None, description="Performance metrics for the operation")


class JobRequirementsResponse(BaseModel):
    """Response model for job requirements analysis.
    
    Attributes:
        requirements: Job requirements extracted from job description
        performance: Performance metrics for the operation (optional)
    """
    requirements: JobRequirements = Field(..., description="Job requirements extracted from job description")
    performance: Optional[PerformanceResponse] = Field(None, description="Performance metrics for the operation")


class UploadResponse(BaseModel):
    """Response model for file upload.
    
    Attributes:
        filename: The original filename
        file_id: The ID of the uploaded file
        file_type: The MIME type of the file
        file_size: The size of the file in bytes
        extract_count: The number of characters extracted from the file
    """
    filename: str = Field(..., description="The original filename")
    file_id: str = Field(..., description="The ID of the uploaded file")
    file_type: str = Field(..., description="The MIME type of the file")
    file_size: int = Field(..., description="The size of the file in bytes")
    extract_count: Optional[int] = Field(None, description="The number of characters extracted from the file")


class PerformanceResponse(BaseModel):
    """Response model for performance metrics.
    
    Attributes:
        elapsed_time: The elapsed time in seconds
        timestamp: The timestamp of the request
        operation: The operation being performed
        cache_hit: Whether the result was retrieved from cache
    """
    elapsed_time: float = Field(..., description="The elapsed time in seconds")
    timestamp: float = Field(..., description="The timestamp of the request")
    operation: str = Field(..., description="The operation being performed")
    cache_hit: bool = Field(False, description="Whether the result was retrieved from cache")


class ResumeCustomizationResponse(BaseModel):
    """Response model for resume customization.
    
    Attributes:
        optimized_resume: The optimized resume
        profile: The professional profile used for customization (optional)
        requirements: The job requirements used for customization (optional)
        performance: Performance metrics for the operation (optional)
    """
    optimized_resume: OptimizedResume = Field(..., description="The optimized resume")
    profile: Optional[ProfessionalProfile] = Field(None, description="The professional profile used for customization")
    requirements: Optional[JobRequirements] = Field(None, description="The job requirements used for customization")
    performance: Optional[PerformanceResponse] = Field(None, description="Performance metrics for the operation")
