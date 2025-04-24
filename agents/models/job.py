"""Job models for Resume Customizer."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JobRequirements(BaseModel):
    """Analyzed job requirements from a job description."""
    
    company_profile: str = Field(
        description="Company context and position"
    )
    
    core_requirements: List[str] = Field(
        description="Must-have skills and qualifications",
        default_factory=list
    )
    
    supplementary_attributes: List[str] = Field(
        description="Nice-to-have skills and qualities",
        default_factory=list
    )
    
    hidden_expectations: str = Field(
        description="Reading between the lines on expectations"
    )
    
    application_strategy: str = Field(
        description="Areas to emphasize and address"
    )
    
    keywords: List[str] = Field(
        description="Critical terms for ATS optimization",
        default_factory=list
    )
    
    company_values: List[str] = Field(
        description="Company culture and values mentioned in the job description",
        default_factory=list
    )
    
    required_experience: str = Field(
        description="Years of experience required",
        default=""
    )
    
    tech_stack: List[str] = Field(
        description="Technologies and tools mentioned in the job description",
        default_factory=list
    )
    
    education_requirements: str = Field(
        description="Required education level and field",
        default=""
    )
    
    metadata: Dict = Field(
        description="Additional processed information about the job",
        default_factory=dict
    )
