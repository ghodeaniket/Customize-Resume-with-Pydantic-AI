"""Test configuration and fixtures for the Resume Customizer application."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from resume_customizer.agents.infrastructure import ResumeCustomizerDeps
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume
from resume_customizer.core.config import settings
from resume_customizer.main import app as fastapi_app


@pytest.fixture
def app() -> FastAPI:
    """Fixture for the FastAPI app.
    
    Returns:
        FastAPI: The FastAPI application
    """
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Fixture for a FastAPI test client.
    
    Args:
        app: The FastAPI application
        
    Yields:
        TestClient: A test client for the application
    """
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture for an async HTTPX client.
    
    Args:
        app: The FastAPI application
        
    Yields:
        AsyncClient: An async client for the application
    """
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Fixture for an async HTTPX client for external requests.
    
    Yields:
        AsyncClient: An async HTTP client
    """
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def sample_resume_content() -> str:
    """Fixture for sample resume content.
    
    Returns:
        str: Sample resume content
    """
    return """
    JOHN DOE
    Software Engineer
    
    CONTACT
    Email: john.doe@example.com
    Phone: (555) 123-4567
    LinkedIn: linkedin.com/in/johndoe
    
    SUMMARY
    Experienced software engineer with 5+ years specializing in backend development
    with Python and Node.js. Proven track record of designing scalable microservices
    and optimizing database performance.
    
    SKILLS
    - Languages: Python, JavaScript, TypeScript, SQL
    - Frameworks: FastAPI, Django, Express, React
    - Databases: PostgreSQL, MongoDB, Redis
    - Tools: Docker, Kubernetes, AWS, CI/CD
    
    EXPERIENCE
    Senior Software Engineer | TechCorp Inc. | 2020 - Present
    - Led development of a high-performance API serving 10M+ daily requests
    - Reduced database query times by 40% through optimization
    - Mentored junior developers and conducted code reviews
    - Implemented automated testing that increased code coverage from 65% to 92%
    
    Software Engineer | DataSystems LLC | 2018 - 2020
    - Developed microservices architecture supporting 50K concurrent users
    - Designed and implemented RESTful APIs using Node.js and Express
    - Optimized MongoDB queries resulting in 30% faster response times
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology, 2018
    GPA: 3.8/4.0
    """


@pytest.fixture
def sample_job_description() -> str:
    """Fixture for sample job description.
    
    Returns:
        str: Sample job description
    """
    return """
    Senior Backend Engineer
    
    About Us:
    TechInnovate is a leading technology company specializing in cloud-native 
    solutions for enterprise clients. We're looking for a talented Senior Backend 
    Engineer to join our growing team.
    
    Responsibilities:
    - Design and implement scalable, high-performance backend services
    - Write clean, maintainable, and well-tested code
    - Collaborate with frontend developers and product managers
    - Mentor junior developers and conduct code reviews
    - Contribute to architecture discussions and technical decisions
    
    Requirements:
    - 5+ years of experience in backend development
    - Strong proficiency in Python and at least one Python framework (FastAPI, Django, Flask)
    - Experience with SQL and NoSQL databases
    - Knowledge of container technologies (Docker, Kubernetes)
    - Experience with cloud platforms (AWS, GCP, or Azure)
    - Strong problem-solving skills and attention to detail
    
    Nice-to-Have:
    - Experience with message queues (Kafka, RabbitMQ)
    - Knowledge of GraphQL
    - Experience with microservices architecture
    - Contributions to open-source projects
    
    Benefits:
    - Competitive salary and equity
    - Health, dental, and vision insurance
    - Flexible work schedule and remote options
    - Professional development budget
    - 401(k) matching
    
    Location: Remote (US time zones preferred)
    """


@pytest.fixture
def mock_agent_dependencies() -> ResumeCustomizerDeps:
    """Fixture for mock agent dependencies.
    
    Returns:
        ResumeCustomizerDeps: Mock dependencies for agent tests
    """
    # Create a synchronous HTTP client for testing
    client = httpx.Client()
    
    # Create dependencies with test API key
    return ResumeCustomizerDeps(
        http_client=client,  # Type mismatch for testing purposes
        openrouter_api_key="test-api-key",
        model_name="test-model"
    )


@pytest.fixture
def mock_professional_profile() -> ProfessionalProfile:
    """Fixture for a mock professional profile.
    
    Returns:
        ProfessionalProfile: A mock professional profile
    """
    return ProfessionalProfile(
        core_identity="Experienced backend engineer specializing in scalable systems",
        technical_skills=[],
        soft_skills=[],
        work_experience=[],
        projects=[],
        education=[],
        contribution_patterns="Delivers high-performance solutions through optimization",
        interests=["Backend development", "Databases", "System design"],
        work_style="Collaborative and detail-oriented",
        career_highlights=["Led high-performance API development", "Optimized database performance"]
    )


@pytest.fixture
def mock_job_requirements() -> JobRequirements:
    """Fixture for mock job requirements.
    
    Returns:
        JobRequirements: Mock job requirements
    """
    return JobRequirements(
        company_profile=CompanyContext(
            name="TechInnovate",
            industry="Technology",
            culture="Innovative and collaborative"
        ),
        position=PositionDetails(
            title="Senior Backend Engineer",
            responsibilities=["Design backend services", "Write clean code"]
        ),
        core_requirements=[],
        supplementary_attributes=[],
        hidden_expectations=["Leadership potential", "Ability to work independently"],
        application_strategy="Emphasize backend experience and Python expertise",
        keywords=["Python", "FastAPI", "Backend", "Microservices"]
    )


@pytest.fixture
def mock_optimized_resume() -> OptimizedResume:
    """Fixture for a mock optimized resume.
    
    Returns:
        OptimizedResume: A mock optimized resume
    """
    return OptimizedResume(
        content="# John Doe\nSenior Software Engineer\n\n## Summary\nExperienced backend engineer...",
        format="markdown",
        optimization_summary=ResumeOptimizationSummary(
            key_changes=["Emphasized Python experience", "Highlighted API development"],
            alignment_points=["Backend expertise matches job requirements"],
            ats_optimization=["Added key technical terms"]
        ),
        sections_modified=["summary", "experience", "skills"],
        keyword_matches={"Python": 3, "API": 2}
    )


# This is needed to properly import from the fixtures
from resume_customizer.agents.models.job import CompanyContext, PositionDetails  # noqa
from resume_customizer.agents.models.resume import ResumeOptimizationSummary  # noqa
