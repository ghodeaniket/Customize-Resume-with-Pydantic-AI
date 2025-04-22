"""Document processor for the Resume Customizer application.

This module contains tools for processing and extracting content from documents.
"""

import os
from typing import Dict, List, Optional

from fastapi import UploadFile
from loguru import logger

from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import DocumentProcessingError


class DocumentProcessor:
    """Document processor for handling various file types.
    
    This class provides methods for extracting text from different document types
    like PDF and DOCX files.
    """
    
    async def extract_text(self, file: UploadFile) -> str:
        """Extract text from a document file.
        
        This is a placeholder implementation for Phase 1. In Phase 2, this will
        be implemented with proper PDF and DOCX handling.
        
        Args:
            file: The document file
            
        Returns:
            str: The extracted text
            
        Raises:
            DocumentProcessingError: If there's an error extracting text
        """
        try:
            logger.info(f"Extracting text from {file.filename}")
            
            # Get file extension
            file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
            
            # For Phase 1, just read as text
            # In Phase 2, we'll add proper support for different file types
            content = await file.read()
            text = content.decode("utf-8")
            
            # Reset the file pointer for potential future use
            await file.seek(0)
            
            if not text.strip():
                raise ValueError("Extracted text is empty")
                
            logger.debug(f"Successfully extracted {len(text)} characters from {file.filename}")
            return text
            
        except UnicodeDecodeError:
            error_msg = f"Could not decode {file.filename} as text. Phase 2 will add proper file type support."
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg, document_type=file_ext)
            
        except Exception as e:
            error_msg = f"Error extracting text from {file.filename}: {str(e)}"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg, document_type=file_ext)
    
    def is_supported_file_type(self, filename: str) -> bool:
        """Check if a file type is supported.
        
        Args:
            filename: The filename to check
            
        Returns:
            bool: True if the file type is supported, False otherwise
        """
        if not filename:
            return False
        
        # Get file extension
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        # Check if extension is allowed
        return file_ext in settings.ALLOWED_EXTENSIONS
    
    def get_mime_type(self, filename: str) -> str:
        """Get the MIME type for a file.
        
        Args:
            filename: The filename
            
        Returns:
            str: The MIME type
        """
        # Simple mapping for common file types
        mime_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
            "txt": "text/plain",
            "json": "application/json",
            "html": "text/html",
            "csv": "text/csv",
        }
        
        # Get file extension
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        # Return MIME type or default
        return mime_map.get(file_ext, "application/octet-stream")


# Instantiate the processor
document_processor = DocumentProcessor()
