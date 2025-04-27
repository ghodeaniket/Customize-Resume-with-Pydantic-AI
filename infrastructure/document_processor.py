"""Document processing infrastructure for Resume Customizer."""
import io
import logging
import re
import time
import hashlib
import functools
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import traceback
from functools import lru_cache

import docx
from PyPDF2 import PdfReader

# Lazy loading for PyMuPDF - don't import at module level
PYMUPDF_AVAILABLE = None
fitz = None  # Will be imported on-demand

from core.exceptions import DocumentProcessingError
from core.logging import LoggerMixin
from core.utils.file_detection import (
    detect_file_type, get_detailed_file_info, PDF_MIME_TYPE, 
    DOCX_MIME_TYPE, TEXT_MIME_TYPE, OCTET_STREAM
)

logger = logging.getLogger(__name__)


def lazy_import_pymupdf():
    """Lazily import PyMuPDF only when needed to improve startup time."""
    global PYMUPDF_AVAILABLE, fitz
    
    if PYMUPDF_AVAILABLE is None:
        try:
            import fitz as pymupdf
            fitz = pymupdf
            PYMUPDF_AVAILABLE = True
            logger.debug("PyMuPDF successfully imported")
        except ImportError:
            PYMUPDF_AVAILABLE = False
            logger.warning("PyMuPDF (fitz) is not available; using PyPDF2 only for PDF processing")
    
    return PYMUPDF_AVAILABLE


# Cache for document extraction results
_EXTRACTION_CACHE = {}
_CACHE_MAX_SIZE = 16
_CACHE_MAX_AGE_SECONDS = 3600  # 1 hour

def document_extraction_cache(extraction_func: Callable) -> Callable:
    """Decorator to cache document extraction results.
    
    Args:
        extraction_func: The extraction function to wrap with caching
        
    Returns:
        Callable: Wrapped function with caching
    """
    @functools.wraps(extraction_func)
    def wrapper(self, content: bytes, *args, **kwargs) -> str:
        # Skip caching if disabled
        if not getattr(self, 'cache_enabled', True):
            return extraction_func(self, content, *args, **kwargs)
            
        # Create a hash of the content to use as cache key
        content_hash = hashlib.md5(content).hexdigest()
        
        # Get function name for the cache key
        func_name = extraction_func.__name__
        
        # Create cache key
        cache_key = f"{content_hash}_{func_name}"
        
        # Check if result is in cache
        current_time = time.time()
        if cache_key in _EXTRACTION_CACHE:
            cached_time, cached_result = _EXTRACTION_CACHE[cache_key]
            
            # Check if the cached result is still valid (not expired)
            if current_time - cached_time < _CACHE_MAX_AGE_SECONDS:
                self.log_info(f"Using cached extraction result for {func_name}")
                return cached_result
        
        # Not in cache or expired, execute the function
        result = extraction_func(self, content, *args, **kwargs)
        
        # Cache the result with timestamp
        _EXTRACTION_CACHE[cache_key] = (current_time, result)
        
        # Prune cache if it grows too large
        if len(_EXTRACTION_CACHE) > _CACHE_MAX_SIZE:
            # Remove the oldest entries
            sorted_keys = sorted(_EXTRACTION_CACHE.keys(), 
                               key=lambda k: _EXTRACTION_CACHE[k][0])
            for old_key in sorted_keys[:len(_EXTRACTION_CACHE) - _CACHE_MAX_SIZE]:
                del _EXTRACTION_CACHE[old_key]
        
        return result
    
    return wrapper


