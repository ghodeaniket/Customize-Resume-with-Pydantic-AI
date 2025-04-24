"""Tests for resume customization API endpoints.

This module contains tests for the resume customization API endpoints.
"""

import io
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import UploadFile
from fastapi.testclient import TestClient

from resume_customizer.main import app
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.resume import OptimizedResume, ResumeOptimizationSummary


# Test data
TEST_DIR = Path(__file__).parent.parent.parent
TEST_RESUME_TXT = TEST_DIR / "test_resume.txt"


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from resume_customizer.api.dependencies import verify_api_key
    
    # Override API key verification for testing
    app.dependency_overrides[verify_api_key] = lambda: "test_api_key"
    
    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_resume_content():
    """Get the content of the test resume."""
    with open(TEST_RESUME_TXT, "r") as f:
        return f.read()


@pytest.fixture
def test_job_description():
    """Create a sample job description."""
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


@pytest.fixture
def mock_profile():
    """Create a mock professional profile."""
    return ProfessionalProfile(
        core_identity="Senior Software Engineer with Python expertise",
        technical_skills=[],
        soft_skills=[],
        work_experience=[],
        projects=[],
        education=[],
        contribution_patterns="Leads development teams and optimizes systems",
        interests=[],
        work_style="Collaborative and detail-oriented",
        career_highlights=[]
    )


@pytest.fixture
def mock_requirements():
    """Create mock job requirements."""
    return JobRequirements(
        company_profile=MagicMock(),
        position=MagicMock(
            title="Software Engineer - Backend",
            department="Engineering",
            level="Senior",
            responsibilities=["Backend development", "API design"]
        ),
        application_strategy="Emphasize Python and cloud experience",
        keywords=["Python", "FastAPI", "AWS", "GCP"],
        core_requirements=[],
        supplementary_attributes=[],
        hidden_expectations=[]
    )


@pytest.fixture
def mock_optimized_resume():
    """Create a mock optimized resume."""
    return OptimizedResume(
        content="# John Smith\nSenior Software Engineer\n\n## Skills\n- Python\n- FastAPI\n- AWS",
        optimization_summary=ResumeOptimizationSummary(
            key_changes=["Restructured resume to highlight Python skills"],
            alignment_points=["Emphasized cloud experience"],
            ats_optimization=["Added key skills in bullet points"]
        )
    )


def test_api_healthcheck(client):
    """Test the API health check endpoint."""
    response = client.get("/api/v1/health/check")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("resume_customizer.api.endpoints.resumes.analyze_resume")
def test_analyze_resume_endpoint(mock_analyze_resume, client, test_resume_content, mock_profile):
    """Test the analyze resume endpoint."""
    # Mock agent response
    mock_analyze_resume.return_value = mock_profile
    
    # Make request
    response = client.post(
        "/api/v1/resumes/analyze",
        data={"resume_content": test_resume_content}
    )
    
    # Assertions
    assert response.status_code == 200
    assert "profile" in response.json()
    assert response.json()["profile"]["core_identity"] == mock_profile.core_identity


@patch("resume_customizer.api.endpoints.resumes.analyze_job_description")
def test_analyze_job_endpoint(mock_analyze_job, client, test_job_description, mock_requirements):
    """Test the analyze job description endpoint."""
    # Mock agent response
    mock_analyze_job.return_value = mock_requirements
    
    # Make request
    response = client.post(
        "/api/v1/resumes/analyze-job",
        data={"job_description": test_job_description}
    )
    
    # Assertions
    assert response.status_code == 200
    assert "requirements" in response.json()
    assert "Python" in response.json()["requirements"]["keywords"]


@patch("resume_customizer.api.endpoints.resumes.customize_resume")
def test_customize_resume_endpoint(
    mock_customize_resume,
    client,
    test_resume_content,
    test_job_description,
    mock_optimized_resume
):
    """Test the customize resume endpoint."""
    # Mock agent response
    mock_customize_resume.return_value = mock_optimized_resume
    
    # Make request
    response = client.post(
        "/api/v1/resumes/customize",
        data={
            "resume_content": test_resume_content,
            "job_description": test_job_description
        }
    )
    
    # Assertions
    assert response.status_code == 200
    assert "optimized_resume" in response.json()
    assert "# John Smith" in response.json()["optimized_resume"]["content"]


@patch("resume_customizer.api.endpoints.resumes.DocumentProcessor.extract_text")
@patch("resume_customizer.api.endpoints.resumes.DocumentProcessor.save_file")
@patch("resume_customizer.api.endpoints.resumes.DocumentProcessor.is_valid_file")
def test_upload_resume_endpoint(
    mock_is_valid_file,
    mock_save_file,
    mock_extract_text,
    client
):
    """Test the upload resume endpoint."""
    # Mock responses
    mock_is_valid_file.return_value = True
    mock_save_file.return_value = Path("/tmp/test_resume.txt")
    mock_extract_text.return_value = "Resume content"
    
    # Create a test file
    test_file_content = b"Test resume content"
    test_file = io.BytesIO(test_file_content)
    
    # Make request
    response = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("test_resume.txt", test_file, "text/plain")},
        data={"extract_text": "true"}
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["filename"] == "test_resume.txt"
    assert response.json()["file_type"] == "text/plain"
    assert "extract_count" in response.json()


@patch("resume_customizer.api.endpoints.resumes.analyze_resume")
def test_analyze_resume_file_endpoint(
    mock_analyze_resume,
    client,
    mock_profile
):
    """Test the analyze resume file endpoint."""
    # Mock agent response
    mock_analyze_resume.return_value = mock_profile
    
    # Create a test file
    test_file_content = b"Test resume content"
    test_file = io.BytesIO(test_file_content)
    
    # Make request
    response = client.post(
        "/api/v1/resumes/analyze-file",
        files={"file": ("test_resume.txt", test_file, "text/plain")},
        data={"model_name": "test-model"}
    )
    
    # Assertions
    assert response.status_code == 200
    assert "profile" in response.json()
    assert response.json()["profile"]["core_identity"] == mock_profile.core_identity


@patch("resume_customizer.api.endpoints.resumes.customize_resume")
def test_customize_resume_file_endpoint(
    mock_customize_resume,
    client,
    test_job_description,
    mock_optimized_resume
):
    """Test the customize resume file endpoint."""
    # Mock agent response
    mock_customize_resume.return_value = mock_optimized_resume
    
    # Create a test file
    test_file_content = b"Test resume content"
    test_file = io.BytesIO(test_file_content)
    
    # Make request
    response = client.post(
        "/api/v1/resumes/customize-file",
        files={"resume_file": ("test_resume.txt", test_file, "text/plain")},
        data={
            "job_description": test_job_description,
            "model_name": "test-model"
        }
    )
    
    # Assertions
    assert response.status_code == 200
    assert "optimized_resume" in response.json()
    assert "# John Smith" in response.json()["optimized_resume"]["content"]
