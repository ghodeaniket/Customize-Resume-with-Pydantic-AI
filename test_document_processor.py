#!/usr/bin/env python3
"""
Test script for the Document Processor functionality.

This script tests the basic functionality of the Document Processor
without requiring the full API to be running.
"""

import asyncio
import os
from pathlib import Path

from resume_customizer.services.document.processor import DocumentProcessor, DocumentFormat


async def test_document_processor():
    """Test the document processor with various file formats."""
    print("\n=== Testing Document Processor ===")
    
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
        
        # Test saving file
        from io import BytesIO
        from fastapi import UploadFile
        
        # Create a mock UploadFile
        mock_file = UploadFile(
            filename=test_resume_path.name,
            file=BytesIO(file_content)
        )
        # Set content_type after initialization
        mock_file.content_type = "text/plain"
        
        # Test is_valid_file
        is_valid = await DocumentProcessor.is_valid_file(mock_file)
        print(f"✅ File validation: {'passed' if is_valid else 'failed'}")
        
        # Test save_file
        if is_valid:
            saved_path = await DocumentProcessor.save_file(mock_file)
            print(f"✅ File saved to: {saved_path}")
            
            # Clean up
            if os.path.exists(saved_path):
                print(f"✅ Cleaning up saved file")
                os.remove(saved_path)
        
        # Print completion message
        print("\n✅ Document processor tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing document processor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point for the test script."""
    print("=" * 80)
    print("DOCUMENT PROCESSOR TEST SCRIPT")
    print("=" * 80)
    
    # Run tests
    success = await test_document_processor()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Document Processor: {'✅ PASS' if success else '❌ FAIL'}")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
