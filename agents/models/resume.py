"""Resume models for Resume Customizer."""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ResumeFormat(str, Enum):
    """Output format for optimized resume."""
    
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"


class ResumeSection(BaseModel):
    """Section of a resume with title and content."""
    
    title: str
    content: str


class OptimizedResume(BaseModel):
    """Optimized resume output from the Strategist agent."""
    
    content: str = Field(
        description="Full resume content in specified format"
    )
    
    format: ResumeFormat = Field(
        description="Format of the resume content",
        default=ResumeFormat.MARKDOWN
    )
    
    sections: List[ResumeSection] = Field(
        description="Individual resume sections",
        default_factory=list
    )
    
    optimizations: List[str] = Field(
        description="List of optimizations applied to the resume",
        default_factory=list
    )
    
    keywords_included: List[str] = Field(
        description="Keywords from job description included in the resume",
        default_factory=list
    )
    
    ats_score: Optional[float] = Field(
        description="Estimated ATS matching score (0-100)",
        default=None
    )
    
    improvement_areas: List[str] = Field(
        description="Areas where the resume could be further improved",
        default_factory=list
    )


class CustomizationRequest(BaseModel):
    """Request model for resume customization."""
    
    resume_content: str = Field(
        description="Full text content of the resume"
    )
    
    job_description: str = Field(
        description="Full text content of the job description"
    )
    
    model_name: str = Field(
        description="The AI model to use for customization",
        default="deepseek/deepseek-r1-distill-llama-70b"
    )
    
    output_format: ResumeFormat = Field(
        description="Desired output format",
        default=ResumeFormat.MARKDOWN
    )
    
    max_tokens: Optional[int] = Field(
        description="Maximum number of tokens to generate",
        default=None
    )


class CustomizationResponse(BaseModel):
    """Response model for resume customization."""
    
    optimized_resume: OptimizedResume
    
    usage_stats: Optional[Dict] = Field(
        description="Token usage statistics",
        default=None
    )
