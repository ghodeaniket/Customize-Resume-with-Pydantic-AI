#!/usr/bin/env python3
"""
Test script for Resume Customizer API endpoints.

This script tests the basic functionality of the Resume Customizer API
by making requests to the key endpoints.
"""

import os
import sys
import time
import json
import httpx
import asyncio
from pathlib import Path

# Constants
API_BASE_URL = "http://localhost:8000"
API_KEY = "sk-or-dummy-key-for-testing"  # This matches the dummy key in .env
TEST_TIMEOUT = 60  # seconds

# Test files
CURRENT_DIR = Path(__file__).parent
TEST_RESUME_PATH = CURRENT_DIR / "test_resume.txt"
TEST_JOB_DESCRIPTION_PATH = CURRENT_DIR / "test_job_description.txt"


# Test functions
async def test_health_endpoint():
    """Test the basic health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/health")
            resp.raise_for_status()
            data = resp.json()
            
            print(f"✅ Health Check: {data}")
            return True
        except Exception as e:
            print(f"❌ Error testing health endpoint: {str(e)}")
            return False


async def test_detailed_health_endpoint():
    """Test the detailed health endpoint."""
    print("\n=== Testing Detailed Health Endpoint ===")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}/health/detail",
                headers={"X-API-Key": API_KEY}
            )
            resp.raise_for_status()
            data = resp.json()
            
            # Pretty print some key information
            print(f"✅ API Version: {data.get('version')}")
            print(f"✅ Environment: {data.get('environment')}")
            print(f"✅ Debug Mode: {data.get('settings', {}).get('debug')}")
            print(f"✅ Cache Enabled: {data.get('settings', {}).get('enable_cache')}")
            
            return True
        except Exception as e:
            print(f"❌ Error testing detailed health endpoint: {str(e)}")
            return False


async def test_metrics_endpoint():
    """Test the metrics endpoint."""
    print("\n=== Testing Metrics Endpoint ===")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/metrics",
                headers={"X-API-Key": API_KEY}
            )
            resp.raise_for_status()
            data = resp.json()
            
            print(f"✅ Metrics retrieved: {json.dumps(data, indent=2)[:500]}...")
            return True
        except Exception as e:
            print(f"❌ Error testing metrics endpoint: {str(e)}")
            return False


async def test_resume_customization_endpoint():
    """Test the basic resume customization endpoint."""
    print("\n=== Testing Resume Customization Endpoint ===")
    
    # Read test files
    try:
        with open(TEST_RESUME_PATH, "r") as f:
            resume_content = f.read()
        
        with open(TEST_JOB_DESCRIPTION_PATH, "r") as f:
            job_description = f.read()
    except Exception as e:
        print(f"❌ Error reading test files: {str(e)}")
        return False
    
    # Make API request
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=TEST_TIMEOUT)) as client:
        try:
            print("📝 Sending resume and job description for customization...")
            start_time = time.time()
            
            resp = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/resumes/customize",
                headers={"X-API-Key": API_KEY},
                data={
                    "resume_content": resume_content,
                    "job_description": job_description,
                    "include_performance": "true"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            elapsed_time = time.time() - start_time
            
            print(f"✅ Resume customization completed in {elapsed_time:.2f}s")
            
            # Print performance metrics if available
            if "performance" in data:
                print(f"✅ Performance Metrics:")
                print(f"  - Elapsed Time: {data['performance']['elapsed_time']:.2f}s")
                print(f"  - Operation: {data['performance']['operation']}")
                print(f"  - Cache Hit: {data['performance']['cache_hit']}")
            
            # Print a preview of the optimized resume
            if "optimized_resume" in data:
                print("\n✅ Optimized Resume Preview:")
                print("-" * 40)
                print(data["optimized_resume"][:500] + "...")
                print("-" * 40)
            
            return True
        except Exception as e:
            print(f"❌ Error testing resume customization endpoint: {str(e)}")
            return False


async def test_file_upload_endpoint():
    """Test the file upload endpoint."""
    print("\n=== Testing File Upload Endpoint ===")
    
    # Prepare the file
    try:
        resume_file = open(TEST_RESUME_PATH, "rb")
    except Exception as e:
        print(f"❌ Error opening test resume file: {str(e)}")
        return False
    
    # Make API request
    async with httpx.AsyncClient() as client:
        try:
            files = {"file": (os.path.basename(TEST_RESUME_PATH), resume_file, "text/plain")}
            resp = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/resumes/upload",
                headers={"X-API-Key": API_KEY},
                files=files,
                data={"extract_text": "true"}
            )
            resp.raise_for_status()
            data = resp.json()
            
            print(f"✅ File Upload Results:")
            print(f"  - Filename: {data.get('filename')}")
            print(f"  - File ID: {data.get('file_id')}")
            print(f"  - File Type: {data.get('file_type')}")
            print(f"  - File Size: {data.get('file_size')} bytes")
            
            if "extract_count" in data:
                print(f"  - Extracted {data.get('extract_count')} characters of text")
            
            return True
        except Exception as e:
            print(f"❌ Error testing file upload endpoint: {str(e)}")
            return False
        finally:
            resume_file.close()


async def test_resume_file_customization_endpoint():
    """Test the resume file customization endpoint."""
    print("\n=== Testing Resume File Customization Endpoint ===")
    
    # Prepare the file and job description
    try:
        resume_file = open(TEST_RESUME_PATH, "rb")
        
        with open(TEST_JOB_DESCRIPTION_PATH, "r") as f:
            job_description = f.read()
    except Exception as e:
        print(f"❌ Error opening test files: {str(e)}")
        return False
    
    # Make API request
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=TEST_TIMEOUT)) as client:
        try:
            print("📝 Sending resume file and job description for customization...")
            start_time = time.time()
            
            files = {"resume_file": (os.path.basename(TEST_RESUME_PATH), resume_file, "text/plain")}
            resp = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/resumes/customize-file",
                headers={"X-API-Key": API_KEY},
                files=files,
                data={
                    "job_description": job_description,
                    "include_performance": "true"
                }
            )
            resp.raise_for_status()
            data = resp.json()
            
            elapsed_time = time.time() - start_time
            
            print(f"✅ Resume file customization completed in {elapsed_time:.2f}s")
            
            # Print performance metrics if available
            if "performance" in data:
                print(f"✅ Performance Metrics:")
                print(f"  - Elapsed Time: {data['performance']['elapsed_time']:.2f}s")
                print(f"  - Operation: {data['performance']['operation']}")
                print(f"  - Cache Hit: {data['performance']['cache_hit']}")
            
            # Print a preview of the optimized resume
            if "optimized_resume" in data:
                print("\n✅ Optimized Resume Preview:")
                print("-" * 40)
                print(data["optimized_resume"][:500] + "...")
                print("-" * 40)
            
            return True
        except Exception as e:
            print(f"❌ Error testing resume file customization endpoint: {str(e)}")
            return False
        finally:
            resume_file.close()


# Main function
async def main():
    print("=" * 80)
    print("RESUME CUSTOMIZER API TEST SCRIPT")
    print("=" * 80)
    
    # Determine API prefix
    global API_V1_PREFIX
    API_V1_PREFIX = "/api/v1"
    
    # Run tests
    health_ok = await test_health_endpoint()
    
    if health_ok:
        # Only run other tests if health check passes
        detailed_health_ok = await test_detailed_health_endpoint()
        metrics_ok = await test_metrics_endpoint()
        customization_ok = await test_resume_customization_endpoint()
        upload_ok = await test_file_upload_endpoint()
        file_customization_ok = await test_resume_file_customization_endpoint()
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"Detailed Health: {'✅ PASS' if detailed_health_ok else '❌ FAIL'}")
        print(f"Metrics: {'✅ PASS' if metrics_ok else '❌ FAIL'}")
        print(f"Resume Customization: {'✅ PASS' if customization_ok else '❌ FAIL'}")
        print(f"File Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
        print(f"File Customization: {'✅ PASS' if file_customization_ok else '❌ FAIL'}")
        
        # Overall result
        all_passed = all([
            health_ok, 
            detailed_health_ok, 
            metrics_ok, 
            customization_ok, 
            upload_ok, 
            file_customization_ok
        ])
        
        print("\nOverall Result:", "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED")
        return 0 if all_passed else 1
    else:
        print("\n❌ Health check failed, skipping other tests")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
