"""End-to-end tests for the Resume Customizer application."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from agents.models.resume import ResumeFormat
from infrastructure.ai_provider import AIProvider, PromptManager, ResumeCustomizerDeps
from infrastructure.init_prompts import init_prompt_manager
from main import app


@pytest.fixture
def initialized_app() -> TestClient:
    """Get initialized test client.
    
    Returns:
        TestClient: Initialized test client
    """
    # Initialize prompt manager
    init_prompt_manager()
    
    # Get test client
    return TestClient(app)


def test_health_check(initialized_app: TestClient) -> None:
    """Test health check endpoint.
    
    Args:
        initialized_app: Initialized test client
    """
    # Make request to health check endpoint
    response = initialized_app.get("/health")
    
    # Check response status code
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data
    assert isinstance(data["uptime"], float)


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY environment variable not set"
)
def test_customize_resume_integration(initialized_app: TestClient) -> None:
    """Test the complete resume customization flow.
    
    This test is skipped if the OPENROUTER_API_KEY environment variable is not set.
    When running, it will make real API calls to OpenRouter.
    
    Args:
        initialized_app: Initialized test client
    """
    # Sample resume and job description
    resume_content = """
    Jane Smith
    Software Engineer
    
    Summary:
    Experienced software engineer with 5 years of experience in full-stack development.
    Proficient in Python, JavaScript, and cloud technologies.
    
    Experience:
    Senior Software Engineer, ABC Tech (2020-Present)
    - Led development of a microservices architecture using FastAPI and React
    - Improved system performance by 40% through optimizations
    - Mentored junior developers and conducted code reviews
    
    Software Engineer, XYZ Solutions (2018-2020)
    - Developed RESTful APIs using Django and PostgreSQL
    - Implemented CI/CD pipelines with Jenkins and Docker
    
    Education:
    Bachelor of Science in Computer Science, University of Technology (2018)
    
    Skills:
    - Python, JavaScript, TypeScript
    - React, Angular, Vue.js
    - FastAPI, Django, Flask
    - PostgreSQL, MongoDB
    - AWS, Docker, Kubernetes
    """
    
    job_description = """
    Senior Software Engineer - Backend
    
    About the Role:
    We are looking for a Senior Software Engineer to join our backend team.
    In this role, you will design and implement high-performance APIs and microservices
    using Python and FastAPI. You will work closely with frontend developers and
    data scientists to build scalable and maintainable systems.
    
    Requirements:
    - 5+ years of experience in backend development
    - Strong proficiency in Python
    - Experience with FastAPI or similar frameworks (Django, Flask)
    - Solid understanding of RESTful API design
    - Experience with PostgreSQL and database optimization
    - Familiarity with containerization (Docker) and orchestration (Kubernetes)
    - Experience with cloud platforms (preferably AWS)
    
    Nice to Have:
    - Experience with real-time data processing
    - Knowledge of machine learning frameworks
    - Experience with GraphQL
    - Open-source contributions
    
    What We Offer:
    - Competitive salary and benefits
    - Remote-first work environment
    - Professional development opportunities
    - Collaborative and innovative team culture
    """
    
    # Create request data
    request_data = {
        "resume_content": resume_content,
        "job_description": job_description,
        "model_name": "deepseek/deepseek-r1-distill-llama-70b",
        "output_format": "markdown",
        "max_tokens": 3000
    }
    
    # Make request to customize resume endpoint
    response = initialized_app.post("/resumes/customize", json=request_data)
    
    # Check response status code
    assert response.status_code == 200
    
    # Check response data
    data = response.json()
    assert "optimized_resume" in data
    assert "content" in data["optimized_resume"]
    assert "format" in data["optimized_resume"]
    assert "optimizations" in data["optimized_resume"]
    assert "keywords_included" in data["optimized_resume"]
    
    # Check that usage stats are included
    assert "usage_stats" in data
    assert "total_tokens" in data["usage_stats"]


def test_customize_resume_with_mocks(initialized_app: TestClient) -> None:
    """Test the resume customization flow with mocked dependencies.
    
    Args:
        initialized_app: Initialized test client
    """
    # Sample resume and job description
    resume_content = "Sample resume content"
    job_description = "Sample job description"
    
    # Create request data
    request_data = {
        "resume_content": resume_content,
        "job_description": job_description,
        "model_name": "test-model",
        "output_format": "markdown",
        "max_tokens": 1000
    }
    
    # Mock ResumeCustomizerService.customize_resume method
    with patch("services.customizer.ResumeCustomizerService.customize_resume") as mock_customize:
        # Create mock response
        mock_response = MagicMock()
        mock_response.optimized_resume = MagicMock()
        mock_response.optimized_resume.content = "# Optimized Resume\n\n..."
        mock_response.optimized_resume.format = ResumeFormat.MARKDOWN
        mock_response.optimized_resume.optimizations = ["Optimization 1", "Optimization 2"]
        mock_response.optimized_resume.keywords_included = ["Python", "FastAPI"]
        mock_response.optimized_resume.ats_score = 95.0
        mock_response.usage_stats = {"total_tokens": 1000}
        
        # Configure mock
        mock_customize.return_value = mock_response
        
        # Make request to customize resume endpoint
        response = initialized_app.post("/resumes/customize", json=request_data)
        
        # Check response status code
        assert response.status_code == 200
        
        # Check that the service was called with the right arguments
        mock_customize.assert_called_once()
        args = mock_customize.call_args[0][0]
        assert args.resume_content == resume_content
        assert args.job_description == job_description
        assert args.model_name == "test-model"
        assert args.output_format == ResumeFormat.MARKDOWN
        assert args.max_tokens == 1000
