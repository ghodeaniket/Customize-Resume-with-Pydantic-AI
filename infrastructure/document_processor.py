"""Document processing infrastructure for Resume Customizer."""
import io
import logging
import re
from typing import Dict, List, Optional, Tuple, Union
import time as import_time
import traceback

import docx
from PyPDF2 import PdfReader

# Import fitz (PyMuPDF) for more robust PDF processing
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF (fitz) is not available; using PyPDF2 only for PDF processing")

from core.exceptions import DocumentProcessingError
from core.logging import LoggerMixin
from core.utils.file_detection import (
    detect_file_type, PDF_MIME_TYPE, DOCX_MIME_TYPE, 
    TEXT_MIME_TYPE, OCTET_STREAM
)

logger = logging.getLogger(__name__)

class DocumentProcessor(LoggerMixin):
    """Processor for different document formats."""
    
    def __init__(self):
        """Initialize document processor."""
        pass
    
    async def extract_text_from_bytes(
        self, 
        file_content: bytes, 
        file_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """Extract text from various file formats.
        
        Args:
            file_content: Raw file content bytes
            file_type: MIME type of the file (optional)
            filename: Original filename (optional)
            
        Returns:
            str: Extracted text content
            
        Raises:
            DocumentProcessingError: If file type is unsupported or extraction fails
        """
        try:
            start_time = import_time.time()
            
            # Validate file content
            if not file_content or len(file_content) == 0:
                self.log_error("Empty file content")
                raise DocumentProcessingError(
                    message="Empty file content",
                    file_size=0
                )
                
            # Log hex header for debugging regardless of file type
            if len(file_content) > 0:
                hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
                self.log_debug(f"File header (hex): {hex_header}")
            
            # Determine the file type using the centralized detection utility
            actual_file_type = detect_file_type(file_content, file_type, filename)
            
            self.log_debug(f"Extracting text from file of type: {actual_file_type}")
            logger.info(f"Extracting text from file of type: {actual_file_type}, size: {len(file_content)} bytes")
            
            # Process based on detected file type
            if actual_file_type == PDF_MIME_TYPE:
                # Try PyMuPDF first if available (more robust)
                if PYMUPDF_AVAILABLE:
                    try:
                        self.log_info("Attempting PDF extraction with PyMuPDF")
                        return self._extract_from_pdf_pymupdf(file_content)
                    except Exception as e:
                        self.log_warning(f"PyMuPDF extraction failed, falling back to PyPDF2: {str(e)}")
                        # Fall through to PyPDF2
                
                # Use PyPDF2 as fallback or primary method if PyMuPDF is not available
                return self._extract_from_pdf(file_content)
            
            elif actual_file_type == DOCX_MIME_TYPE:
                return self._extract_from_docx(file_content)
            
            elif actual_file_type == TEXT_MIME_TYPE:
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
            
            else:
                self.log_warning(f"Unsupported file type: {actual_file_type}, attempting to process as text")
                # Try one more time as plain text as last resort
                try:
                    text = file_content.decode('utf-8', errors='replace')
                    self.log_info(f"Processed as text with unknown MIME type: {actual_file_type}")
                    return text
                except Exception:
                    self.log_error(f"Failed all extraction methods for file type: {actual_file_type}")
                    raise DocumentProcessingError(f"Unsupported file type: {actual_file_type}")
        
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
                self.log_file_error("No text extracted from PDF", PDF_MIME_TYPE, file_size)
                raise DocumentProcessingError(
                    message="No text could be extracted from PDF",
                    file_type=PDF_MIME_TYPE,
                    file_size=file_size
                )
            
        except Exception as e:
            total_time_ms = (import_time.time() - start_time) * 1000
            self.log_performance("pdf_extraction", total_time_ms, False, {"error": str(e)})
            self.log_file_error("Error processing PDF", PDF_MIME_TYPE, file_size, e)
            
            # Create details dict for more context
            details = {
                "extraction_method": "PyPDF2",
                "error_type": type(e).__name__
            }
            
            # Provide more specific error messages based on the exception
            if "file has not been decrypted" in str(e).lower():
                raise DocumentProcessingError(
                    message="PDF is encrypted and cannot be processed",
                    file_type=PDF_MIME_TYPE,
                    file_size=file_size,
                    details=details
                )
            elif "EOF marker not found" in str(e):
                raise DocumentProcessingError(
                    message="PDF file is incomplete or corrupted",
                    file_type=PDF_MIME_TYPE,
                    file_size=file_size,
                    details=details
                )
            else:
                raise DocumentProcessingError(
                    message=f"Error processing PDF: {str(e)}",
                    file_type=PDF_MIME_TYPE,
                    file_size=file_size,
                    details=details
                )
    
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX content.
        
        Args:
            content: DOCX file content
            
        Returns:
            str: Extracted text
        """
        start_time = import_time.time()
        file_size = len(content)
        
        self.log_file_processing("docx_extraction_start", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", file_size)
        
        docx_file = io.BytesIO(content)
        try:
            doc = docx.Document(docx_file)
            
            # Extract text from paragraphs
            paragraphs = [para.text for para in doc.paragraphs]
            self.log_debug(f"Extracted {len(paragraphs)} paragraphs from DOCX")
            
            # Extract text from tables if any
            table_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    table_text.append(" | ".join(row_text))
            
            if table_text:
                self.log_debug(f"Extracted text from {len(doc.tables)} tables")
                
            # Combine all text
            all_text = paragraphs + table_text
            text = "\n".join(all_text)
            
            # Clean and return text
            cleaned_text = self._clean_text(text)
            
            # Log performance and results
            total_time_ms = (import_time.time() - start_time) * 1000
            self.log_performance("docx_extraction", total_time_ms, True, 
                          {"paragraphs": len(paragraphs), "tables": len(doc.tables), 
                           "chars": len(cleaned_text)})
            
            # Log sample for verification
            sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
            self.log_debug(f"Extracted text sample: {sample}")
            
            return cleaned_text
            
        except Exception as e:
            total_time_ms = (import_time.time() - start_time) * 1000
            self.log_performance("docx_extraction", total_time_ms, False, {"error": str(e)})
            self.log_file_error("Error processing DOCX", DOCX_MIME_TYPE, file_size, e)
            
            raise DocumentProcessingError(
                message=f"Error processing DOCX: {str(e)}",
                file_type=DOCX_MIME_TYPE,
                file_size=file_size,
                details={"error_type": type(e).__name__}
            )
    
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
        
    def _extract_from_pdf_pymupdf(self, content: bytes) -> str:
        """Extract text from PDF content using PyMuPDF (more robust than PyPDF2).
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If PyMuPDF extraction fails
        """
        if not PYMUPDF_AVAILABLE:
            raise DocumentProcessingError(
                message="PyMuPDF not available for PDF extraction", 
                file_type=PDF_MIME_TYPE
            )
            
        start_time = import_time.time()
        file_size = len(content)
        self.log_file_processing("pdf_pymupdf_extraction_start", "application/pdf", file_size)
        
        try:
            # Open PDF from memory buffer
            pdf_file = io.BytesIO(content)
            doc = fitz.open(stream=pdf_file, filetype="pdf")
            
            text_parts = []
            
            # Process each page
            for i, page in enumerate(doc):
                page_start_time = import_time.time()
                try:
                    # Get text with more granular control
                    page_text = page.get_text("text")
                    page_time_ms = (import_time.time() - page_start_time) * 1000
                    
                    self.log_file_processing("pdf_pymupdf_page_extraction", "application/pdf", file_size,
                                      {"page": i+1, "chars": len(page_text), "time_ms": page_time_ms})
                    
                    if page_text:
                        text_parts.append(page_text)
                        
                except Exception as page_error:
                    self.log_file_error(f"PyMuPDF: Error extracting text from page {i+1}",
                                 "application/pdf", file_size, page_error)
                    # Try alternate extraction method
                    try:
                        # Fallback to blocks extraction
                        blocks = page.get_text("blocks")
                        block_text = "\n".join([b[4] for b in blocks if isinstance(b[4], str)])
                        if block_text:
                            text_parts.append(block_text)
                            self.log_debug(f"Recovered text from page {i+1} using blocks method")
                    except Exception:
                        # Continue with other pages
                        pass
            
            # Close the document
            doc.close()
            
            # Combine all text
            if text_parts:
                combined_text = "\n\n".join(text_parts)
                cleaned_text = self._clean_text(combined_text)
                
                total_time_ms = (import_time.time() - start_time) * 1000
                self.log_performance("pdf_pymupdf_extraction", total_time_ms, True,
                              {"pages": len(doc), "chars": len(cleaned_text)})
                
                # Log sample
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                self.log_debug(f"PyMuPDF extracted text sample: {sample}")
                
                return cleaned_text
            else:
                self.log_file_error("No text extracted from PDF with PyMuPDF", PDF_MIME_TYPE, file_size)
                raise DocumentProcessingError(
                    message="No text could be extracted from PDF with PyMuPDF",
                    file_type=PDF_MIME_TYPE,
                    file_size=file_size,
                    details={"extraction_method": "PyMuPDF"}
                )
                
        except Exception as e:
            total_time_ms = (import_time.time() - start_time) * 1000
            self.log_performance("pdf_pymupdf_extraction", total_time_ms, False, {"error": str(e)})
            
            # Include traceback in log for debugging
            tb = traceback.format_exc()
            self.log_error(f"PyMuPDF extraction error: {str(e)}\n{tb}")
            
            raise DocumentProcessingError(
                message=f"PyMuPDF PDF extraction error: {str(e)}",
                file_type=PDF_MIME_TYPE,
                file_size=file_size,
                details={
                    "extraction_method": "PyMuPDF",
                    "error_type": type(e).__name__
                }
            )
    
    def detect_content_type(self, file_content: bytes, content_type: Optional[str] = None, filename: Optional[str] = None) -> str:
        """Detect MIME type based on file content signatures.
        
        Args:
            file_content: Binary content of the file
            content_type: MIME type from request (optional)
            filename: Original filename (optional)
            
        Returns:
            str: Detected MIME type or application/octet-stream if unknown
        """
        file_size = len(file_content) if file_content else 0
        self.log_file_processing("content_detection", "unknown", file_size)
        
        # Use the centralized file detection utility
        detected_type = detect_file_type(file_content, content_type, filename)
        
        # Log the detection result based on the type
        if detected_type == PDF_MIME_TYPE:
            hex_header = " ".join([f"{b:02x}" for b in file_content[:20]]) if file_content else ""
            self.log_file_processing("signature_detection", PDF_MIME_TYPE, file_size, 
                                     {"signature": "PDF", "header": hex_header})
        
        elif detected_type == DOCX_MIME_TYPE:
            hex_header = " ".join([f"{b:02x}" for b in file_content[:20]]) if file_content else ""
            self.log_file_processing("signature_detection", DOCX_MIME_TYPE, file_size,
                                     {"signature": "PK", "header": hex_header})
        
        elif detected_type == TEXT_MIME_TYPE:
            sample = ""
            try:
                sample = file_content[:1024].decode('utf-8')[:50] if file_content else ""
            except UnicodeDecodeError:
                pass
                
            self.log_file_processing("text_detection", TEXT_MIME_TYPE, file_size,
                                     {"sample": sample})
        
        else:
            # Log the first bytes for unknown type
            if file_content and len(file_content) > 0:
                hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
                self.log_debug(f"Unknown file type. Header bytes: {hex_header}")
            
            self.log_file_processing("fallback_detection", OCTET_STREAM, file_size)
        
        return detected_type


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
