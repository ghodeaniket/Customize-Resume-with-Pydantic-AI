#!/usr/bin/env python3
"""
Mock server for the Resume Customizer API.

This script creates a modified version of the main application with mocked
agent functions to allow testing of the API without requiring the actual
AI agent functionality.
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Mock pydantic_ai before importing any project modules
sys.modules['pydantic_ai'] = MagicMock()

# Create mock Agent class that will be used in the project
agent_instance = MagicMock()
agent_instance.run.return_value.output = "Mocked agent response"

# Make the Agent constructor return our mocked instance
sys.modules['pydantic_ai'].Agent = MagicMock(return_value=agent_instance)

# Mock the RunContext class
sys.modules['pydantic_ai'].RunContext = MagicMock

# Import necessary modules from our project
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.resume import OptimizedResume, ResumeFormat, ResumeOptimizationSummary


# Create mock implementations for the agent functions
async def mock_analyze_resume(*args, **kwargs):
    """Mock implementation of analyze_resume function."""
    print(f"Mock analyze_resume called")
    
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
    print(f"Mock analyze_job_description called")
    
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
    print(f"Mock customize_resume called")
    
    # Return a mock optimized resume
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
"""


# Now apply our mocks to the project modules
import resume_customizer.agents.profiler
import resume_customizer.agents.researcher
import resume_customizer.agents.strategist

# Replace the original functions with our mocks
resume_customizer.agents.profiler.analyze_resume = mock_analyze_resume
resume_customizer.agents.researcher.analyze_job_description = mock_analyze_job_description
resume_customizer.agents.strategist.customize_resume = mock_customize_resume

# Make sure all tool functions return what we expect
for tool_func in agent_instance.tool.return_value.side_effect.mock_calls:
    tool_func.return_value = "Mocked tool function response"

# Now run the actual server
if __name__ == "__main__":
    print("=" * 80)
    print("STARTING RESUME CUSTOMIZER API WITH MOCKED AGENTS")
    print("=" * 80)
    
    import uvicorn
    uvicorn.run(
        "resume_customizer.main:app",
        host="127.0.0.1",
        port=9700,
        reload=True
    )
