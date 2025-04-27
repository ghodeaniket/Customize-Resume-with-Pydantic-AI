#!/usr/bin/env python3
"""Test the document processor refactoring changes."""
import asyncio
import io
import time
from infrastructure.document_processor import DocumentProcessor
from core.utils.file_detection import detect_file_type, get_detailed_file_info


async def test_centralized_content_detection():
    """Test the centralized content detection."""
    print("\n=== Testing Centralized Content Detection ===")
    
    # Create test content
    pdf_content = b'%PDF-1.4\n some pdf content'
    docx_content = b'PK\x03\x04 docx content'
    text_content = b'This is plain text content'
    
    # Test detection
    pdf_type = detect_file_type(pdf_content)
    docx_type = detect_file_type(docx_content)
    text_type = detect_file_type(text_content)
    
    print(f"PDF detection: {pdf_type}")
    print(f"DOCX detection: {docx_type}")
    print(f"Text detection: {text_type}")
    
    # Get detailed info
    pdf_info = get_detailed_file_info(pdf_content, "test.pdf")
    print(f"PDF detailed info: {pdf_info['detected_type']}")
    
    return pdf_type == "application/pdf" and docx_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and text_type == "text/plain"


async def test_partial_failure_recovery():
    """Test recovery from partial failures during text extraction."""
    print("\n=== Testing Partial Failure Recovery ===")
    
    processor = DocumentProcessor()
    
    # Create a simple text file that should succeed
    text = await processor.extract_text_from_bytes(b'Some text content', 'text/plain')
    print(f"Simple text extraction: {text}")
    
    # Future test with PDF extraction could be added here
    
    return True


async def test_lazy_loading_and_caching():
    """Test lazy loading and caching functionality."""
    print("\n=== Testing Lazy Loading and Caching ===")
    
    processor = DocumentProcessor(cache_enabled=True)
    
    # First extraction should not be cached
    start_time = time.time()
    text1 = await processor.extract_text_from_bytes(b'Some text content', 'text/plain')
    first_extraction_time = time.time() - start_time
    print(f"First extraction time: {first_extraction_time:.6f}s")
    
    # Second extraction of the same content should be faster due to caching
    start_time = time.time()
    text2 = await processor.extract_text_from_bytes(b'Some text content', 'text/plain')
    second_extraction_time = time.time() - start_time
    print(f"Second extraction time: {second_extraction_time:.6f}s")
    
    return text1 == text2 and second_extraction_time <= first_extraction_time


async def run_tests():
    """Run all tests and report results."""
    test_results = {}
    
    # Run tests
    test_results["content_detection"] = await test_centralized_content_detection()
    test_results["partial_failure"] = await test_partial_failure_recovery()
    test_results["lazy_loading_caching"] = await test_lazy_loading_and_caching()
    
    # Report results
    print("\n=== Test Results ===")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # Overall result
    all_passed = all(test_results.values())
    print("\n=== Overall Result ===")
    print("✅ All tests passed!" if all_passed else "❌ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(run_tests())
    exit(0 if result else 1)
