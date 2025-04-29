"""Test boundary conditions for file processing.

This module tests various edge cases and boundary conditions for file processing,
focusing on file sizes, formats, and content validation.
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import UploadFile

from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import DocumentProcessingError
from resume_customizer.services.document.processor import DocumentFormat, DocumentProcessor


class MockUploadFile:
    """Mock UploadFile class for testing."""
    
    def __init__(self, filename, content, content_type="text/plain"):
        """Initialize the mock file."""
        self.filename = filename
        self.file = io.BytesIO(content)
        self.content_type = content_type
    
    async def read(self):
        """Read the file content."""
        return self.file.getvalue()
    
    async def seek(self, position):
        """Seek to a position in the file."""
        self.file.seek(position)


@pytest.mark.asyncio
async def test_file_size_boundaries():
    """Test boundary conditions for file sizes."""
    # Save original max size
    original_max_size = settings.MAX_UPLOAD_SIZE
    
    try:
        # Set a specific size for testing
        settings.MAX_UPLOAD_SIZE = 1024  # 1KB
        
        # Test empty file (0 bytes)
        empty_file = MockUploadFile("empty.txt", b"")
        assert await DocumentProcessor.is_valid_file(empty_file)
        
        # Test file exactly at size limit
        exact_size_file = MockUploadFile("exact.txt", b"x" * 1024)
        assert await DocumentProcessor.is_valid_file(exact_size_file)
        
        # Test file 1 byte over limit
        over_limit_file = MockUploadFile("over.txt", b"x" * 1025)
        assert not await DocumentProcessor.is_valid_file(over_limit_file)
        
        # Test file just under limit
        under_limit_file = MockUploadFile("under.txt", b"x" * 1023)
        assert await DocumentProcessor.is_valid_file(under_limit_file)
        
    finally:
        # Restore original max size
        settings.MAX_UPLOAD_SIZE = original_max_size


@pytest.mark.asyncio
async def test_file_format_boundaries():
    """Test boundary conditions for file formats."""
    # Test different file extensions with mismatched content types
    
    # TXT file with PDF content type
    mixed_file1 = MockUploadFile("text.txt", b"Plain text content", "application/pdf")
    assert DocumentProcessor.get_format(mixed_file1) == DocumentFormat.PDF
    
    # PDF file with TXT content type
    mixed_file2 = MockUploadFile("doc.pdf", b"%PDF-1.5\nSample content", "text/plain")
    assert DocumentProcessor.get_format(mixed_file2) == DocumentFormat.TXT
    
    # File with no extension but valid content type
    no_ext_file = MockUploadFile("noextension", b"Some content", "text/plain")
    assert DocumentProcessor.get_format(no_ext_file) == DocumentFormat.TXT
    
    # File with valid extension but missing content type
    no_type_file = MockUploadFile("doc.pdf", b"%PDF content", None)
    assert DocumentProcessor.get_format(no_type_file) == DocumentFormat.PDF
    
    # File with no extension and no content type
    unknown_file = MockUploadFile("unknown", b"Mystery content", None)
    assert DocumentProcessor.get_format(unknown_file) == DocumentFormat.UNKNOWN
    
    # File with invalid extension but valid content type
    weird_ext_file = MockUploadFile("doc.xyz", b"Content", "application/pdf")
    assert DocumentProcessor.get_format(weird_ext_file) == DocumentFormat.PDF


@pytest.mark.asyncio
async def test_malformed_file_content():
    """Test handling of malformed file content."""
    # Malformed PDF
    malformed_pdf = MockUploadFile(
        "broken.pdf", 
        b"%PDF-1.5\nThis is not a valid PDF file",
        "application/pdf"
    )
    
    # Mock the PyMuPDF and PyPDF2 extraction to simulate failures
    with patch('fitz.open', side_effect=Exception("Invalid PDF structure")), \
         patch('PyPDF2.PdfReader', side_effect=Exception("Cannot read PDF")):
        
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.extract_text_from_pdf(await malformed_pdf.read())
    
    # Malformed DOCX
    malformed_docx = MockUploadFile(
        "broken.docx",
        b"PK\x03\x04\x14\x00\x00\x00Invalid DOCX content",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    
    # Mock docx.Document to simulate failure
    with patch('docx.Document', side_effect=Exception("Cannot parse DOCX")):
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.extract_text_from_docx(await malformed_docx.read())
    
    # Text file with invalid encoding
    invalid_encoding = MockUploadFile(
        "invalid_encoding.txt",
        bytes([0xFF, 0xFE, 0xFD]),  # Invalid UTF-8
        "text/plain"
    )
    
    with pytest.raises(DocumentProcessingError):
        await DocumentProcessor.extract_text_from_txt(await invalid_encoding.read())


@pytest.mark.asyncio
async def test_file_with_minimal_content():
    """Test handling of files with minimal valid content."""
    # Minimal PDF
    minimal_pdf = MockUploadFile(
        "minimal.pdf",
        b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>",
        "application/pdf"
    )
    
    # Mock successful extraction but with empty content
    with patch('fitz.open'), \
         patch('resume_customizer.services.document.processor.DocumentProcessor.extract_text_from_pdf',
              AsyncMock(return_value="")):
        
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.extract_text(minimal_pdf)
    
    # Minimal DOCX (mock)
    with patch('resume_customizer.services.document.processor.DocumentProcessor.extract_text_from_docx',
              AsyncMock(return_value="")):
        
        minimal_docx = MockUploadFile(
            "minimal.docx",
            b"PK minimal docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.extract_text(minimal_docx)


@pytest.mark.asyncio
async def test_file_name_special_cases():
    """Test handling of files with special characters in names."""
    # File with spaces in name
    spaced_name = MockUploadFile("my document.pdf", b"%PDF-1.5\nContent", "application/pdf")
    assert DocumentProcessor.get_format(spaced_name) == DocumentFormat.PDF
    
    # File with unicode characters in name
    unicode_name = MockUploadFile("résumé.pdf", b"%PDF-1.5\nContent", "application/pdf")
    assert DocumentProcessor.get_format(unicode_name) == DocumentFormat.PDF
    
    # File with very long name
    long_name = MockUploadFile("a" * 200 + ".pdf", b"%PDF-1.5\nContent", "application/pdf")
    assert DocumentProcessor.get_format(long_name) == DocumentFormat.PDF
    
    # File with special characters
    special_chars = MockUploadFile("file!@#$%^&*().pdf", b"%PDF-1.5\nContent", "application/pdf")
    assert DocumentProcessor.get_format(special_chars) == DocumentFormat.PDF
