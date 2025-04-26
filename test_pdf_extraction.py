#!/usr/bin/env python3
"""
Test script to verify PDF text extraction is working properly.
"""

import asyncio
import os
import sys
from pathlib import Path

from infrastructure.document_processor import DocumentProcessor, PYMUPDF_AVAILABLE

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Find PDFs in the repository for testing
def find_test_pdfs(directory: str = '.') -> list[Path]:
    """Find PDF files for testing."""
    pdfs = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.lower().endswith('.pdf'):
                pdfs.append(Path(dirpath) / filename)
    return pdfs


async def test_pdf_extraction(pdf_path: Path) -> bool:
    """Test both PDF extraction methods on a PDF file."""
    print(f"\n{YELLOW}Testing PDF extraction on: {pdf_path}{RESET}")
    
    processor = DocumentProcessor()
    success = True
    
    try:
        # Load the PDF content
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
            
        # Test PyPDF2 extraction
        print(f"\n{BLUE}Using PyPDF2 extraction:{RESET}")
        try:
            pypdf_text = await processor._extract_from_pdf(pdf_content)
            print(f"{GREEN}✓ PyPDF2 extraction successful{RESET}")
            print(f"  Extracted {len(pypdf_text)} characters")
            if len(pypdf_text) > 0:
                print(f"  Sample: {pypdf_text[:100]}...")
        except Exception as e:
            print(f"{RED}✗ PyPDF2 extraction failed: {str(e)}{RESET}")
            success = False
            
        # Test PyMuPDF extraction if available
        if PYMUPDF_AVAILABLE:
            print(f"\n{BLUE}Using PyMuPDF extraction:{RESET}")
            try:
                pymupdf_text = await processor._extract_from_pdf_pymupdf(pdf_content)
                print(f"{GREEN}✓ PyMuPDF extraction successful{RESET}")
                print(f"  Extracted {len(pymupdf_text)} characters")
                if len(pymupdf_text) > 0:
                    print(f"  Sample: {pymupdf_text[:100]}...")
            except Exception as e:
                print(f"{RED}✗ PyMuPDF extraction failed: {str(e)}{RESET}")
                success = False
        else:
            print(f"{YELLOW}⚠ PyMuPDF not available, skipping test{RESET}")
            
        # Test full extraction pipeline with file type "a" (the problematic value)
        print(f"\n{BLUE}Testing full extraction pipeline with file_type='a':{RESET}")
        try:
            full_text = await processor.extract_text_from_bytes(
                file_content=pdf_content,
                file_type="a"  # This should no longer cause an error
            )
            print(f"{GREEN}✓ Extraction with 'a' file type successful{RESET}")
            print(f"  Extracted {len(full_text)} characters")
            if len(full_text) > 0:
                print(f"  Sample: {full_text[:100]}...")
        except Exception as e:
            print(f"{RED}✗ Extraction with 'a' file type failed: {str(e)}{RESET}")
            success = False
            
        return success
    except Exception as e:
        print(f"{RED}✗ General error during test: {str(e)}{RESET}")
        return False


async def main():
    """Main test function."""
    print(f"{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}PDF EXTRACTION TEST{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")
    
    # Find test PDFs
    test_pdfs = find_test_pdfs()
    if not test_pdfs:
        print(f"{YELLOW}No PDF files found for testing.{RESET}")
        
        # Create a simple test PDF in memory for testing
        print(f"{YELLOW}Creating a minimal test PDF in memory.{RESET}")
        pdf_content = b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Parent 2 0 R/Contents 4 0 R>>endobj 4 0 obj<</Length 21>>stream\nBT /F1 12 Tf (Test) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n0000000194 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n264\n%%EOF\n'
        
        # Test with the minimal PDF
        processor = DocumentProcessor()
        
        success = True
        try:
            # Test full extraction pipeline with file type "a"
            text = await processor.extract_text_from_bytes(
                file_content=pdf_content,
                file_type="a"  # This should no longer cause an error
            )
            print(f"{GREEN}✓ Extraction with 'a' file type successful{RESET}")
            print(f"  Result: {text}")
        except Exception as e:
            print(f"{RED}✗ Extraction with 'a' file type failed: {str(e)}{RESET}")
            success = False
            
        print(f"\n{YELLOW}{'='*80}{RESET}")
        print(f"{YELLOW}TEST SUMMARY{RESET}")
        print(f"{YELLOW}{'='*80}{RESET}")
        print(f"Memory PDF Test: {GREEN}✓ PASS{RESET}" if success else f"Memory PDF Test: {RED}✗ FAIL{RESET}")
        
        return 0 if success else 1
    
    results = []
    for pdf in test_pdfs:
        result = await test_pdf_extraction(pdf)
        results.append((pdf, result))
    
    # Print summary
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}TEST SUMMARY{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}")
    
    for pdf, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"{pdf}: {status}")
        
    # Overall result
    all_passed = all(result for _, result in results)
    print(f"\nOverall Result: {GREEN}✓ ALL TESTS PASSED{RESET}" if all_passed else f"\nOverall Result: {RED}✗ SOME TESTS FAILED{RESET}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
