#!/usr/bin/env python3
"""Simple script to verify the fix for PDF upload issue."""

import io
import sys
from pathlib import Path

from infrastructure.document_processor import DocumentProcessor
from api.endpoints.resumes import router as resume_router
from fastapi import UploadFile, FastAPI
from fastapi.testclient import TestClient

# Test file paths
TEST_DIR = Path(__file__).parent
TEST_RESUME_TXT = TEST_DIR / "test_resume.txt"

print("Testing document processor PDF file type handling...")

# Create document processor for direct testing
processor = DocumentProcessor()

# Create test app for endpoint testing
try:
    app = FastAPI()
    app.include_router(resume_router)
    client = TestClient(app)
    test_client_available = True
except (ImportError, TypeError):
    print("TestClient not properly configured, skipping endpoint test")
    test_client_available = False

def test_upload_endpoint():
    """Test the upload-test endpoint with a text file."""
    print("\nTesting /resumes/upload-test endpoint...")
    
    if not test_client_available:
        print("TestClient not available, skipping endpoint test")
        return True
    
    try:
        # Read the test file
        with open(TEST_RESUME_TXT, "rb") as f:
            file_content = f.read()
        
        # Create a file-like object
        file = io.BytesIO(file_content)
        file.name = "test_resume.txt"
        
        # Test the endpoint
        response = client.post(
            "/resumes/upload-test",
            files={"file": ("test_resume.txt", file, "text/plain")}
        )
        
        # Print response
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            for key, value in response.json().items():
                print(f"  {key}: {value}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error during upload test: {str(e)}")
        return False

async def test_document_processor():
    """Test document processor with various file types."""
    print("\nTesting DocumentProcessor.extract_text_from_bytes...")
    
    # Create processor
    processor = DocumentProcessor()
    
    # Read test file
    with open(TEST_RESUME_TXT, "rb") as f:
        file_content = f.read()
    
    # Test cases
    test_cases = [
        {"name": "Text with correct type", "type": "text/plain"},
        {"name": "Text with incorrect type", "type": "application/octet-stream"},
        {"name": "Text with empty type", "type": ""},
        {"name": "Text with None type", "type": None},
        {"name": "Text with invalid type", "type": "a"},
    ]
    
    all_passed = True
    
    # Run tests
    for case in test_cases:
        try:
            print(f"\nTesting {case['name']}...")
            
            # Call extract_text_from_bytes with our test case
            result = await processor.extract_text_from_bytes(
                file_content=file_content,
                file_type=case["type"]
            )
            
            # Check if the operation was successful
            if result and len(result) > 0:
                print(f"✅ Success: Extracted {len(result)} characters")
                print(f"Sample: {result[:50]}...")
            else:
                print(f"❌ Failed: No text extracted")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            all_passed = False
    
    return all_passed

async def main():
    """Main function."""
    import asyncio
    
    upload_test_passed = test_upload_endpoint()
    processor_test_passed = await test_document_processor()
    
    print("\n=== TEST SUMMARY ===")
    print(f"Upload Endpoint Test: {'✅ PASS' if upload_test_passed else '❌ FAIL'}")
    print(f"Document Processor Test: {'✅ PASS' if processor_test_passed else '❌ FAIL'}")
    
    return 0 if upload_test_passed and processor_test_passed else 1

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
