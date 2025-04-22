"""Job requirement models for job description analysis."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RequirementCategory(BaseModel):
    """Categorized job requirement with details."""
    
    name: str = Field(..., description="Name of the requirement category")
    items: List[str] = Field(..., description="Specific requirements in this category")
    importance: str = Field(
        ..., 
        description="Importance level (essential, preferred, bonus)"
    )


class CompanyContext(BaseModel):
    """Company context information from job description."""
    
    name: Optional[str] = Field(None, description="Company name")
    industry: Optional[str] = Field(None, description="Company industry")
    size: Optional[str] = Field(None, description="Company size (if mentioned)")
    culture: Optional[str] = Field(None, description="Company culture indications")
    mission: Optional[str] = Field(None, description="Company mission or values (if mentioned)")


class PositionDetails(BaseModel):
    """Details about the position being offered."""
    
    title: str = Field(..., description="Job title")
    department: Optional[str] = Field(None, description="Department or team")
    level: Optional[str] = Field(None, description="Seniority level or grade")
    reporting_structure: Optional[str] = Field(None, description="Reporting relationships")
    responsibilities: List[str] = Field(
        default_factory=list, 
        description="Key responsibilities of the role"
    )


class JobRequirements(BaseModel):
    """Analyzed job requirements from a job description."""
    
    company_profile: CompanyContext = Field(
        ...,
        description="Company context and position details"
    )
    position: PositionDetails = Field(
        ...,
        description="Details about the position"
    )
    core_requirements: List[RequirementCategory] = Field(
        default_factory=list,
        description="Must-have skills and qualifications"
    )
    supplementary_attributes: List[RequirementCategory] = Field(
        default_factory=list,
        description="Nice-to-have skills and qualities"
    )
    hidden_expectations: List[str] = Field(
        default_factory=list,
        description="Reading between the lines on expectations"
    )
    application_strategy: str = Field(
        ...,
        description="Areas to emphasize and address in application"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Critical terms for ATS optimization"
    )
    compensation_info: Optional[str] = Field(
        None,
        description="Any information about compensation or benefits"
    )
    work_arrangement: Optional[str] = Field(
        None,
        description="Remote, hybrid, or on-site arrangements"
    )
