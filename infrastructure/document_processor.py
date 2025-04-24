"""Document processing infrastructure for Resume Customizer."""
import io
import re
from typing import Dict, List, Optional, Tuple, Union

import docx
from PyPDF2 import PdfReader

from core.exceptions import DocumentProcessingError
from core.logging import LoggerMixin


class DocumentProcessor(LoggerMixin):
    """Processor for different document formats."""
    
    def __init__(self):
        """Initialize document processor."""
        pass
    
    async def extract_text_from_bytes(
        self, 
        file_content: bytes, 
        file_type: str
    ) -> str:
        """Extract text from various file formats.
        
        Args:
            file_content: Raw file content bytes
            file_type: MIME type of the file
            
        Returns:
            str: Extracted text content
            
        Raises:
            DocumentProcessingError: If file type is unsupported or extraction fails
        """
        try:
            self.log_debug(f"Extracting text from file of type: {file_type}")
            
            if file_type == "application/pdf":
                return self._extract_from_pdf(file_content)
            
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._extract_from_docx(file_content)
            
            elif file_type == "text/plain":
                # For text files, just decode the bytes to string
                return file_content.decode('utf-8')
            
            else:
                self.log_error(f"Unsupported file type: {file_type}")
                raise DocumentProcessingError(f"Unsupported file type: {file_type}")
        
        except Exception as e:
            self.log_error(f"Error extracting text from document: {str(e)}")
            raise DocumentProcessingError(f"Error extracting text from document: {str(e)}")
    
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
        """
        self.log_debug("Extracting text from PDF")
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return self._clean_text(text)
    
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX content.
        
        Args:
            content: DOCX file content
            
        Returns:
            str: Extracted text
        """
        self.log_debug("Extracting text from DOCX")
        docx_file = io.BytesIO(content)
        doc = docx.Document(docx_file)
        
        text = "\n".join([para.text for para in doc.paragraphs])
        return self._clean_text(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove empty lines
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Fix line breaks
        text = text.replace('\r\n', '\n')
        
        return text.strip()


class DocumentBuilder(LoggerMixin):
    """Builder for creating documents in various formats."""
    
    def __init__(self):
        """Initialize document builder."""
        pass
    
    def create_markdown(self, sections: List[Tuple[str, str]]) -> str:
        """Create a markdown document from sections.
        
        Args:
            sections: List of (section_title, section_content) tuples
            
        Returns:
            str: Markdown document
        """
        self.log_debug(f"Creating markdown document with {len(sections)} sections")
        
        markdown = ""
        for title, content in sections:
            markdown += f"## {title}\n\n{content}\n\n"
        
        return markdown.strip()
