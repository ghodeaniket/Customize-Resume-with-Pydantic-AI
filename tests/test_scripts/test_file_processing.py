#!/usr/bin/env python3
"""
Test Script for File Processing

This script tests the refactored file processing functionality of the Resume Customizer
by making requests to the API endpoints that handle file uploads and extraction.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
import logging
import httpx
from typing import Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/test_file_processing.log")
    ]
)

logger = logging.getLogger("file_processing_test")

# Constants
API_BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
TEST_TIMEOUT = 20  # seconds

# Path to test files
TEST_DIR = Path(__file__).parent / "tests" / "files"


async def test_health_check() -> bool:
    """Test the health check endpoint.
    
    Returns:
        bool: True if test passes, False otherwise
    """
    logger.info("Testing health check endpoint")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/health")
            resp.raise_for_status()
            data = resp.json()
            
            logger.info(f"Health check successful: API version {data.get('api', {}).get('version', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False


async def test_upload_endpoint(file_path: Path) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Test the file upload endpoint.
    
    Args:
        file_path: Path to the file to upload
        
    Returns:
        tuple: (success, response_data)
    """
    logger.info(f"Testing file upload endpoint with file: {file_path.name}")
    
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False, None
    
    async with httpx.AsyncClient() as client:
        try:
            with open(file_path, "rb") as file:
                files = {"file": (file_path.name, file, "application/octet-stream")}
                resp = await client.post(
                    f"{API_BASE_URL}{API_PREFIX}/resumes/upload-test",
                    files=files,
                    timeout=TEST_TIMEOUT
                )
            
            resp.raise_for_status()
            data = resp.json()
            
            logger.info(
                f"File upload successful: {data.get('data', {}).get('filename')} "
                f"({data.get('data', {}).get('size', 0)} bytes) "
                f"detected as {data.get('data', {}).get('detected_type', 'unknown')}"
            )
            
            return True, data
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return False, None


async def test_file_extraction(file_path: Path) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Test the file extraction functionality.
    
    Args:
        file_path: Path to the file to upload
        
    Returns:
        tuple: (success, response_data)
    """
    logger.info(f"Testing file extraction with file: {file_path.name}")
    
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False, None
    
    async with httpx.AsyncClient() as client:
        try:
            with open(file_path, "rb") as file:
                files = {"resume_file": (file_path.name, file, "application/octet-stream")}
                resp = await client.post(
                    f"{API_BASE_URL}{API_PREFIX}/resumes/customize-upload",
                    files=files,
                    data={
                        "job_description": "This is a test job description for a Python developer.",
                        "output_format": "text"
                    },
                    timeout=TEST_TIMEOUT
                )
            
            resp.raise_for_status()
            data = resp.json()
            
            # Check if we have optimized resume content
            if "data" in data and "optimized_resume" in data["data"]:
                content_length = len(data["data"]["optimized_resume"].get("content", ""))
                logger.info(f"File extraction successful: {content_length} characters extracted")
                return True, data
            else:
                logger.error("File extraction failed: No optimized resume content in response")
                return False, data
        except Exception as e:
            logger.error(f"File extraction failed: {str(e)}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response: {e.response.text}")
            return False, None


async def run_tests() -> int:
    """Run the file processing tests.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting file processing tests")
    
    # Test health check
    health_ok = await test_health_check()
    if not health_ok:
        logger.error("Health check failed, skipping other tests")
        return 1
    
    # Create test directory if it doesn't exist
    if not TEST_DIR.exists():
        logger.info(f"Creating test directory: {TEST_DIR}")
        TEST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create sample test files if they don't exist
    sample_txt_path = TEST_DIR / "sample_resume.txt"
    if not sample_txt_path.exists():
        logger.info(f"Creating sample text file: {sample_txt_path}")
        with open(sample_txt_path, "w") as f:
            f.write("""
John Doe
Software Engineer

Contact:
john.doe@example.com
(123) 456-7890

Experience:
- Senior Software Engineer, XYZ Corp (2018-Present)
  * Developed and maintained Python applications
  * Implemented CI/CD pipelines
  * Improved system performance by 30%

- Software Engineer, ABC Inc (2015-2018)
  * Built REST APIs using FastAPI
  * Designed database schemas
  * Mentored junior developers

Education:
- BS in Computer Science, University of Technology (2015)

Skills:
- Python, JavaScript, SQL
- FastAPI, Django, React
- Docker, Kubernetes, AWS
            """)
    
    # Get all test files
    test_files = list(TEST_DIR.glob("*"))
    if not test_files:
        logger.warning("No test files found")
        test_files = [sample_txt_path]
    
    # Run file upload tests
    upload_results = []
    for file_path in test_files:
        success, data = await test_upload_endpoint(file_path)
        upload_results.append((file_path.name, success))
    
    # Run file extraction tests
    extraction_results = []
    for file_path in test_files:
        success, data = await test_file_extraction(file_path)
        extraction_results.append((file_path.name, success))
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    logger.info("\nFile Upload Tests:")
    for filename, success in upload_results:
        logger.info(f"- {filename}: {'✅ PASS' if success else '❌ FAIL'}")
    
    logger.info("\nFile Extraction Tests:")
    for filename, success in extraction_results:
        logger.info(f"- {filename}: {'✅ PASS' if success else '❌ FAIL'}")
    
    # Overall result
    all_passed = all(success for _, success in upload_results + extraction_results)
    logger.info("\nOverall Result: " + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run_tests()))
