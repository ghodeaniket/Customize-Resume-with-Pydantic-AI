"""Integration test for the Resume Customizer application.

This module tests the full flow of the Resume Customizer application
from file upload to resume customization.
"""

import io
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from resume_customizer.agents.models.profile import ProfessionalProfile
from resume_customizer.agents.models.job import JobRequirements
from resume_customizer.agents.models.resume import OptimizedResume
from resume_customizer.core.exceptions import DocumentProcessingError
from resume_customizer.main import app
from resume_customizer.services.document.processor import DocumentProcessor


class MockUploadFile:
    """Mock UploadFile class for testing."""
    
    def __init__(self, filename, content, content_type="text/plain"):
        """Initialize the mock file."""
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = content_type
    
    async def read(self):
        """Read the file content."""
        return self.file.getvalue()
    
    async def seek(self, position):
        """Seek to a position in the file."""
        self.file.seek(position)


@pytest.mark.asyncio
async def test_full_resume_customization_flow():
    """Test the full flow of resume customization from file upload to customization."""
    # Sample data
    sample_resume_content = b"""
    JOHN DOE
    Software Engineer
    
    CONTACT
    Email: john.doe@example.com
    Phone: (555) 123-4567
    LinkedIn: linkedin.com/in/johndoe
    
    SUMMARY
    Experienced software engineer with a passion for building scalable applications.
    5+ years of experience in full-stack development with expertise in Python and JavaScript.
    
    EXPERIENCE
    Senior Software Engineer
    ABC Tech, 2018-Present
    - Led development of microservices architecture
    - Implemented CI/CD pipeline reducing deployment time by 40%
    - Mentored junior developers
    
    Software Engineer
    XYZ Solutions, 2015-2018
    - Developed REST APIs using Python and Flask
    - Collaborated with cross-functional teams
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology, 2015
    GPA: 3.8/4.0
    """
    
    sample_job_description = """
    Senior Backend Engineer
    
    About Us:
    TechInnovate is a leading technology company specializing in cloud-based solutions.
    
    Responsibilities:
    - Design and develop scalable backend systems
    - Collaborate with cross-functional teams
    - Write clean, maintainable, and efficient code
    - Troubleshoot and resolve complex technical issues
    - Participate in code reviews
    
    Requirements:
    - 5+ years of experience in backend development
    - Proficiency in Python, Django/Flask
    - Experience with RESTful APIs
    - Knowledge of SQL and NoSQL databases
    - Understanding of cloud platforms (AWS/GCP)
    - Excellent problem-solving skills
    
    Nice to Have:
    - Experience with microservices architecture
    - Knowledge of CI/CD pipelines
    - Familiarity with Docker and Kubernetes
    
    Benefits:
    - Competitive salary
    - Health insurance
    - Flexible working hours
    - Professional development budget
    - 401(k) matching
    
    Location: Remote (US time zones preferred)
    """
    
    # Mock data for each step
    mock_profile = ProfessionalProfile(
        core_identity="Software Engineer with backend expertise",
        technical_skills=["Python", "Flask", "REST APIs", "Microservices"],
        soft_skills=["Leadership", "Mentoring", "Collaboration"],
        work_experience=[],
        projects=[],
        education=[],
        contribution_patterns="Focuses on scalable architecture and efficient systems",
        interests=["Backend Development", "Cloud Computing"],
        work_style="Collaborative with strong independent execution",
        career_highlights=[]
    )
    
    mock_requirements = JobRequirements(
        company_profile="TechInnovate: Cloud-based solutions provider",
        position={
            "title": "Senior Backend Engineer",
            "responsibilities": ["Design scalable systems", "Write clean code"]
        },
        core_requirements=["Python", "Django/Flask", "RESTful APIs", "SQL/NoSQL"],
        supplementary_attributes=["Microservices", "CI/CD", "Docker"],
        hidden_expectations="Problem solver who can work independently",
        application_strategy="Emphasize backend experience and scalable solutions",
        keywords=["Python", "Backend", "Scalable", "APIs", "Cloud"]
    )
    
    mock_optimized_resume = OptimizedResume(
        content="# John Doe\n\n**Senior Backend Engineer**\n\n## Contact\n...",
        format="markdown",
        optimization_summary={
            "key_changes": ["Emphasized backend experience", "Added cloud keywords"],
            "alignment_points": ["Highlighted Python and API experience"],
            "ats_optimization": ["Added key technical terms"]
        }
    )
    
    # 1. Test file upload
    with patch('resume_customizer.services.document.processor.DocumentProcessor.save_file',
              AsyncMock(return_value=Path("/uploads/test_resume.txt"))), \
         patch('resume_customizer.services.document.processor.DocumentProcessor.extract_text',
              AsyncMock(return_value=sample_resume_content.decode('utf-8'))), \
         patch('resume_customizer.services.document.processor.DocumentProcessor.is_valid_file',
              AsyncMock(return_value=True)):
        
        # Create a mock file
        mock_file = MockUploadFile("resume.txt", sample_resume_content)
        
        # Test file text extraction
        extracted_text = await DocumentProcessor.extract_text(mock_file)
        assert isinstance(extracted_text, str)
        assert len(extracted_text) > 0
        assert "JOHN DOE" in extracted_text
    
    # 2. Test resume analysis
    with patch('resume_customizer.agents.profiler.profiler_agent.run',
              AsyncMock(return_value=MagicMock(output=mock_profile))):
        
        from resume_customizer.agents.profiler import analyze_resume
        
        # Test profile generation
        profile = await analyze_resume(
            resume_content=sample_resume_content.decode('utf-8'),
            http_client=httpx.AsyncClient()
        )
        
        assert isinstance(profile, ProfessionalProfile)
        assert profile.core_identity == mock_profile.core_identity
        assert "Python" in profile.technical_skills
    
    # 3. Test job description analysis
    with patch('resume_customizer.agents.researcher.researcher_agent.run',
              AsyncMock(return_value=MagicMock(output=mock_requirements))):
        
        from resume_customizer.agents.researcher import analyze_job_description
        
        # Test job requirements extraction
        requirements = await analyze_job_description(
            job_description=sample_job_description,
            http_client=httpx.AsyncClient()
        )
        
        assert isinstance(requirements, JobRequirements)
        assert requirements.company_profile == mock_requirements.company_profile
        assert "Python" in requirements.core_requirements
    
    # 4. Test resume customization
    with patch('resume_customizer.agents.strategist.strategist_agent.run',
              AsyncMock(return_value=MagicMock(output=mock_optimized_resume.content))), \
         patch('resume_customizer.agents.profiler.analyze_resume',
              AsyncMock(return_value=mock_profile)), \
         patch('resume_customizer.agents.researcher.analyze_job_description',
              AsyncMock(return_value=mock_requirements)), \
         patch('resume_customizer.agents.strategist.get_job_insights',
              AsyncMock(return_value=mock_requirements)), \
         patch('resume_customizer.agents.strategist.get_resume_insights',
              AsyncMock(return_value=mock_profile)):
        
        from resume_customizer.agents.strategist import customize_resume
        
        # Test resume customization
        optimized_resume = await customize_resume(
            resume_content=sample_resume_content.decode('utf-8'),
            job_description=sample_job_description,
            http_client=httpx.AsyncClient()
        )
        
        assert isinstance(optimized_resume, OptimizedResume)
        assert "John Doe" in optimized_resume.content
        assert optimized_resume.format == "markdown"


