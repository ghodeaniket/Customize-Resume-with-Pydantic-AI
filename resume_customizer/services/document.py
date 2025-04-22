"""Document processing service.

This module contains document processing functionality for resume and job documents.
"""

import os
from typing import List, Optional

from fastapi import UploadFile
from loguru import logger

from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import DocumentProcessingError


class DocumentService:
    """Service for document processing.
    
    This service handles document processing for resume and job documents,
    including text extraction and validation.
    """
    
    async def validate_file(self, file: UploadFile) -> None:
        """Validate an uploaded file.
        
        Args:
            file: The uploaded file
            
        Raises:
            DocumentProcessingError: If the file is invalid
        """
        # Check if the file exists
        if not file:
            raise DocumentProcessingError("No file provided")
        
        # Check if the file has content
        if not file.file:
            raise DocumentProcessingError("File is empty")
        
        # Check the file size
        try:
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)  # Reset file position
            
            if file_size > settings.MAX_UPLOAD_SIZE:
                max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
                raise DocumentProcessingError(
                    f"File size exceeds maximum allowed size of {max_size_mb:.1f}MB"
                )
        except Exception as e:
            raise DocumentProcessingError(f"Error checking file size: {str(e)}")
        
        # Check the file extension
        file_ext = file.filename.split(".")[-1].lower() if file.filename else ""
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            allowed_ext_str = ", ".join(settings.ALLOWED_EXTENSIONS)
            raise DocumentProcessingError(
                f"File type not allowed. Allowed types: {allowed_ext_str}"
            )
    
    async def extract_text_from_file(self, file: UploadFile) -> str:
        """Extract text from an uploaded file.
        
        For Phase 1, this is a simple implementation that reads the file as text.
        In Phase 2, we'll add support for PDF and DOCX files.
        
        Args:
            file: The uploaded file
            
        Returns:
            str: The extracted text
            
        Raises:
            DocumentProcessingError: If there's an error extracting text
        """
        try:
            logger.info(f"Extracting text from file: {file.filename}")
            
            # For Phase 1, we'll assume all files are plain text
            content = await file.read()
            text = content.decode("utf-8")
            
            if not text:
                raise ValueError("Extracted text is empty")
            
            logger.debug(f"Successfully extracted {len(text)} characters from file")
            return text
            
        except UnicodeDecodeError:
            error_msg = "File encoding not supported or not a text file"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg, document_type=file.filename)
            
        except Exception as e:
            error_msg = f"Failed to extract text from file: {str(e)}"
            logger.error(error_msg)
            raise DocumentProcessingError(error_msg, document_type=file.filename)
    
    async def clean_text(self, text: str) -> str:
        """Clean and normalize text.
        
        Args:
            text: The text to clean
            
        Returns:
            str: The cleaned text
        """
        # For Phase 1, just do basic cleaning
        return text.strip()
    
    def get_allowed_extensions(self) -> List[str]:
        """Get the list of allowed file extensions.
        
        Returns:
            List[str]: The allowed file extensions
        """
        return settings.ALLOWED_EXTENSIONS
    
    def get_max_upload_size(self) -> int:
        """Get the maximum upload size in bytes.
        
        Returns:
            int: The maximum upload size in bytes
        """
        return settings.MAX_UPLOAD_SIZE


# Instantiate the service
document_service = DocumentService()
