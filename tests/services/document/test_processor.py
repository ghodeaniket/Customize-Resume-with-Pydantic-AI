"""Tests for the document processor.

This module contains tests for the DocumentProcessor class.
"""

import io
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import docx
import fitz
from fastapi import UploadFile
from PyPDF2 import PdfReader

from resume_customizer.core.exceptions import DocumentProcessingError
from resume_customizer.services.document.processor import DocumentFormat, DocumentProcessor


@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "test_resume.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.file = MagicMock()
    mock_file.file.tell.return_value = 1000  # 1KB
    return mock_file


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    # In a real test, this would be a real PDF, but for now we'll use a mock
    return b"%PDF-1.5\nSample PDF content"


@pytest.fixture
def sample_docx_content():
    """Sample DOCX content for testing."""
    # In a real test, this would be a real DOCX, but for now we'll use a mock
    return b"Sample DOCX content"


@pytest.fixture
def sample_txt_content():
    """Sample TXT content for testing."""
    return b"Sample TXT content"


class TestDocumentProcessor:
    """Test cases for the DocumentProcessor class."""
    
    def test_get_format_from_content_type(self, mock_upload_file):
        """Test format detection from content type."""
        mock_upload_file.content_type = "application/pdf"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.PDF
        
        mock_upload_file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.DOCX
        
        mock_upload_file.content_type = "text/plain"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.TXT
        
        mock_upload_file.content_type = "application/unknown"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.UNKNOWN
    
    def test_get_format_from_filename(self, mock_upload_file):
        """Test format detection from filename."""
        mock_upload_file.content_type = None
        
        mock_upload_file.filename = "resume.pdf"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.PDF
        
        mock_upload_file.filename = "resume.docx"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.DOCX
        
        mock_upload_file.filename = "resume.txt"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.TXT
        
        mock_upload_file.filename = "resume.unknown"
        format_type = DocumentProcessor.get_format(mock_upload_file)
        assert format_type == DocumentFormat.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_is_valid_file_size_check(self, mock_upload_file):
        """Test file size validation."""
        # Simulate a file within size limits
        mock_upload_file.file.tell.return_value = 1000  # 1KB
        assert await DocumentProcessor.is_valid_file(mock_upload_file)
        
        # Simulate a file exceeding size limits
        with patch('resume_customizer.core.config.settings.MAX_UPLOAD_SIZE', 500):
            mock_upload_file.file.tell.return_value = 1000  # 1KB
            assert not await DocumentProcessor.is_valid_file(mock_upload_file)
    
    @pytest.mark.asyncio
    async def test_is_valid_file_format_check(self, mock_upload_file):
        """Test file format validation."""
        # Supported format
        mock_upload_file.content_type = "application/pdf"
        assert await DocumentProcessor.is_valid_file(mock_upload_file)
        
        # Unsupported format
        mock_upload_file.content_type = "application/unknown"
        mock_upload_file.filename = "resume.unknown"
        assert not await DocumentProcessor.is_valid_file(mock_upload_file)
    
    @pytest.mark.asyncio
    async def test_save_file(self, mock_upload_file):
        """Test saving a file."""
        mock_upload_file.read = AsyncMock(return_value=b"test content")
        
        with patch('builtins.open', create=True) as mock_open, \
             patch('os.makedirs') as mock_makedirs, \
             patch('resume_customizer.core.config.settings.UPLOAD_DIRECTORY', './test_uploads'):
            
            file_path = await DocumentProcessor.save_file(mock_upload_file)
            
            # Check that the directory was created
            mock_makedirs.assert_called_once_with('./test_uploads', exist_ok=True)
            
            # Check that the file was written
            mock_open.assert_called_once()
            assert str(file_path) == os.path.join('./test_uploads', 'test_resume.pdf')
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_with_pymupdf(self, sample_pdf_content):
        """Test PDF text extraction with PyMuPDF."""
        with patch('fitz.open') as mock_open:
            # Setup the mock
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Sample PDF text"
            mock_doc.load_page.return_value = mock_page
            mock_doc.__len__.return_value = 1
            mock_open.return_value = mock_doc
            
            # Call the function
            text = await DocumentProcessor.extract_text_from_pdf(sample_pdf_content)
            
            # Verify the result
            assert text == "Sample PDF text"
            mock_open.assert_called_once()
            mock_doc.load_page.assert_called_once_with(0)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_with_pypdf2_fallback(self, sample_pdf_content):
        """Test PDF text extraction with PyPDF2 fallback."""
        with patch('fitz.open', side_effect=Exception("PyMuPDF error")), \
             patch('PyPDF2.PdfReader') as mock_reader:
            
            # Setup the mock
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample PDF text"
            mock_reader.return_value.pages = [mock_page]
            
            # Call the function
            text = await DocumentProcessor.extract_text_from_pdf(sample_pdf_content)
            
            # Verify the result
            assert text == "Sample PDF text\n"
            mock_reader.assert_called_once()
            mock_page.extract_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_from_docx(self, sample_docx_content):
        """Test DOCX text extraction."""
        with patch('docx.Document') as mock_document:
            # Setup the mock
            mock_doc = MagicMock()
            mock_doc.paragraphs = [
                MagicMock(text="Paragraph 1"),
                MagicMock(text="Paragraph 2")
            ]
            mock_doc.tables = [
                MagicMock(rows=[
                    MagicMock(cells=[
                        MagicMock(text="Cell 1"),
                        MagicMock(text="Cell 2")
                    ])
                ])
            ]
            mock_document.return_value = mock_doc
            
            # Call the function
            text = await DocumentProcessor.extract_text_from_docx(sample_docx_content)
            
            # Verify the result
            assert "Paragraph 1" in text
            assert "Paragraph 2" in text
            assert "Cell 1" in text
            assert "Cell 2" in text
            mock_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_text_from_txt(self, sample_txt_content):
        """Test TXT text extraction."""
        # Call the function
        text = await DocumentProcessor.extract_text_from_txt(sample_txt_content)
        
        # Verify the result
        assert text == "Sample TXT content"
    
    @pytest.mark.asyncio
    async def test_extract_text_from_uploadfile(self, mock_upload_file, sample_pdf_content):
        """Test text extraction from UploadFile."""
        # Setup the mock
        mock_upload_file.read = AsyncMock(return_value=sample_pdf_content)
        
        with patch('resume_customizer.services.document.processor.DocumentProcessor.extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "Extracted text from PDF"
            
            # Call the function
            text = await DocumentProcessor.extract_text(mock_upload_file)
            
            # Verify the result
            assert text == "Extracted text from PDF"
            mock_extract.assert_called_once_with(sample_pdf_content)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_path(self, sample_pdf_content):
        """Test text extraction from Path."""
        # Setup mocks
        with patch('builtins.open', create=True) as mock_open, \
             patch('resume_customizer.services.document.processor.DocumentProcessor.extract_text_from_pdf') as mock_extract:
            
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = sample_pdf_content
            mock_open.return_value = mock_file
            mock_extract.return_value = "Extracted text from PDF"
            
            # Call the function
            text = await DocumentProcessor.extract_text(Path("test.pdf"))
            
            # Verify the result
            assert text == "Extracted text from PDF"
            mock_extract.assert_called_once_with(sample_pdf_content)
    
    @pytest.mark.asyncio
    async def test_extract_text_error_handling(self, mock_upload_file):
        """Test error handling in extract_text."""
        # Setup the mock to raise an error
        mock_upload_file.read = AsyncMock(side_effect=Exception("Read error"))
        
        # Call the function and expect an error
        with pytest.raises(DocumentProcessingError):
            await DocumentProcessor.extract_text(mock_upload_file)