@pytest.mark.asyncio
async def test_error_handling_for_invalid_files():
    """Test error handling for invalid files."""
    # Test empty file
    with pytest.raises(DocumentProcessingError):
        mock_empty_file = MockUploadFile("empty.txt", b"")
        await DocumentProcessor.extract_text(mock_empty_file)
    
    # Test malformed PDF
    with patch('resume_customizer.services.document.processor.DocumentProcessor.extract_text_from_pdf',
              AsyncMock(side_effect=DocumentProcessingError("Failed to parse PDF", "PDF"))):
        
        mock_pdf_file = MockUploadFile("malformed.pdf", b"%PDF-1.7\nInvalid PDF content", "application/pdf")
        
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.extract_text(mock_pdf_file)
    
    # Test oversized file
    with patch('resume_customizer.core.config.settings.MAX_UPLOAD_SIZE', 100):
        large_content = b"x" * 200  # 200 bytes
        mock_large_file = MockUploadFile("large.txt", large_content)
        
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.is_valid_file(mock_large_file)


@pytest.mark.asyncio
async def test_boundary_conditions():
    """Test boundary conditions for file processing."""
    # Test file exactly at size limit
    with patch('resume_customizer.core.config.settings.MAX_UPLOAD_SIZE', 100):
        # File exactly at size limit (100 bytes)
        exact_size_content = b"x" * 100
        mock_exact_file = MockUploadFile("exact.txt", exact_size_content)
        
        # Should pass validation
        assert await DocumentProcessor.is_valid_file(mock_exact_file)
        
        # File 1 byte over limit
        slightly_over_content = b"x" * 101
        mock_over_file = MockUploadFile("over.txt", slightly_over_content)
        
        # Should fail validation
        assert not await DocumentProcessor.is_valid_file(mock_over_file)
    
    # Test different content types
    content_types = {
        "text/plain": ".txt",
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"
    }
    
    # Make sure all supported content types are properly detected
    for content_type, extension in content_types.items():
        mock_file = MockUploadFile(f"test{extension}", b"test content", content_type)
        from resume_customizer.services.document.processor import DocumentFormat
        
        format_type = DocumentProcessor.get_format(mock_file)
        assert format_type != DocumentFormat.UNKNOWN
    
    # Test unsupported content type
    unsupported_file = MockUploadFile("image.jpg", b"image data", "image/jpeg")
    from resume_customizer.services.document.processor import DocumentFormat
    
    format_type = DocumentProcessor.get_format(unsupported_file)
    assert format_type == DocumentFormat.UNKNOWN
