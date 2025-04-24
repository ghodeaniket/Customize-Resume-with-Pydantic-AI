"""Document processing service."""
from typing import Dict, List, Optional, Tuple

from core.logging import LoggerMixin
from infrastructure.document_processor import DocumentProcessor, DocumentBuilder


class DocumentService(LoggerMixin):
    """Service for processing documents."""
    
    def __init__(
        self,
        document_processor: DocumentProcessor,
        document_builder: DocumentBuilder
    ):
        """Initialize document service.
        
        Args:
            document_processor: Document processor instance
            document_builder: Document builder instance
        """
        self.document_processor = document_processor
        self.document_builder = document_builder
    
    async def extract_text(
        self,
        file_content: bytes,
        file_type: str
    ) -> str:
        """Extract text from a document file.
        
        Args:
            file_content: Binary content of the file
            file_type: MIME type of the file
            
        Returns:
            str: Extracted text
        """
        self.log_info(f"Extracting text from file of type {file_type}")
        return await self.document_processor.extract_text_from_bytes(file_content, file_type)
    
    def create_markdown_document(
        self,
        sections: List[Tuple[str, str]]
    ) -> str:
        """Create a markdown document from sections.
        
        Args:
            sections: List of (section_title, section_content) tuples
            
        Returns:
            str: Markdown document
        """
        self.log_info(f"Creating markdown document with {len(sections)} sections")
        return self.document_builder.create_markdown(sections)
