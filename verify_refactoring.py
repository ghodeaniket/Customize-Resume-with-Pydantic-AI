#!/usr/bin/env python3
"""
Verify that refactoring hasn't broken core functionality.

This script runs a simple test of the core functionality of the Resume Customizer.
"""
import asyncio
import os
import sys
from typing import Dict, Any

from agents.models.resume import CustomizationRequest, ResumeFormat
from infrastructure.ai_provider import AIProvider
from services.customizer import ResumeCustomizerService
from core.config import Settings
from agents.strategist import StrategistAgent
from agents.profiler import ProfilerAgent
from agents.researcher import ResearcherAgent
from infrastructure.document_processor import DocumentProcessor
from infrastructure.ai_provider import PromptManager


async def test_basic_functionality():
    """Test basic functionality of the Resume Customizer."""
    print("Testing Resume Customizer after refactoring...")
    
    # Create test resume and job description
    resume_content = """
    John Doe
    Software Engineer
    
    Experience:
    - Senior Software Engineer, XYZ Corp (2018-Present)
      * Developed and maintained backend APIs using Python
      * Implemented CI/CD pipelines
    
    Skills:
    - Python, JavaScript, TypeScript
    - AWS, Docker, Kubernetes
    - CI/CD, GitLab
    
    Education:
    - Bachelor of Science in Computer Science, University of Example (2014-2018)
    """
    
    job_description = """
    Software Engineer
    
    We are looking for a skilled Software Engineer to join our team. The ideal candidate
    should have experience with:
    
    - Python backend development
    - Cloud infrastructure (AWS preferred)
    - CI/CD pipelines
    - Knowledge of Docker and containerization
    """
    
    # Initialize services
    print("Initializing services...")
    prompt_manager = PromptManager()
    
    # Create agents
    profiler_agent = ProfilerAgent(prompt_manager)
    researcher_agent = ResearcherAgent(prompt_manager)
    strategist_agent = StrategistAgent(profiler_agent, researcher_agent, prompt_manager)
    
    # Create AI provider
    ai_provider = AIProvider("test")
    
    # Create document processor
    document_processor = DocumentProcessor()
    
    # Create service
    service = ResumeCustomizerService(strategist_agent, ai_provider, document_processor)
    
    # Create request
    request = CustomizationRequest(
        resume_content=resume_content,
        job_description=job_description,
        model_name="test",  # Use test model
        output_format=ResumeFormat.MARKDOWN,
        max_tokens=1000
    )
    
    try:
        # Process request
        print("Processing request...")
        response = await service.customize_resume(request)
        
        # Verify response
        if response.optimized_resume and response.optimized_resume.content:
            print("✅ Basic functionality test passed!")
        else:
            print("❌ Basic functionality test failed: No optimized resume content")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Basic functionality test failed with error: {str(e)}")
        raise e


async def test_file_processing():
    """Test file processing functionality."""
    print("\nTesting file processing functionality...")
    
    # Create test PDF content
    pdf_path = os.path.join(os.getcwd(), "tests", "test_files", "test_resume.pdf")
    
    if not os.path.exists(pdf_path):
        print(f"❓ Test file not found: {pdf_path}")
        print("Skipping file processing test.")
        return
    
    # Read test file
    try:
        with open(pdf_path, "rb") as f:
            file_content = f.read()
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Process file
        print("Processing file...")
        text = await processor.extract_text_from_bytes(file_content, "application/pdf", "test_resume.pdf")
        
        # Verify result
        if text and len(text) > 0:
            print("✅ File processing test passed!")
        else:
            print("❌ File processing test failed: No text extracted")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ File processing test failed with error: {str(e)}")
        raise e


async def main():
    """Run verification tests."""
    try:
        await test_basic_functionality()
        await test_file_processing()
        
        print("\n✅ All verification tests passed!")
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
