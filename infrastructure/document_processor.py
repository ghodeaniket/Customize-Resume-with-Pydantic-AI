"""Document processing infrastructure for Resume Customizer."""
import io
import logging
import re
from typing import Dict, List, Optional, Tuple, Union

import docx
from PyPDF2 import PdfReader

from core.exceptions import DocumentProcessingError
from core.logging import LoggerMixin

logger = logging.getLogger(__name__)

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
            logger.info(f"Extracting text from file of type: {file_type}, size: {len(file_content)} bytes")
            
            # Check if this is a PDF by examining the first few bytes (PDF signature)
            if file_content[:4] == b'%PDF':
                self.log_debug("PDF signature detected, processing as PDF")
                logger.info("PDF signature detected, processing as PDF")
                return self._extract_from_pdf(file_content)
            
            # Process by mime type
            if file_type == "application/pdf":
                return self._extract_from_pdf(file_content)
            
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._extract_from_docx(file_content)
            
            elif file_type == "text/plain":
                # For text files, just decode the bytes to string
                text = file_content.decode('utf-8')
                logger.info(f"Extracted text (first 100 chars): {text[:100]}")
                return text
            
            elif file_type == "application/octet-stream":
                # Try to determine file type based on content
                if file_content[:4] == b'%PDF':
                    self.log_debug("Detected PDF from content")
                    return self._extract_from_pdf(file_content)
                elif file_content[:2] == b'PK':
                    self.log_debug("Detected ZIP/DOCX from content")
                    return self._extract_from_docx(file_content)
                else:
                    # Try as plain text
                    try:
                        text = file_content.decode('utf-8')
                        self.log_debug("Successfully decoded as text")
                        return text
                    except UnicodeDecodeError:
                        self.log_error("Unrecognized binary content")
                        raise DocumentProcessingError("Unrecognized binary content")
            
            else:
                self.log_error(f"Unsupported file type: {file_type}")
                raise DocumentProcessingError(f"Unsupported file type: {file_type}")
        
        except Exception as e:
            self.log_error(f"Error extracting text from document: {str(e)}")
            logger.error(f"Error extracting text from document: {str(e)}", exc_info=True)
            raise DocumentProcessingError(f"Error extracting text from document: {str(e)}")
    
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
        """
        self.log_debug("Extracting text from PDF")
        logger.info(f"Extracting text from PDF of size {len(content)} bytes")
        
        # Log first few bytes for debugging
        logger.info(f"PDF header: {content[:20]}")
        
        pdf_file = io.BytesIO(content)
        try:
            reader = PdfReader(pdf_file)
            
            text = ""
            num_pages = len(reader.pages)
            logger.info(f"PDF has {num_pages} pages")
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                logger.info(f"Extracted {len(page_text)} characters from page {i+1}")
                text += page_text + "\n"
            
            cleaned_text = self._clean_text(text)
            logger.info(f"Cleaned text (first 200 chars): {cleaned_text[:200]}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            raise DocumentProcessingError(f"Error processing PDF: {str(e)}")
    
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX content.
        
        Args:
            content: DOCX file content
            
        Returns:
            str: Extracted text
        """
        self.log_debug("Extracting text from DOCX")
        logger.info(f"Extracting text from DOCX of size {len(content)} bytes")
        
        docx_file = io.BytesIO(content)
        try:
            doc = docx.Document(docx_file)
            
            paragraphs = [para.text for para in doc.paragraphs]
            logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX")
            
            text = "\n".join(paragraphs)
            cleaned_text = self._clean_text(text)
            logger.info(f"Cleaned text (first 200 chars): {cleaned_text[:200]}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}", exc_info=True)
            raise DocumentProcessingError(f"Error processing DOCX: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace but preserve paragraphs
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n')
        
        # Remove empty lines but preserve paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)
        
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
