"""Document processing infrastructure for Resume Customizer."""
import io
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Union
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
            ServiceError: If file type is unsupported or extraction fails
        """
        start_time = time.time()
        
        # Validate file content
        if not file_content or len(file_content) == 0:
            self.log_error("Empty file content")
            raise DocumentProcessingError(
                message="Empty file content",
                file_size=0
            )
        
        # Log initial file info
        file_size = len(file_content)
        self.log_file_processing("extraction_start", "unknown", file_size)
        
        # Determine the file type using the centralized detection utility
        actual_file_type = detect_file_type(file_content, file_type, filename)
        
        # Log file detection results
        from core.utils.file_detection import log_file_detection
        log_file_detection(file_content, actual_file_type, self.log_file_processing)
        
        self.log_info(f"Extracting text from file of type: {actual_file_type}, size: {file_size} bytes")
        
        try:
            # Process based on detected file type
            if actual_file_type == PDF_MIME_TYPE:
                return await self._extract_from_pdf_with_fallback(file_content)
            
            elif actual_file_type == DOCX_MIME_TYPE:
                return self._extract_from_docx(file_content)
            
            elif actual_file_type == TEXT_MIME_TYPE:
                return self._extract_from_text(file_content)
            
            else:
                # Try as text for unknown types
                try:
                    return self._extract_from_text(file_content)
                except UnicodeDecodeError:
                    self.log_error(f"Unsupported file type: {actual_file_type}")
                    raise DocumentProcessingError(
                        message=f"Unsupported file type: {actual_file_type}",
                        file_type=actual_file_type,
                        file_size=file_size
                    )
                
        except Exception as e:
            self.log_error(f"Error extracting text from document: {str(e)}")
            raise DocumentProcessingError(
                message=f"Error extracting text from document: {str(e)}",
                file_type=actual_file_type,
                file_size=file_size,
                details={"error_type": type(e).__name__}
            )
    
    async def _extract_from_pdf_with_fallback(self, content: bytes) -> str:
        """Extract text from PDF content with fallback mechanism.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            ServiceError: If all extraction methods fail
        """
        # Try PyMuPDF first if available (more robust)
        if PYMUPDF_AVAILABLE:
            try:
                self.log_info("Attempting PDF extraction with PyMuPDF")
                return self._extract_from_pdf_pymupdf(content)
            except Exception as e:
                self.log_warning(f"PyMuPDF extraction failed, falling back to PyPDF2: {str(e)}")
                # Fall through to PyPDF2
        
        # Use PyPDF2 as fallback or primary method if PyMuPDF is not available
        return self._extract_from_pdf(content)
    
    def _extract_from_text(self, content: bytes) -> str:
        """Extract text from text file content.
        
        Args:
            content: Text file content
            
        Returns:
            str: Decoded text
            
        Raises:
            UnicodeDecodeError: If content cannot be decoded as text
        """
        try:
            text = content.decode('utf-8')
            self.log_debug(f"Extracted text (first 100 chars): {text[:100]}")
            return text
        except UnicodeDecodeError:
            self.log_warning("Failed to decode as UTF-8, trying with errors='replace'")
            text = content.decode('utf-8', errors='replace')
            self.log_debug(f"Extracted text with replacement (first 100 chars): {text[:100]}")
            return text
    
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
        """
        start_time = time.time()
        file_size = len(content)
        
        self.log_file_processing("pdf_extraction_start", PDF_MIME_TYPE, file_size)
        
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
            
            text_parts = []
            num_pages = len(reader.pages)
            successful_pages = 0
            
            self.log_file_processing("pdf_structure", PDF_MIME_TYPE, file_size, 
                              {"pages": num_pages})
            
            # Process each page with detailed logging
            for i, page in enumerate(reader.pages):
                page_start_time = time.time()
                try:
                    page_text = page.extract_text()
                    page_time_ms = (time.time() - page_start_time) * 1000
                    
                    self.log_file_processing("pdf_page_extraction", PDF_MIME_TYPE, file_size, 
                                      {"page": i+1, "chars": len(page_text), 
                                       "time_ms": page_time_ms})
                    
                    if page_text.strip():  # Only add non-empty pages
                        text_parts.append(page_text)
                        successful_pages += 1
                except Exception as page_error:
                    self.log_file_error(f"Error extracting text from page {i+1}", 
                                 PDF_MIME_TYPE, file_size, page_error)
                    # Continue with other pages instead of failing completely
            
            # Calculate success rate for extraction
            success_rate = successful_pages / num_pages if num_pages > 0 else 0
            
            # Clean the extracted text
            if text_parts:
                text = "\n\n".join(text_parts)
                cleaned_text = self._clean_text(text)
                total_time_ms = (time.time() - start_time) * 1000
                
                self.log_performance("pdf_extraction", total_time_ms, True, 
                              {"pages": num_pages, "successful_pages": successful_pages,
                               "success_rate": f"{success_rate:.2f}", "chars": len(cleaned_text)})
                
                # Log sample of extracted text for verification
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                self.log_debug(f"Extracted text sample: {sample}")
                
                # Warn if partial extraction
                if success_rate < 1.0:
                    self.log_warning(f"Partial PDF extraction: {successful_pages}/{num_pages} pages extracted")
                
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
            ServiceError: If PyMuPDF extraction fails
        """
        if not PYMUPDF_AVAILABLE:
            raise DocumentProcessingError(
                message="PyMuPDF not available for PDF extraction", 
                file_type=PDF_MIME_TYPE
            )
            
        start_time = import_time.time()
        file_size = len(content)
        self.log_file_processing("pdf_pymupdf_extraction_start", PDF_MIME_TYPE, file_size)
        
        try:
            # Open PDF from memory buffer
            pdf_file = io.BytesIO(content)
            doc = fitz.open(stream=pdf_file, filetype="pdf")
            
            text_parts = []
            num_pages = len(doc)
            successful_pages = 0
            
            # Process each page
            for i, page in enumerate(doc):
                page_start_time = import_time.time()
                page_extracted = False
                
                # Try primary extraction method
                try:
                    page_text = page.get_text("text")
                    page_time_ms = (import_time.time() - page_start_time) * 1000
                    
                    self.log_file_processing("pdf_pymupdf_page_extraction", PDF_MIME_TYPE, file_size,
                                      {"page": i+1, "chars": len(page_text), "time_ms": page_time_ms})
                    
                    if page_text.strip():
                        text_parts.append(page_text)
                        successful_pages += 1
                        page_extracted = True
                        
                except Exception as page_error:
                    self.log_file_error(f"PyMuPDF: Error extracting text from page {i+1}",
                                 PDF_MIME_TYPE, file_size, page_error)
                    # Continue to fallback method
                
                # Try fallback extraction method if primary failed
                if not page_extracted:
                    try:
                        blocks = page.get_text("blocks")
                        block_text = "\n".join([b[4] for b in blocks if isinstance(b[4], str)])
                        if block_text.strip():
                            text_parts.append(block_text)
                            successful_pages += 1
                            self.log_debug(f"Recovered text from page {i+1} using blocks method")
                    except Exception as block_error:
                        self.log_file_error(f"PyMuPDF: Block extraction failed for page {i+1}",
                                     PDF_MIME_TYPE, file_size, block_error)
                        # Continue with other pages
            
            # Close the document
            doc.close()
            
            # Calculate success rate
            success_rate = successful_pages / num_pages if num_pages > 0 else 0
            
            # Combine all text
            if text_parts:
                combined_text = "\n\n".join(text_parts)
                cleaned_text = self._clean_text(combined_text)
                
                total_time_ms = (import_time.time() - start_time) * 1000
                self.log_performance("pdf_pymupdf_extraction", total_time_ms, True,
                              {"pages": num_pages, "successful_pages": successful_pages,
                               "success_rate": f"{success_rate:.2f}", "chars": len(cleaned_text)})
                
                # Log sample
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                self.log_debug(f"PyMuPDF extracted text sample: {sample}")
                
                # Warn if partial extraction
                if success_rate < 1.0:
                    self.log_warning(f"Partial PDF extraction with PyMuPDF: {successful_pages}/{num_pages} pages extracted")
                
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
            
            # Log error without full traceback for cleaner logs
            self.log_error(f"PyMuPDF extraction error: {str(e)}")
            
            raise DocumentProcessingError(
                message=f"PyMuPDF PDF extraction error: {str(e)}",
                file_type=PDF_MIME_TYPE,
                file_size=file_size,
                details={
                    "extraction_method": "PyMuPDF",
                    "error_type": type(e).__name__
                }
            )
    
    # Method removed: detect_content_type is now consolidated to use the centralized detect_file_type utility


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
