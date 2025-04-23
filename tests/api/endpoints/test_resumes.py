"""Tests for the resume endpoints.

This module contains tests for the resume API endpoints.
"""

import io
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.resume import OptimizedResume, ResumeFormat, ResumeOptimizationSummary
from resume_customizer.api.endpoints.resumes import router
from resume_customizer.core.exceptions import AgentError, DocumentProcessingError


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router)
    
    # Mock dependencies
    app.dependency_overrides = {}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def mock_profiler():
    """Mock the analyze_resume function."""
    with patch('resume_customizer.api.endpoints.resumes.analyze_resume') as mock:
        # Create a mock profile
        profile = ProfessionalProfile(
            core_identity="Senior Software Engineer",
            technical_skills=["Python", "FastAPI", "AWS"],
            soft_skills=["Leadership", "Communication"],
            projects=[{"name": "API Development", "impact": "Improved performance by 50%"}],
            contribution_patterns="Focuses on scalable architecture",
            interests=["Cloud Computing", "Machine Learning"],
            work_style="Collaborative with independent execution"
        )
        mock.return_value = profile
        yield mock


@pytest.fixture
def mock_researcher():
    """Mock the analyze_job_description function."""
    with patch('resume_customizer.api.endpoints.resumes.analyze_job_description') as mock:
        # Create a mock job requirements
        requirements = JobRequirements(
            company_profile="Tech startup in fintech",
            core_requirements=["Python", "FastAPI", "AWS"],
            supplementary_attributes=["Docker", "Kubernetes"],
            hidden_expectations="Looking for self-motivated individuals",
            application_strategy="Emphasize cloud experience",
            keywords=["Python", "AWS", "API", "Cloud"]
        )
        mock.return_value = requirements
        yield mock


@pytest.fixture
def mock_strategist():
    """Mock the customize_resume function."""
    with patch('resume_customizer.api.endpoints.resumes.customize_resume') as mock:
        # Create a mock optimized resume
        optimized_resume = OptimizedResume(
            content="# John Doe\n\nSenior Software Engineer\n\n## Experience\n...",
            format=ResumeFormat.MARKDOWN,
            optimization_summary=ResumeOptimizationSummary(
                key_changes=["Added cloud experience"],
                alignment_points=["Matched Python skills"],
                ats_optimization=["Added keywords"]
            )
        )
        mock.return_value = optimized_resume
        yield mock


@pytest.fixture
def mock_document_processor():
    """Mock the DocumentProcessor class."""
    with patch('resume_customizer.api.endpoints.resumes.DocumentProcessor') as mock:
        # Set up mock methods
        mock.is_valid_file = AsyncMock(return_value=True)
        mock.save_file = AsyncMock(return_value="uploads/test_resume.pdf")
        mock.extract_text = AsyncMock(return_value="Sample resume content")
        yield mock


@pytest.fixture
def sample_resume_file():
    """Create a sample resume file for testing."""
    content = b"Sample resume content"
    return io.BytesIO(content)


