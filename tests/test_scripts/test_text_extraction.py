#!/usr/bin/env python3
"""
Test script for the text extraction functionality of the Document Processor.

This script tests just the text extraction functionality without requiring
the full API or UploadFile handling.
"""

import asyncio
from pathlib import Path

from resume_customizer.services.document.processor import DocumentProcessor, DocumentFormat


async def test_text_extraction():
    """Test the text extraction functionality."""
    print("\n=== Testing Text Extraction ===")
    
    # Test files
    current_dir = Path(__file__).parent
    test_resume_path = current_dir / "test_resume.txt"
    
    # Test TXT file processing
    try:
        with open(test_resume_path, "rb") as f:
            file_content = f.read()
        
        print(f"📝 Reading text file: {test_resume_path.name}")
        
        # Extract text
        text = await DocumentProcessor.extract_text(
            file=file_content,
            format_type=DocumentFormat.TXT
        )
        
        print(f"✅ Successfully extracted {len(text)} characters from TXT file")
        print("✅ Preview of extracted text:")
        print("-" * 40)
        print(text[:500] + "...")
        print("-" * 40)
        
        # Print completion message
        print("\n✅ Text extraction tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing text extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point for the test script."""
    print("=" * 80)
    print("TEXT EXTRACTION TEST SCRIPT")
    print("=" * 80)
    
    # Run tests
    success = await test_text_extraction()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Text Extraction: {'✅ PASS' if success else '❌ FAIL'}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
