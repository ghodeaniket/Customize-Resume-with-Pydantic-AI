"""Tests for the document processor service.

This module contains tests for the document processor service, which is responsible
for extracting text from various document formats.
"""

import os
import io
import pytest
from pathlib import Path
from fastapi import UploadFile

from resume_customizer.services.document.processor import DocumentProcessor, DocumentFormat


# Test file paths
TEST_DIR = Path(__file__).parent.parent.parent
TEST_RESUME_TXT = TEST_DIR / "test_resume.txt"
TEST_JOB_DESC_TXT = TEST_DIR / "test_job_description.txt"


@pytest.fixture
def test_txt_content():
    """Get the content of the test resume text file."""
    with open(TEST_RESUME_TXT, "rb") as f:
        return f.read()


@pytest.fixture
def test_txt_upload_file(test_txt_content):
    """Create a test UploadFile object for a text file."""
    return UploadFile(
        filename="test_resume.txt",
        file=io.BytesIO(test_txt_content),
        content_type="text/plain"
    )


@pytest.mark.asyncio
async def test_extract_text_from_txt_bytes(test_txt_content):
    """Test extracting text from a text file using bytes input."""
    # Extract text
    text = await DocumentProcessor.extract_text(
        file=test_txt_content,
        format_type=DocumentFormat.TXT
    )
    
    # Assertions
    assert text is not None
    assert len(text) > 0
    assert "John Smith" in text
    assert "Senior Software Engineer" in text


@pytest.mark.asyncio
async def test_extract_text_from_txt_uploadfile(test_txt_upload_file):
    """Test extracting text from a text file using UploadFile input."""
    # Extract text
    text = await DocumentProcessor.extract_text(
        file=test_txt_upload_file
    )
    
    # Reset file position
    await test_txt_upload_file.seek(0)
    
    # Assertions
    assert text is not None
    assert len(text) > 0
    assert "John Smith" in text
    assert "Senior Software Engineer" in text


@pytest.mark.asyncio
async def test_extract_text_from_path():
    """Test extracting text from a file path."""
    # Extract text
    text = await DocumentProcessor.extract_text(
        file=TEST_RESUME_TXT
    )
    
    # Assertions
    assert text is not None
    assert len(text) > 0
    assert "John Smith" in text
    assert "Senior Software Engineer" in text


@pytest.mark.asyncio
async def test_get_format(test_txt_upload_file):
    """Test getting the format of a document."""
    # Get format
    format_type = DocumentProcessor.get_format(test_txt_upload_file)
    
    # Assertions
    assert format_type == DocumentFormat.TXT


@pytest.mark.asyncio
async def test_is_valid_file(test_txt_upload_file):
    """Test validating a file."""
    # Validate file
    is_valid = await DocumentProcessor.is_valid_file(test_txt_upload_file)
    
    # Assertions
    assert is_valid is True


@pytest.mark.asyncio
async def test_empty_file():
    """Test handling an empty file."""
    # Create an empty file
    empty_file = UploadFile(
        filename="empty.txt",
        file=io.BytesIO(b""),
        content_type="text/plain"
    )
    
    # Extract text
    with pytest.raises(Exception) as excinfo:
        await DocumentProcessor.extract_text(empty_file)
    
    # Assertions
    assert "empty" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_unsupported_format():
    """Test handling an unsupported file format."""
    # Create a file with unsupported format
    unsupported_file = UploadFile(
        filename="test.xyz",
        file=io.BytesIO(b"Test content"),
        content_type="application/octet-stream"
    )
    
    # Get format
    format_type = DocumentProcessor.get_format(unsupported_file)
    
    # Assertions
    assert format_type == DocumentFormat.UNKNOWN


@pytest.mark.asyncio
async def test_save_file(test_txt_upload_file, tmp_path):
    """Test saving a file."""
    # Set a temporary upload directory
    from resume_customizer.core.config import settings
    original_upload_dir = settings.UPLOAD_DIRECTORY
    settings.UPLOAD_DIRECTORY = str(tmp_path)
    
    try:
        # Save file
        file_path = await DocumentProcessor.save_file(test_txt_upload_file)
        
        # Assertions
        assert file_path.exists()
        assert file_path.name == test_txt_upload_file.filename
        assert file_path.stat().st_size > 0
    finally:
        # Restore original upload directory
        settings.UPLOAD_DIRECTORY = original_upload_dir