class TestResumeEndpoints:
    """Test cases for the resume API endpoints."""
    
    def test_analyze_resume(self, client, mock_profiler):
        """Test the analyze resume endpoint."""
        # Setup
        mock_profiler.return_value = ProfessionalProfile(
            core_identity="Senior Software Engineer",
            technical_skills=["Python", "FastAPI", "AWS"],
            soft_skills=["Leadership", "Communication"],
            projects=[{"name": "API Development", "impact": "Improved performance by 50%"}],
            contribution_patterns="Focuses on scalable architecture",
            interests=["Cloud Computing", "Machine Learning"],
            work_style="Collaborative with independent execution"
        )
        
        # Send request
        response = client.post(
            "/resumes/analyze",
            data={"resume_content": "Sample resume content"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["core_identity"] == "Senior Software Engineer"
        assert "Python" in data["profile"]["technical_skills"]
        
        # Verify mock was called
        mock_profiler.assert_called_once()
    
    def test_analyze_resume_with_performance(self, client, mock_profiler):
        """Test the analyze resume endpoint with performance metrics."""
        # Send request
        response = client.post(
            "/resumes/analyze",
            data={
                "resume_content": "Sample resume content",
                "include_performance": True
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "performance" in data
        assert "elapsed_time" in data["performance"]
    
    @pytest.mark.asyncio
    async def test_analyze_resume_file(self, app, mock_profiler, mock_document_processor, sample_resume_file):
        """Test the analyze resume file endpoint."""
        # Setup file upload
        file = {"file": ("test_resume.pdf", sample_resume_file, "application/pdf")}
        form_data = {"model_name": "test-model", "include_performance": "false"}
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/resumes/analyze-file", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        
        # Verify mocks were called
        mock_document_processor.is_valid_file.assert_called_once()
        mock_document_processor.save_file.assert_called_once()
        mock_profiler.assert_called_once()
    
    def test_analyze_job(self, client, mock_researcher):
        """Test the analyze job endpoint."""
        # Send request
        response = client.post(
            "/resumes/analyze-job",
            data={"job_description": "Sample job description"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "requirements" in data
        assert "company_profile" in data["requirements"]
        
        # Verify mock was called
        mock_researcher.assert_called_once()
    
    def test_customize_resume(self, client, mock_strategist):
        """Test the customize resume endpoint."""
        # Send request
        response = client.post(
            "/resumes/customize",
            data={
                "resume_content": "Sample resume content",
                "job_description": "Sample job description"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "optimized_resume" in data
        assert data["optimized_resume"]["format"] == "markdown"
        
        # Verify mock was called
        mock_strategist.assert_called_once()
    
    def test_customize_resume_with_analysis(self, client, mock_strategist, mock_profiler, mock_researcher):
        """Test the customize resume endpoint with analysis."""
        # Send request
        response = client.post(
            "/resumes/customize",
            data={
                "resume_content": "Sample resume content",
                "job_description": "Sample job description",
                "include_analysis": "true"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "optimized_resume" in data
        assert "profile" in data
        assert "requirements" in data
        
        # Verify mocks were called
        mock_strategist.assert_called_once()
        mock_profiler.assert_called_once()
        mock_researcher.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_customize_resume_file(self, app, mock_strategist, mock_document_processor, sample_resume_file):
        """Test the customize resume file endpoint."""
        # Setup file upload
        file = {"resume_file": ("test_resume.pdf", sample_resume_file, "application/pdf")}
        form_data = {
            "job_description": "Sample job description",
            "model_name": "test-model",
            "include_performance": "true"
        }
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/resumes/customize-file", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "optimized_resume" in data
        assert "performance" in data
        
        # Verify mocks were called
        mock_document_processor.is_valid_file.assert_called_once()
        mock_document_processor.save_file.assert_called_once()
        mock_strategist.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_resume(self, app, mock_document_processor, sample_resume_file):
        """Test the upload resume endpoint."""
        # Setup file upload
        file = {"file": ("test_resume.pdf", sample_resume_file, "application/pdf")}
        form_data = {"extract_text": "true"}
        
        # Set up mock
        mock_document_processor.extract_text.return_value = "Sample extracted text"
        
        # Send request using AsyncClient
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/resumes/upload", files=file, data=form_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "file_id" in data
        assert "extract_count" in data
        
        # Verify mocks were called
        mock_document_processor.is_valid_file.assert_called_once()
        mock_document_processor.save_file.assert_called_once()
        mock_document_processor.extract_text.assert_called_once()
    
    def test_error_handling_validation(self, client, mock_document_processor):
        """Test error handling for validation errors."""
        # Setup mock
        mock_document_processor.is_valid_file.return_value = False
        
        # Send request with missing required field
        response = client.post("/resumes/analyze", data={})
        
        # Verify response
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_error_handling_document_error(self, client, mock_profiler):
        """Test error handling for document processing errors."""
        # Setup mock to raise an error
        mock_profiler.side_effect = DocumentProcessingError("Failed to process document")
        
        # Send request
        response = client.post(
            "/resumes/analyze",
            data={"resume_content": "Sample resume content"}
        )
        
        # Verify response
        assert response.status_code == 400  # Bad Request
        data = response.json()
        assert "Failed to process" in data["detail"]
    
    def test_error_handling_agent_error(self, client, mock_profiler):
        """Test error handling for agent errors."""
        # Setup mock to raise an error
        mock_profiler.side_effect = AgentError("Agent failed", "ProfilerAgent")
        
        # Send request
        response = client.post(
            "/resumes/analyze",
            data={"resume_content": "Sample resume content"}
        )
        
        # Verify response
        assert response.status_code == 500  # Internal Server Error
        data = response.json()
        assert "Failed to analyze" in data["detail"]
