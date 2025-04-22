"""Resume output models for optimized resumes."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ResumeSection(str, Enum):
    """Standard sections in a resume."""
    
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    PUBLICATIONS = "publications"
    ACHIEVEMENTS = "achievements"
    INTERESTS = "interests"
    LANGUAGES = "languages"
    REFERENCES = "references"


class ResumeFormat(str, Enum):
    """Resume output formats."""
    
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    JSON = "json"


class ResumeOptimizationSummary(BaseModel):
    """Summary of optimizations made to a resume."""
    
    key_changes: List[str] = Field(
        default_factory=list,
        description="Major changes made to the resume"
    )
    alignment_points: List[str] = Field(
        default_factory=list, 
        description="How the resume aligns with job requirements"
    )
    ats_optimization: List[str] = Field(
        default_factory=list,
        description="Changes made to improve ATS compatibility"
    )


class OptimizedResume(BaseModel):
    """Optimized resume with metadata."""
    
    content: str = Field(..., description="The full content of the optimized resume")
    format: ResumeFormat = Field(
        ResumeFormat.MARKDOWN,
        description="Format of the resume content"
    )
    optimization_summary: ResumeOptimizationSummary = Field(
        ...,
        description="Summary of the optimizations made"
    )
    sections_modified: List[ResumeSection] = Field(
        default_factory=list,
        description="Sections that were modified"
    )
    keyword_matches: Dict[str, int] = Field(
        default_factory=dict,
        description="Job keywords included and their count in the resume"
    )
    compatibility_score: Optional[float] = Field(
        None,
        description="Estimated compatibility score with the job (0-100)"
    )
