#!/usr/bin/env python3
"""
Test script that mocks the agent responses for the Resume Customizer API.

This script creates mock implementations of the agent functions
to allow testing of the API without requiring the pydantic-ai dependency.
"""

import os
import sys
import importlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the necessary modules
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.job import JobRequirements


# Create mock implementations for the agent functions
async def mock_analyze_resume(*args, **kwargs):
    """Mock implementation of analyze_resume function."""
    print(f"Mock analyze_resume called with args: {args}, kwargs: {kwargs}")
    
    # Return a mock ProfessionalProfile
    return ProfessionalProfile(
        core_identity="Experienced Software Engineer with Python/JavaScript expertise",
        technical_skills=["Python", "JavaScript", "AWS", "FastAPI", "React"],
        soft_skills=["Communication", "Leadership", "Problem Solving"],
        projects=[
            {
                "name": "Microservices Architecture",
                "description": "Led development of microservices",
                "impact": "Reduced system response time by 40%"
            }
        ],
        contribution_patterns="Strong technical leadership and mentoring",
        interests=["Cloud Architecture", "DevOps", "Web Development"],
        work_style="Collaborative team player with strong communication skills"
    )


async def mock_analyze_job_description(*args, **kwargs):
    """Mock implementation of analyze_job_description function."""
    print(f"Mock analyze_job_description called with args: {args}, kwargs: {kwargs}")
    
    # Return a mock JobRequirements
    return JobRequirements(
        company_profile="TechInnovate Inc. - Fintech startup with innovative payment processing platform",
        core_requirements=[
            "5+ years of backend development",
            "Strong proficiency in Python",
            "Experience with FastAPI or similar frameworks",
            "Solid understanding of RESTful API design"
        ],
        supplementary_attributes=[
            "Experience with asynchronous programming",
            "Knowledge of message queues",
            "Experience with GraphQL"
        ],
        hidden_expectations="Looking for self-starters who can work independently",
        application_strategy="Emphasize Python backend experience and API design",
        keywords=["Python", "FastAPI", "RESTful API", "PostgreSQL", "microservices"]
    )


async def mock_customize_resume(*args, **kwargs):
    """Mock implementation of customize_resume function."""
    print(f"Mock customize_resume called with args: {args}, kwargs: {kwargs}")
    
    # Return a mock optimized resume as Markdown string
    return """
# JOHN SMITH
**Senior Backend Engineer**
San Francisco, CA | (555) 123-4567 | john.smith@email.com | linkedin.com/in/johnsmith

## SUMMARY
Experienced Python Backend Engineer with 8+ years building scalable web applications and RESTful APIs. 
Specialized in microservices architecture and cloud solutions with a track record of optimizing 
system performance and mentoring development teams.

## SKILLS
- **Languages**: Python, JavaScript, TypeScript, SQL
- **Frameworks**: FastAPI, Django, React, Node.js, Express
- **Cloud**: AWS (EC2, S3, Lambda), Docker, Kubernetes
- **Databases**: PostgreSQL, MongoDB, Redis
- **Development**: RESTful API Design, Microservices, CI/CD, Agile

## EXPERIENCE
**Senior Software Engineer | TechCorp | San Francisco, CA | 2021 - Present**
- Led development of microservices architecture using Python and FastAPI, reducing system response time by 40%
- Designed and implemented high-performance API gateway handling 200+ requests per second
- Optimized PostgreSQL database queries, improving data retrieval efficiency by 60%
- Mentored junior developers through code reviews and pair programming sessions
- Implemented CI/CD pipelines with GitHub Actions, reducing deployment time from hours to minutes

**Software Engineer | DataSystems Inc. | Oakland, CA | 2018 - 2021**
- Built scalable data processing pipelines using Python and AWS Lambda
- Developed RESTful APIs for internal and customer-facing applications
- Optimized database performance through query tuning and proper indexing
- Collaborated with cross-functional teams to deliver features meeting business requirements

**Junior Developer | WebStart | San Jose, CA | 2016 - 2018**
- Created RESTful APIs using Django for customer-facing applications
- Implemented responsive UI components with React and Bootstrap
- Participated in agile development processes and sprint planning

## EDUCATION
**Bachelor of Science in Computer Science**
University of California, Berkeley | 2016
- Relevant coursework: Data Structures, Algorithms, Database Systems, Web Development

## CERTIFICATIONS
- AWS Certified Solutions Architect - Associate
- Docker Certified Associate
- MongoDB Certified Developer
"""


def apply_mocks():
    """Apply mocks to the agent functions."""
    # Create patch for analyze_resume
    analyze_resume_patch = patch(
        'resume_customizer.agents.profiler.analyze_resume', 
        mock_analyze_resume
    )
    
    # Create patch for analyze_job_description
    analyze_job_patch = patch(
        'resume_customizer.agents.researcher.analyze_job_description',
        mock_analyze_job_description
    )
    
    # Create patch for customize_resume
    customize_resume_patch = patch(
        'resume_customizer.agents.strategist.customize_resume',
        mock_customize_resume
    )
    
    # Apply the patches
    analyze_resume_patch.start()
    analyze_job_patch.start()
    customize_resume_patch.start()
    
    # Also patch the pydantic-ai imports
    sys.modules['pydantic_ai'] = MagicMock()
    
    print("✅ Applied mocks to agent functions")


if __name__ == "__main__":
    print("=" * 80)
    print("APPLYING MOCKS TO AGENT FUNCTIONS")
    print("=" * 80)
    
    apply_mocks()
    
    print("\nMocks applied successfully. You can now start the API with mocked agent functions.")
    print("Example: uvicorn resume_customizer.main:app --reload --port 9500")
