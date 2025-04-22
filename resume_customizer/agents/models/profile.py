"""Professional profile models for resume analysis."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SkillDetails(BaseModel):
    """Detailed information about a skill."""
    
    name: str = Field(..., description="Name of the skill")
    proficiency: str = Field(..., description="Proficiency level (e.g., beginner, intermediate, expert)")
    evidence: List[str] = Field(
        default_factory=list,
        description="Evidence of skill application from resume"
    )


class ProjectExperience(BaseModel):
    """Project experience with impact metrics."""
    
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Brief description of the project")
    role: str = Field(..., description="Role in the project")
    skills_used: List[str] = Field(
        default_factory=list, 
        description="Skills demonstrated in this project"
    )
    impact_metrics: List[str] = Field(
        default_factory=list,
        description="Quantitative or qualitative impact measurements"
    )
    duration: Optional[str] = Field(None, description="Duration of the project")


class WorkExperience(BaseModel):
    """Work experience from a resume."""
    
    company: str = Field(..., description="Company name")
    position: str = Field(..., description="Job title/position")
    duration: str = Field(..., description="Employment duration")
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Key responsibilities in the role"
    )
    achievements: List[str] = Field(
        default_factory=list,
        description="Notable achievements and impacts"
    )


class Education(BaseModel):
    """Educational background information."""
    
    institution: str = Field(..., description="Name of educational institution")
    degree: str = Field(..., description="Degree obtained or pursued")
    field_of_study: str = Field(..., description="Field or major of study")
    graduation_date: Optional[str] = Field(None, description="Graduation date or expected graduation")
    gpa: Optional[str] = Field(None, description="GPA if provided")
    relevant_coursework: List[str] = Field(
        default_factory=list,
        description="Relevant courses taken"
    )


class ProfessionalProfile(BaseModel):
    """Comprehensive professional profile extracted from a resume."""
    
    core_identity: str = Field(
        ..., 
        description="Distillation of candidate's unique value proposition"
    )
    technical_skills: List[SkillDetails] = Field(
        default_factory=list,
        description="Technical skills with evidence of application"
    )
    soft_skills: List[SkillDetails] = Field(
        default_factory=list,
        description="Soft skills with evidence of application"
    )
    work_experience: List[WorkExperience] = Field(
        default_factory=list,
        description="Work experience entries"
    )
    projects: List[ProjectExperience] = Field(
        default_factory=list,
        description="Project experience with impact metrics"
    )
    education: List[Education] = Field(
        default_factory=list,
        description="Educational background"
    )
    contribution_patterns: str = Field(
        ...,
        description="How the candidate creates value in their work"
    )
    interests: List[str] = Field(
        default_factory=list,
        description="Professional interests and motivations"
    )
    work_style: str = Field(
        ...,
        description="Communication and collaboration preferences"
    )
    career_highlights: List[str] = Field(
        default_factory=list,
        description="Key career achievements and notable experiences"
    )
