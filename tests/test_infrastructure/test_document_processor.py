"""Tests for the document processor."""
import io
import pytest
from unittest.mock import MagicMock, patch

from infrastructure.document_processor import DocumentProcessor, DocumentBuilder
from core.exceptions import DocumentProcessingError


@pytest.fixture
def sample_text() -> str:
    """Get sample text content.
    
    Returns:
        str: Sample text content
    """
    return "This is a sample text document."


@pytest.fixture
def sample_docx_bytes() -> bytes:
    """Mock sample DOCX bytes.
    
    Returns:
        bytes: Mock DOCX content
    """
    return b"Mock DOCX content"


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Mock sample PDF bytes.
    
    Returns:
        bytes: Mock PDF content
    """
    return b"Mock PDF content"


@pytest.mark.asyncio
async def test_document_processor_init() -> None:
    """Test document processor initialization."""
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Check initialization
    assert isinstance(processor, DocumentProcessor)


@pytest.mark.asyncio
async def test_extract_text_from_plain_text(sample_text: str) -> None:
    """Test extracting text from plain text.
    
    Args:
        sample_text: Sample text content
    """
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Extract text from plain text
    result = await processor.extract_text_from_bytes(
        sample_text.encode('utf-8'), 
        'text/plain'
    )
    
    # Check result
    assert result == sample_text


@pytest.mark.asyncio
async def test_extract_text_from_docx(sample_docx_bytes: bytes) -> None:
    """Test extracting text from DOCX.
    
    Args:
        sample_docx_bytes: Sample DOCX content
    """
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Create mock Document
    mock_doc = MagicMock()
    mock_doc.paragraphs = [
        MagicMock(text="Paragraph 1"),
        MagicMock(text="Paragraph 2")
    ]
    
    # Mock the docx.Document constructor
    with patch('docx.Document', return_value=mock_doc):
        # Mock the _extract_from_docx method to avoid implementation details
        with patch.object(processor, '_extract_from_docx') as mock_extract:
            mock_extract.return_value = "Paragraph 1\nParagraph 2"
            
            # Extract text from DOCX
            result = await processor.extract_text_from_bytes(
                sample_docx_bytes, 
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
    
    # Check result
    assert result == "Paragraph 1\nParagraph 2"


@pytest.mark.asyncio
async def test_extract_text_from_pdf(sample_pdf_bytes: bytes) -> None:
    """Test extracting text from PDF.
    
    Args:
        sample_pdf_bytes: Sample PDF content
    """
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Mock the _extract_from_pdf method to avoid implementation details
    with patch.object(processor, '_extract_from_pdf') as mock_extract:
        mock_extract.return_value = "Page 1 content\nPage 2 content"
        
        # Extract text from PDF
        result = await processor.extract_text_from_bytes(
            sample_pdf_bytes, 
            'application/pdf'
        )
    
    # Check result
    assert result == "Page 1 content\nPage 2 content"


@pytest.mark.asyncio
async def test_extract_text_unsupported_type() -> None:
    """Test error when extracting text from unsupported file type."""
    # Initialize document processor
    processor = DocumentProcessor()
    
    # Try to extract text from unsupported file type
    with pytest.raises(DocumentProcessingError):
        await processor.extract_text_from_bytes(
            b"Sample content", 
            'application/unsupported'
        )


def test_document_builder_init() -> None:
    """Test document builder initialization."""
    # Initialize document builder
    builder = DocumentBuilder()
    
    # Check initialization
    assert isinstance(builder, DocumentBuilder)


def test_document_builder_create_markdown() -> None:
    """Test creating a markdown document."""
    # Initialize document builder
    builder = DocumentBuilder()
    
    # Create sections
    sections = [
        ("Section 1", "Content 1"),
        ("Section 2", "Content 2\nWith multiple lines"),
        ("Section 3", "- Bullet 1\n- Bullet 2")
    ]
    
    # Create markdown document
    markdown = builder.create_markdown(sections)
    
    # Check markdown content
    expected = (
        "## Section 1\n\n"
        "Content 1\n\n"
        "## Section 2\n\n"
        "Content 2\nWith multiple lines\n\n"
        "## Section 3\n\n"
        "- Bullet 1\n- Bullet 2"
    )
    
    assert markdown == expected
