"""Tests for agent integration.

This module contains tests to verify the proper integration and delegation
between the different agents (Profiler, Researcher, Strategist).
"""

import os
import io
import pytest
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.agents.strategist import customize_resume
from resume_customizer.agents.infrastructure import ResumeCustomizerDeps


# Test file paths
TEST_DIR = Path(__file__).parent.parent.parent
TEST_RESUME_TXT = TEST_DIR / "test_resume.txt"
TEST_JOB_DESC_TXT = TEST_DIR / "test_job_description.txt"


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
def test_resume_content():
    """Get the content of the test resume."""
    with open(TEST_RESUME_TXT, "r") as f:
        return f.read()


@pytest.fixture
def test_job_description():
    """Get the content of the test job description."""
    # If test job description file doesn't exist, return a sample
    if not TEST_JOB_DESC_TXT.exists():
        return """
        Software Engineer - Backend
        
        We are looking for a talented Backend Software Engineer to join our team.
        The ideal candidate will have strong experience with Python, FastAPI, and
        cloud technologies like AWS or GCP.
        
        Key Requirements:
        - 5+ years of experience in software development
        - Strong Python programming skills
        - Experience with FastAPI or similar frameworks
        - Knowledge of cloud services (AWS, GCP)
        - Solid understanding of database systems
        
        Nice to have:
        - Experience with machine learning or AI
        - Knowledge of Docker and Kubernetes
        - Familiarity with CI/CD pipelines
        """
    
    with open(TEST_JOB_DESC_TXT, "r") as f:
        return f.read()


@pytest.mark.asyncio
@patch("resume_customizer.agents.profiler.profiler_agent.run")
async def test_analyze_resume_with_text(mock_agent_run, mock_http_client, test_resume_content):
    """Test analyzing a resume with text content."""
    # Mock agent response
    mock_result = MagicMock()
    mock_result.output = {
        "core_identity": "Senior Software Engineer with focus on Python backend development",
        "technical_skills": [],
        "soft_skills": [],
        "work_experience": [],
        "projects": [],
        "education": [],
        "contribution_patterns": "Leads development teams and optimizes systems",
        "interests": [],
        "work_style": "Collaborative and detail-oriented",
        "career_highlights": []
    }
    mock_agent_run.return_value = mock_result
    
    # Analyze resume
    result = await analyze_resume(
        resume_content=test_resume_content,
        http_client=mock_http_client
    )
    
    # Assertions
    assert result is not None
    assert mock_agent_run.called
    assert "Senior Software Engineer" in result.core_identity


@pytest.mark.asyncio
@patch("resume_customizer.agents.researcher.researcher_agent.run")
async def test_analyze_job_description(mock_agent_run, mock_http_client, test_job_description):
    """Test analyzing a job description."""
    # Mock agent response
    mock_result = MagicMock()
    mock_result.output = {
        "company_profile": {},
        "position": {
            "title": "Software Engineer - Backend",
            "department": "Engineering",
            "level": "Senior",
            "responsibilities": ["Backend development", "API design"]
        },
        "core_requirements": [],
        "supplementary_attributes": [],
        "hidden_expectations": [],
        "application_strategy": "Emphasize Python and cloud experience",
        "keywords": ["Python", "FastAPI", "AWS", "GCP"]
    }
    mock_agent_run.return_value = mock_result
    
    # Analyze job description
    result = await analyze_job_description(
        job_description=test_job_description,
        http_client=mock_http_client
    )
    
    # Assertions
    assert result is not None
    assert mock_agent_run.called
    assert "Python" in result.keywords


@pytest.mark.asyncio
@patch("resume_customizer.agents.strategist.strategist_agent.run")
@patch("resume_customizer.agents.strategist.get_job_insights")
@patch("resume_customizer.agents.strategist.get_resume_insights")
async def test_customize_resume(
    mock_get_resume_insights,
    mock_get_job_insights,
    mock_agent_run,
    mock_http_client,
    test_resume_content,
    test_job_description
):
    """Test customizing a resume."""
    # Mock agent responses
    mock_resume_profile = MagicMock()
    mock_resume_profile.core_identity = "Senior Software Engineer with Python expertise"
    mock_resume_profile.technical_skills = []
    mock_resume_profile.soft_skills = []
    mock_get_resume_insights.return_value = mock_resume_profile
    
    mock_job_requirements = MagicMock()
    mock_job_requirements.keywords = ["Python", "FastAPI", "AWS"]
    mock_job_requirements.core_requirements = []
    mock_job_requirements.application_strategy = "Emphasize Python experience"
    mock_job_requirements.company_profile = "Tech company"
    mock_job_requirements.hidden_expectations = "Strong problem-solving skills"
    mock_get_job_insights.return_value = mock_job_requirements
    
    mock_result = MagicMock()
    mock_result.output = "# John Smith\nSenior Software Engineer\n\n## Skills\n- Python\n- FastAPI\n- AWS"
    mock_agent_run.return_value = mock_result
    
    # Customize resume
    result = await customize_resume(
        resume_content=test_resume_content,
        job_description=test_job_description,
        http_client=mock_http_client
    )
    
    # Assertions
    assert result is not None
    assert mock_agent_run.called
    assert "# John Smith" in result.content
    assert result.optimization_summary is not None
    assert len(result.optimization_summary.key_changes) > 0
    assert "Python" in result.content


@pytest.mark.asyncio
@patch("resume_customizer.agents.profiler.DocumentProcessor.extract_text")
@patch("resume_customizer.agents.profiler.profiler_agent.run")
async def test_delegation_with_file(
    mock_agent_run,
    mock_extract_text,
    mock_http_client,
    test_resume_content
):
    """Test delegation with a file input."""
    # Mock text extraction
    mock_extract_text.return_value = test_resume_content
    
    # Mock agent response
    mock_result = MagicMock()
    mock_result.output = {
        "core_identity": "Senior Software Engineer with focus on Python backend development",
        "technical_skills": [],
        "soft_skills": [],
        "work_experience": [],
        "projects": [],
        "education": [],
        "contribution_patterns": "Leads development teams and optimizes systems",
        "interests": [],
        "work_style": "Collaborative and detail-oriented",
        "career_highlights": []
    }
    mock_agent_run.return_value = mock_result
    
    # Create a mock file
    file_path = Path(TEST_RESUME_TXT)
    
    # Analyze resume
    result = await analyze_resume(
        resume_content=file_path,
        http_client=mock_http_client
    )
    
    # Assertions
    assert result is not None
    assert mock_extract_text.called
    assert mock_agent_run.called
    assert "Senior Software Engineer" in result.core_identity
