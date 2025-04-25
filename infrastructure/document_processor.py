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
        file_type: str = "application/octet-stream"
    ) -> str:
        """Extract text from various file formats.
        
        Args:
            file_content: Raw file content bytes
            file_type: MIME type of the file (defaults to application/octet-stream if not provided)
            
        Returns:
            str: Extracted text content
            
        Raises:
            DocumentProcessingError: If file type is unsupported or extraction fails
        """
        try:
            # Validate file_type parameter
            if not isinstance(file_type, str) or len(file_type.strip()) == 0:
                self.log_warning(f"Invalid file_type parameter: {file_type!r}, using default")
                file_type = "application/octet-stream"
            
            self.log_debug(f"Extracting text from file of type: {file_type}")
            logger.info(f"Extracting text from file of type: {file_type}, size: {len(file_content)} bytes")
            
            # Validate file content
            if not file_content or len(file_content) == 0:
                self.log_error("Empty file content")
                raise DocumentProcessingError("Empty file content")
            
            # Always check file signature first regardless of MIME type
            # Check if this is a PDF by examining the first few bytes (PDF signature)
            if len(file_content) >= 4 and file_content[:4] == b'%PDF':
                self.log_debug("PDF signature detected, processing as PDF")
                logger.info("PDF signature detected, processing as PDF regardless of MIME type")
                return self._extract_from_pdf(file_content)
            
            # Check for DOCX signature (PK zip header)
            if len(file_content) >= 2 and file_content[:2] == b'PK':
                self.log_debug("DOCX/ZIP signature detected")
                logger.info("DOCX/ZIP signature detected, attempting to process as DOCX")
                try:
                    return self._extract_from_docx(file_content)
                except Exception as e:
                    self.log_warning(f"Failed to process as DOCX: {str(e)}, falling back to MIME type")
                    # Continue with MIME type processing
            
            # Process by mime type as fallback
            if file_type == "application/pdf":
                return self._extract_from_pdf(file_content)
            
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._extract_from_docx(file_content)
            
            elif file_type == "text/plain":
                # For text files, just decode the bytes to string
                try:
                    text = file_content.decode('utf-8')
                    logger.info(f"Extracted text (first 100 chars): {text[:100]}")
                    return text
                except UnicodeDecodeError:
                    self.log_warning("Failed to decode as UTF-8, trying with errors='replace'")
                    text = file_content.decode('utf-8', errors='replace')
                    logger.info(f"Extracted text with replacement (first 100 chars): {text[:100]}")
                    return text
            
            elif file_type == "application/octet-stream":
                # Try to determine file type based on content
                if len(file_content) >= 4 and file_content[:4] == b'%PDF':
                    self.log_debug("Detected PDF from content")
                    return self._extract_from_pdf(file_content)
                elif len(file_content) >= 2 and file_content[:2] == b'PK':
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
                        raise DocumentProcessingError("Unrecognized binary content, unable to extract text")
            
            else:
                self.log_warning(f"Unsupported file type: {file_type}, attempting content-based detection")
                # Try one more time to detect file type based on content
                try:
                    # Try as plain text first
                    text = file_content.decode('utf-8', errors='replace')
                    self.log_info(f"Processed as text with unknown MIME type: {file_type}")
                    return text
                except Exception:
                    self.log_error(f"Failed all content detection methods for file type: {file_type}")
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
        start_time = import_time.time()
        file_size = len(content)
        
        self.log_file_processing("pdf_extraction_start", "application/pdf", file_size)
        
        # Log detailed content information for debugging
        if content[:4] != b'%PDF':
            hex_header = " ".join([f"{b:02x}" for b in content[:20]])
            self.log_warning(f"Content does not start with PDF signature. Header: {hex_header}")
        
        pdf_file = io.BytesIO(content)
        try:
            reader = PdfReader(pdf_file)
            
            # Get PDF metadata if available
            info = reader.metadata
            if info:
                self.log_debug(f"PDF metadata: {info}")
            
            text = ""
            num_pages = len(reader.pages)
            self.log_file_processing("pdf_structure", "application/pdf", file_size, 
                              {"pages": num_pages})
            
            # Process each page with detailed logging
            for i, page in enumerate(reader.pages):
                page_start_time = import_time.time()
                try:
                    page_text = page.extract_text()
                    page_time_ms = (import_time.time() - page_start_time) * 1000
                    
                    self.log_file_processing("pdf_page_extraction", "application/pdf", file_size, 
                                      {"page": i+1, "chars": len(page_text), 
                                       "time_ms": page_time_ms})
                    
                    text += page_text + "\n"
                except Exception as page_error:
                    self.log_file_error(f"Error extracting text from page {i+1}", 
                                 "application/pdf", file_size, page_error)
                    # Continue with other pages instead of failing completely
            
            # Clean the extracted text
            if text:
                cleaned_text = self._clean_text(text)
                total_time_ms = (import_time.time() - start_time) * 1000
                
                self.log_performance("pdf_extraction", total_time_ms, True, 
                              {"pages": num_pages, "chars": len(cleaned_text)})
                
                # Log sample of extracted text for verification
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                self.log_debug(f"Extracted text sample: {sample}")
                
                return cleaned_text
            else:
                self.log_file_error("No text extracted from PDF", "application/pdf", file_size)
                raise DocumentProcessingError("No text could be extracted from PDF")
            
        except Exception as e:
            total_time_ms = (import_time.time() - start_time) * 1000
            self.log_performance("pdf_extraction", total_time_ms, False, {"error": str(e)})
            self.log_file_error("Error processing PDF", "application/pdf", file_size, e)
            
            # Provide more specific error messages based on the exception
            if "file has not been decrypted" in str(e).lower():
                raise DocumentProcessingError("PDF is encrypted and cannot be processed")
            elif "EOF marker not found" in str(e):
                raise DocumentProcessingError("PDF file is incomplete or corrupted")
            else:
                raise DocumentProcessingError(f"Error processing PDF: {str(e)}")