class DocumentProcessor(LoggerMixin):
    """Processor for different document formats."""
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize document processor.
        
        Args:
            cache_enabled: Whether to cache extraction results
        """
        self.cache_enabled = cache_enabled
    
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
        
        # Get detailed file information for better diagnostics
        file_info = get_detailed_file_info(file_content, filename)
        actual_file_type = file_info["detected_type"]
        
        # Log file detection results
        from core.utils.file_detection import log_file_detection
        log_file_detection(file_content, actual_file_type, self.log_file_processing)
        
        self.log_info(f"Extracting text from file of type: {actual_file_type}, size: {file_size} bytes")
        
        try:
            # Content hash for caching
            content_hash = None
            if self.cache_enabled:
                content_hash = hashlib.md5(file_content).hexdigest()
                self.log_debug(f"Content hash: {content_hash}")
            
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
        finally:
            total_time_ms = (time.time() - start_time) * 1000
            self.log_debug(f"Total extraction time: {total_time_ms:.2f}ms")
    
    async def _extract_from_pdf_with_fallback(self, content: bytes) -> str:
        """Extract text from PDF content with fallback mechanism.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If all extraction methods fail
        """
        errors = []
        
        # Try PyMuPDF first if available (more robust)
        if lazy_import_pymupdf():
            try:
                self.log_info("Attempting PDF extraction with PyMuPDF")
                return self._extract_from_pdf_pymupdf(content)
            except Exception as e:
                self.log_warning(f"PyMuPDF extraction failed, falling back to PyPDF2: {str(e)}")
                errors.append(f"PyMuPDF error: {str(e)}")
                # Fall through to PyPDF2
        
        # Use PyPDF2 as fallback or primary method if PyMuPDF is not available
        try:
            self.log_info("Attempting PDF extraction with PyPDF2")
            return self._extract_from_pdf(content)
        except Exception as e:
            self.log_error(f"PyPDF2 extraction failed: {str(e)}")
            errors.append(f"PyPDF2 error: {str(e)}")
            
            # All extraction methods failed
            error_msg = "All PDF extraction methods failed"
            self.log_error(error_msg)
            raise DocumentProcessingError(
                message=error_msg,
                file_type=PDF_MIME_TYPE,
                file_size=len(content),
                details={"errors": errors}
            )
    
    @document_extraction_cache
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
    
    @document_extraction_cache
    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF content using PyPDF2.
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails completely
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
            failed_pages = []
            
            self.log_file_processing("pdf_structure", PDF_MIME_TYPE, file_size, 
                              {"pages": num_pages})
            
            # Process each page with detailed logging and recovery
            for i, page in enumerate(reader.pages):
                page_start_time = time.time()
                try:
                    page_text = page.extract_text()
                    page_time_ms = (time.time() - page_start_time) * 1000
                    
                    self.log_file_processing("pdf_page_extraction", PDF_MIME_TYPE, file_size, 
                                      {"page": i+1, "chars": len(page_text), 
                                       "time_ms": page_time_ms})
                    
                    if page_text and page_text.strip():  # Only add non-empty pages
                        text_parts.append(page_text)
                        successful_pages += 1
                    else:
                        self.log_warning(f"Page {i+1} extracted successfully but contains no text")
                        failed_pages.append(i+1)
                except Exception as page_error:
                    self.log_file_error(f"Error extracting text from page {i+1}", 
                                 PDF_MIME_TYPE, file_size, page_error)
                    failed_pages.append(i+1)
                    # Continue with other pages
            
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
                    failed_pages_str = ", ".join(map(str, failed_pages))
                    self.log_warning(
                        f"Partial PDF extraction: {successful_pages}/{num_pages} pages extracted. "
                        f"Failed pages: {failed_pages_str}"
                    )
                
                return cleaned_text
            else:
                # No text extracted, but don't fail completely
                self.log_warning("No text extracted from PDF with PyPDF2")
                return "[Document contains no extractable text]"
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            self.log_performance("pdf_extraction", total_time_ms, False, {"error": str(e)})
            self.log_file_error("Error processing PDF", PDF_MIME_TYPE, file_size, e)
            
            # Create details dict for more context
            details = {
                "extraction_method": "PyPDF2",
                "error_type": type(e).__name__
            }
            
            # Provide more specific error messages based on the exception
            error_message = str(e).lower()
            if "file has not been decrypted" in error_message or "password" in error_message:
                raise DocumentProcessingError(
                    message="PDF is encrypted and cannot be processed. Please remove the password and try again.",
                    file_type=PDF_MIME_TYPE,
                    file_size=file_size,
                    details=details
                )
            elif "eof marker not found" in error_message:
                raise DocumentProcessingError(
                    message="PDF file is incomplete or corrupted. Please verify the file and try again.",
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
    
    @document_extraction_cache
    def _extract_from_docx(self, content: bytes) -> str:
        """Extract text from DOCX content.
        
        Args:
            content: DOCX file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If extraction fails
        """
        start_time = time.time()
        file_size = len(content)
        
        self.log_file_processing("docx_extraction_start", DOCX_MIME_TYPE, file_size)
        
        docx_file = io.BytesIO(content)
        try:
            doc = docx.Document(docx_file)
            
            # Extract text from paragraphs with error recovery
            paragraphs = []
            paragraph_errors = 0
            
            for i, para in enumerate(doc.paragraphs):
                try:
                    paragraphs.append(para.text)
                except Exception as para_error:
                    self.log_warning(f"Error extracting paragraph {i}: {str(para_error)}")
                    paragraph_errors += 1
                    # Continue with other paragraphs
            
            self.log_debug(f"Extracted {len(paragraphs)} paragraphs from DOCX (errors: {paragraph_errors})")
            
            # Extract text from tables if any
            table_text = []
            table_errors = 0
            
            for i, table in enumerate(doc.tables):
                try:
                    for row in table.rows:
                        try:
                            row_text = [cell.text for cell in row.cells]
                            table_text.append(" | ".join(row_text))
                        except Exception as row_error:
                            self.log_warning(f"Error extracting row in table {i}: {str(row_error)}")
                            # Continue with other rows
                except Exception as table_error:
                    self.log_warning(f"Error extracting table {i}: {str(table_error)}")
                    table_errors += 1
                    # Continue with other tables
            
            if table_text:
                self.log_debug(
                    f"Extracted text from {len(doc.tables)} tables "
                    f"(errors: {table_errors})"
                )
                
            # Combine all text
            all_text = paragraphs + table_text
            
            # Check if we have any content
            if not all_text:
                self.log_warning("No text extracted from DOCX")
                return "[Document contains no extractable text]"
                
            text = "\n".join(all_text)
            
            # Clean and return text
            cleaned_text = self._clean_text(text)
            
            # Log performance and results
            total_time_ms = (time.time() - start_time) * 1000
            self.log_performance("docx_extraction", total_time_ms, True, 
                          {"paragraphs": len(paragraphs), "tables": len(doc.tables), 
                           "chars": len(cleaned_text),
                           "paragraph_errors": paragraph_errors,
                           "table_errors": table_errors})
            
            # Log sample for verification
            sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
            self.log_debug(f"Extracted text sample: {sample}")
            
            return cleaned_text
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
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
    
    @document_extraction_cache
    def _extract_from_pdf_pymupdf(self, content: bytes) -> str:
        """Extract text from PDF content using PyMuPDF (more robust than PyPDF2).
        
        Args:
            content: PDF file content
            
        Returns:
            str: Extracted text
            
        Raises:
            DocumentProcessingError: If PyMuPDF extraction fails completely
        """
        # Ensure PyMuPDF is available
        if not lazy_import_pymupdf():
            raise DocumentProcessingError(
                message="PyMuPDF not available for PDF extraction", 
                file_type=PDF_MIME_TYPE
            )
            
        start_time = time.time()
        file_size = len(content)
        self.log_file_processing("pdf_pymupdf_extraction_start", PDF_MIME_TYPE, file_size)
        
        try:
            # Open PDF from memory buffer
            pdf_file = io.BytesIO(content)
            doc = fitz.open(stream=pdf_file, filetype="pdf")
            
            text_parts = []
            num_pages = len(doc)
            successful_pages = 0
            failed_pages = []
            
            # Process each page with error recovery
            for i in range(num_pages):
                page_start_time = time.time()
                page_extracted = False
                
                # Try multiple extraction methods for each page with recovery
                extraction_methods = [
                    {"name": "text", "get_text_param": "text"},
                    {"name": "blocks", "get_text_param": "blocks"},
                    {"name": "html", "get_text_param": "html"},
                    {"name": "dict", "get_text_param": "dict"}
                ]
                
                page = None
                try:
                    page = doc[i]
                except Exception as page_access_error:
                    self.log_file_error(f"PyMuPDF: Error accessing page {i+1}",
                                PDF_MIME_TYPE, file_size, page_access_error)
                    failed_pages.append(i+1)
                    continue
                
                # Try each extraction method in order until one succeeds
                for method in extraction_methods:
                    if page_extracted:
                        break
                        
                    method_name = method["name"]
                    get_text_param = method["get_text_param"]
                    
                    try:
                        if method_name == "blocks":
                            # Special handling for blocks method
                            blocks = page.get_text("blocks")
                            page_text = "\n".join([b[4] for b in blocks if isinstance(b[4], str)])
                        elif method_name == "dict":
                            # Special handling for dict method
                            text_dict = page.get_text("dict")
                            blocks = text_dict.get("blocks", [])
                            text_blocks = []
                            for block in blocks:
                                if "lines" in block:
                                    for line in block["lines"]:
                                        if "spans" in line:
                                            for span in line["spans"]:
                                                if "text" in span:
                                                    text_blocks.append(span["text"])
                            page_text = "\n".join(text_blocks)
                        else:
                            # Standard text extraction
                            page_text = page.get_text(get_text_param)
                            
                        page_time_ms = (time.time() - page_start_time) * 1000
                        
                        self.log_file_processing(
                            f"pdf_pymupdf_page_extraction_{method_name}", 
                            PDF_MIME_TYPE, file_size,
                            {"page": i+1, "chars": len(page_text), "time_ms": page_time_ms}
                        )
                        
                        if page_text and page_text.strip():
                            text_parts.append(page_text)
                            successful_pages += 1
                            page_extracted = True
                            self.log_debug(f"Successfully extracted page {i+1} using {method_name} method")
                            break
                            
                    except Exception as method_error:
                        self.log_warning(
                            f"PyMuPDF: {method_name} extraction failed for page {i+1}: {str(method_error)}"
                        )
                        # Continue to next method
                
                # If all extraction methods failed for this page
                if not page_extracted:
                    self.log_warning(f"PyMuPDF: All extraction methods failed for page {i+1}")
                    failed_pages.append(i+1)
            
            # Close the document
            doc.close()
            
            # Calculate success rate
            success_rate = successful_pages / num_pages if num_pages > 0 else 0
            
            # Combine all text
            if text_parts:
                combined_text = "\n\n".join(text_parts)
                cleaned_text = self._clean_text(combined_text)
                
                total_time_ms = (time.time() - start_time) * 1000
                self.log_performance("pdf_pymupdf_extraction", total_time_ms, True,
                              {"pages": num_pages, "successful_pages": successful_pages,
                               "success_rate": f"{success_rate:.2f}", "chars": len(cleaned_text)})
                
                # Log sample
                sample = cleaned_text[:200] + "..." if len(cleaned_text) > 200 else cleaned_text
                self.log_debug(f"PyMuPDF extracted text sample: {sample}")
                
                # Warn if partial extraction
                if success_rate < 1.0:
                    failed_pages_str = ", ".join(map(str, failed_pages))
                    self.log_warning(
                        f"Partial PDF extraction with PyMuPDF: {successful_pages}/{num_pages} pages extracted. "
                        f"Failed pages: {failed_pages_str}"
                    )
                
                return cleaned_text
            else:
                # No text extracted, but don't fail completely
                self.log_warning("No text extracted from PDF with PyMuPDF")
                return "[Document contains no extractable text]"
                
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
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
