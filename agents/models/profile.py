"""Profile models for Resume Customizer."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProfessionalProfile(BaseModel):
    """Comprehensive professional profile extracted from a resume."""
    
    core_identity: str = Field(
        description="Distillation of candidate's unique value proposition"
    )
    
    technical_skills: List[str] = Field(
        description="Technical skills with evidence of application",
        default_factory=list
    )
    
    soft_skills: List[str] = Field(
        description="Soft skills with evidence of application",
        default_factory=list
    )
    
    projects: List[Dict] = Field(
        description="Project experience with impact metrics",
        default_factory=list
    )
    
    contribution_patterns: str = Field(
        description="How the candidate creates value"
    )
    
    interests: List[str] = Field(
        description="Professional interests and motivations",
        default_factory=list
    )
    
    work_style: str = Field(
        description="Communication and collaboration preferences"
    )
    
    experience_level: str = Field(
        description="Senior, mid-level, junior, etc.",
        default=""
    )
    
    career_trajectory: str = Field(
        description="Career path and progression",
        default=""
    )
    
    education: List[Dict] = Field(
        description="Educational background and qualifications",
        default_factory=list
    )
    
    metadata: Dict = Field(
        description="Additional processed information about the candidate",
        default_factory=dict
    )
