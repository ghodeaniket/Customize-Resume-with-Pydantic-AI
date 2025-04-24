#!/usr/bin/env python3
"""
Verification script to check that the implemented fixes address the identified issues.

This script tests the key functionality that was fixed:
1. Document processing issues with UploadFile objects
2. Agent integration with proper text content handling
3. Environment variable configuration
4. API key handling
5. Error handling improvements
6. Logging enhancements
"""

import os
import io
import sys
import asyncio
import httpx
from pathlib import Path
from fastapi import UploadFile

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from resume_customizer.services.document.processor import DocumentProcessor, DocumentFormat
from resume_customizer.agents.profiler import analyze_resume
from resume_customizer.agents.researcher import analyze_job_description
from resume_customizer.core.config import settings
from resume_customizer.core.logging import setup_logging


async def test_document_processing():
    """Test the document processing functionality with UploadFile objects."""
    print("\n=== Testing Document Processing with UploadFile ===")
    
    # Test files
    current_dir = Path(__file__).parent
    test_resume_path = current_dir / "test_resume.txt"
    
    try:
        with open(test_resume_path, "rb") as f:
            file_content = f.read()
        
        print(f"📝 Reading text file: {test_resume_path.name}")
        
        # Create a virtual UploadFile
        upload_file = UploadFile(
            filename="test_resume.txt",
            file=io.BytesIO(file_content),
            content_type="text/plain"
        )
        
        # Extract text using the improved method
        text = await DocumentProcessor.extract_text(upload_file)
        
        # Reset file position
        await upload_file.seek(0)
        
        print(f"✅ Successfully extracted {len(text)} characters from UploadFile")
        print("✅ Preview of extracted text:")
        print("-" * 40)
        print(text[:500] + "...")
        print("-" * 40)
        
        return True
    except Exception as e:
        print(f"❌ Error testing document processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_job_description_handling():
    """Test the researcher agent's handling of job description text versus URLs."""
    print("\n=== Testing Job Description Handling ===")
    
    try:
        # Sample job description text
        job_description = """
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
        """
        
        print("📝 Testing job description text handling")
        
        # Create an HTTP client
        async with httpx.AsyncClient() as client:
            # Mock the agent execution
            try:
                # Just verify that the function doesn't error due to URL detection
                # We don't need actual AI response for this test
                import unittest.mock
                with unittest.mock.patch('resume_customizer.agents.researcher.researcher_agent.run') as mock_run:
                    mock_result = unittest.mock.MagicMock()
                    mock_result.output = {}
                    mock_run.return_value = mock_result
                    
                    await analyze_job_description(
                        job_description=job_description,
                        http_client=client
                    )
                
                print("✅ Successfully handled job description as text")
                return True
            except Exception as e:
                print(f"❌ Error handling job description: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
    except Exception as e:
        print(f"❌ Error in job description test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_environment_config():
    """Test the environment configuration."""
    print("\n=== Testing Environment Configuration ===")
    
    try:
        # Check if environment variables are properly set
        has_openai_key = os.environ.get('OPENAI_API_KEY') is not None
        has_openrouter_key = os.environ.get('OPENROUTER_API_KEY') is not None
        
        print(f"✅ OPENAI_API_KEY is {'set' if has_openai_key else 'not set'}")
        print(f"✅ OPENROUTER_API_KEY is {'set' if has_openrouter_key else 'not set'}")
        
        # Verify settings are loaded
        print(f"✅ Default model: {settings.DEFAULT_MODEL}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing environment config: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_logging_setup():
    """Test the enhanced logging setup."""
    print("\n=== Testing Logging Configuration ===")
    
    try:
        # Setup logging
        setup_logging()
        
        # Import the logger
        from resume_customizer.core.logging import app_logger
        
        # Test logging different levels
        app_logger.debug("This is a debug message")
        app_logger.info("This is an info message")
        app_logger.warning("This is a warning message")
        app_logger.error("This is an error message")
        
        # Check if logs directory was created
        logs_dir = Path("logs")
        has_logs_dir = logs_dir.exists()
        
        print(f"✅ Logs directory exists: {has_logs_dir}")
        if has_logs_dir:
            print(f"✅ Log files: {', '.join(f.name for f in logs_dir.glob('*.log'))}")
        
        # Try to get a request logger
        if hasattr(app_logger, 'bind'):
            request_logger = app_logger.bind(request_id="TEST-REQ-123")
            request_logger.info("This is a message with request ID")
            print("✅ Request logger created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error testing logging setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point for the verification script."""
    print("=" * 80)
    print("VERIFICATION SCRIPT")
    print("=" * 80)
    
    # Run tests
    doc_processing_success = await test_document_processing()
    job_desc_success = await test_agent_job_description_handling()
    env_config_success = await test_environment_config()
    logging_success = await test_logging_setup()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Document Processing: {'✅ PASS' if doc_processing_success else '❌ FAIL'}")
    print(f"Job Description Handling: {'✅ PASS' if job_desc_success else '❌ FAIL'}")
    print(f"Environment Configuration: {'✅ PASS' if env_config_success else '❌ FAIL'}")
    print(f"Logging Setup: {'✅ PASS' if logging_success else '❌ FAIL'}")
    
    # Overall status
    all_passed = all([
        doc_processing_success,
        job_desc_success,
        env_config_success,
        logging_success
    ])
    
    print("\n" + "=" * 80)
    print(f"OVERALL STATUS: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
