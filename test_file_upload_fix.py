#!/usr/bin/env python3
"""
Test script to verify the fix for the file upload issue.

This script tests the document processor's ability to handle different file types,
especially PDFs, and verifies that the file type detection and parameter handling
are working correctly.
"""

import asyncio
import io
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import UploadFile
from infrastructure.document_processor import DocumentProcessor
from agents.profiler import ProfilerAgent
from agents.models.profile import ProfessionalProfile
from infrastructure.ai_provider import PromptManager, ResumeCustomizerDeps


# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


async def test_document_processor_file_type_handling():
    """Test the document processor's handling of different file types and parameters."""
    print(f"\n{YELLOW}=== Testing Document Processor File Type Handling ==={RESET}")
    
    # Create document processor
    processor = DocumentProcessor()
    
    # Test cases with different file types and parameters
    test_cases = [
        # Valid cases
        {"name": "Valid PDF", "content": b'%PDF-1.4\n...', "type": "application/pdf", "should_work": True},
        {"name": "Valid PDF with wrong type", "content": b'%PDF-1.4\n...', "type": "text/plain", "should_work": True},
        {"name": "Valid PDF with empty type", "content": b'%PDF-1.4\n...', "type": "", "should_work": True},
        {"name": "Valid PDF with None type", "content": b'%PDF-1.4\n...', "type": None, "should_work": True},
        {"name": "Valid PDF with invalid type", "content": b'%PDF-1.4\n...', "type": "a", "should_work": True},
        
        # Text files
        {"name": "Valid TXT", "content": b'This is a test', "type": "text/plain", "should_work": True},
        {"name": "TXT with wrong type", "content": b'This is a test', "type": "application/pdf", "should_work": True},
        
        # Edge cases
        {"name": "Empty content", "content": b'', "type": "application/pdf", "should_work": False},
    ]
    
    success = True
    
    for case in test_cases:
        print(f"\n{YELLOW}Testing: {case['name']}{RESET}")
        try:
            result = await processor.extract_text_from_bytes(
                file_content=case["content"],
                file_type=case["type"]
            )
            
            if case["should_work"]:
                print(f"{GREEN}✓ Success: {len(result)} characters extracted{RESET}")
            else:
                print(f"{RED}✗ Expected failure but got success{RESET}")
                success = False
                
        except Exception as e:
            if case["should_work"]:
                print(f"{RED}✗ Failed: {str(e)}{RESET}")
                success = False
            else:
                print(f"{GREEN}✓ Expected failure: {str(e)}{RESET}")
    
    return success


async def test_profiler_agent_tool_parameters():
    """Test the profiler agent's tool function parameter handling."""
    print(f"\n{YELLOW}=== Testing Profiler Agent Tool Parameters ==={RESET}")
    
    # Create dependencies
    prompt_manager = PromptManager()
    
    # Create profiler agent
    profiler_agent = ProfilerAgent(prompt_manager)
    
    # Mock context with dependencies
    class MockContext:
        def __init__(self):
            self.deps = ResumeCustomizerDeps(
                http_client=None,
                openrouter_api_key="test",
                model_name="test"
            )
    
    ctx = MockContext()
    
    # Test cases for the extract_resume_text tool
    test_cases = [
        {"name": "Valid PDF with valid type", "content": b'%PDF-1.4\n...', "type": "application/pdf", "should_work": True},
        {"name": "Valid PDF with invalid type", "content": b'%PDF-1.4\n...', "type": "a", "should_work": True},
        {"name": "Valid PDF with None type", "content": b'%PDF-1.4\n...', "type": None, "should_work": True},
        {"name": "Empty content", "content": b'', "type": "application/pdf", "should_work": False},
    ]
    
    success = True
    
    for case in test_cases:
        print(f"\n{YELLOW}Testing: {case['name']}{RESET}")
        try:
            result = await profiler_agent.agent.extract_resume_text(
                ctx,
                file_content=case["content"],
                file_type=case["type"]
            )
            
            if case["should_work"]:
                print(f"{GREEN}✓ Success: Tool function returned result{RESET}")
            else:
                print(f"{RED}✗ Expected failure but got success{RESET}")
                success = False
                
        except Exception as e:
            if case["should_work"]:
                print(f"{RED}✗ Failed: {str(e)}{RESET}")
                success = False
            else:
                print(f"{GREEN}✓ Expected failure: {str(e)}{RESET}")
    
    return success


async def test_content_type_detection():
    """Test the document processor's content type detection."""
    print(f"\n{YELLOW}=== Testing Content Type Detection ==={RESET}")
    
    # Create document processor
    processor = DocumentProcessor()
    
    # Test cases for content type detection
    test_cases = [
        {"name": "PDF detection", "content": b'%PDF-1.4\n...', "expected": "application/pdf"},
        {"name": "DOCX detection", "content": b'PK\x03\x04...', "expected": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        {"name": "Text detection", "content": b'This is a plain text file', "expected": "text/plain"},
        {"name": "Unknown type", "content": b'\x00\x01\x02\x03', "expected": "application/octet-stream"},
        {"name": "Empty content", "content": b'', "expected": "application/octet-stream"},
    ]
    
    success = True
    
    for case in test_cases:
        print(f"\n{YELLOW}Testing: {case['name']}{RESET}")
        try:
            detected = processor.detect_content_type(case["content"])
            
            if detected == case["expected"]:
                print(f"{GREEN}✓ Success: Detected {detected} as expected{RESET}")
            else:
                print(f"{RED}✗ Failed: Expected {case['expected']} but got {detected}{RESET}")
                success = False
                
        except Exception as e:
            print(f"{RED}✗ Failed with exception: {str(e)}{RESET}")
            success = False
    
    return success


async def main():
    """Main test runner."""
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}FILE UPLOAD FIX VERIFICATION TEST{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")
    
    # Run tests
    doc_processor_success = await test_document_processor_file_type_handling()
    profiler_agent_success = await test_profiler_agent_tool_parameters()
    content_detection_success = await test_content_type_detection()
    
    # Print summary
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}TEST SUMMARY{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")
    print(f"Document Processor File Type Handling: {GREEN}✓ PASS{RESET}" if doc_processor_success else f"Document Processor File Type Handling: {RED}✗ FAIL{RESET}")
    print(f"Profiler Agent Tool Parameters: {GREEN}✓ PASS{RESET}" if profiler_agent_success else f"Profiler Agent Tool Parameters: {RED}✗ FAIL{RESET}")
    print(f"Content Type Detection: {GREEN}✓ PASS{RESET}" if content_detection_success else f"Content Type Detection: {RED}✗ FAIL{RESET}")
    
    overall_success = doc_processor_success and profiler_agent_success and content_detection_success
    print(f"\nOverall Test Result: {GREEN}✓ PASS{RESET}" if overall_success else f"\nOverall Test Result: {RED}✗ FAIL{RESET}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