# Import time at the module level to avoid import within function
import time as import_time
    
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
        
    def detect_content_type(self, file_content: bytes) -> str:
        """Detect MIME type based on file content signatures.
        
        Args:
            file_content: Binary content of the file
            
        Returns:
            str: Detected MIME type or application/octet-stream if unknown
        """
        file_size = len(file_content) if file_content else 0
        self.log_file_processing("content_detection", "unknown", file_size)
        
        if not file_content or len(file_content) == 0:
            self.log_warning("Empty file content")
            return "application/octet-stream"
            
        # Check for PDF signature
        if len(file_content) >= 4 and file_content[:4] == b'%PDF':
            # Log first 20 bytes in hex for debugging
            hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
            self.log_debug(f"PDF signature detected. Header bytes: {hex_header}")
            
            self.log_file_processing("signature_detection", "application/pdf", file_size, 
                                     {"signature": "PDF", "header": hex_header})
            return "application/pdf"
            
        # Check for DOCX/ZIP signature (PK header)
        if len(file_content) >= 2 and file_content[:2] == b'PK':
            # Log first 20 bytes in hex for debugging
            hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
            self.log_debug(f"DOCX/ZIP signature detected. Header bytes: {hex_header}")
            
            self.log_file_processing("signature_detection", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                     file_size, {"signature": "PK", "header": hex_header})
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
        # Check for text file by attempting to decode
        try:
            sample = file_content[:1024].decode('utf-8')
            # Log first 50 chars for debugging
            self.log_debug(f"Text content detected. Sample: {sample[:50]}...")
            
            self.log_file_processing("text_detection", "text/plain", file_size, 
                                     {"sample": sample[:50]})
            return "text/plain"
        except UnicodeDecodeError:
            pass
            
        # Log the first bytes for unknown type
        if len(file_content) > 0:
            hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
            self.log_debug(f"Unknown file type. Header bytes: {hex_header}")
        
        # Default to generic binary
        self.log_file_processing("fallback_detection", "application/octet-stream", file_size)
        return "application/octet-stream"


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
