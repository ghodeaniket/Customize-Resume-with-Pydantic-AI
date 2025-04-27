"""API utility functions."""
import logging
from typing import Dict, List, Optional, Tuple, Union, Any

from fastapi import HTTPException, UploadFile, status

from core.utils.file_detection import (
    detect_file_type, log_file_detection, get_detailed_file_info, 
    OCTET_STREAM, PDF_MIME_TYPE, DOCX_MIME_TYPE, TEXT_MIME_TYPE
)
from core.logging import LoggerMixin
from core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


class APIUtils(LoggerMixin):
    """Utility functions for API endpoints."""
    
    @staticmethod
    async def process_uploaded_file(file: UploadFile) -> Tuple[bytes, str]:
        """Process an uploaded file and return content and type.
        
        Args:
            file: Uploaded file
            
        Returns:
            tuple: (file_content, file_type)
            
        Raises:
            HTTPException: If file is empty or unsupported
        """
        logger.info(f"Processing uploaded file: {file.filename}, content_type: {file.content_type}")
        
        # Read file content
        try:
            file_content = await file.read()
        except Exception as e:
            logger.error(f"Failed to read uploaded file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": f"Failed to read file: {str(e)}"}
            )
            
        if not file_content or len(file_content) == 0:
            logger.error("Empty file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Empty file uploaded"}
            )
        
        # Get detailed file information for better diagnostics
        file_info = get_detailed_file_info(file_content, file.filename)
        file_type = file_info["detected_type"]
        
        # Validate the detected file type is supported
        supported_types = [PDF_MIME_TYPE, DOCX_MIME_TYPE, TEXT_MIME_TYPE]
        if file_type not in supported_types and file_type != OCTET_STREAM:
            logger.warning(f"Unsupported file type detected: {file_type}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "message": f"Unsupported file type: {file_type}",
                    "supported_types": supported_types
                }
            )
        
        # Log file detection results
        logger.info(f"Detected file type: {file_type}, size: {len(file_content)} bytes")
        
        # Log detailed file information
        try:
            utils = APIUtils()
            log_file_detection(file_content, file_type, utils.log_file_processing)
            
            # Log additional diagnostics for debugging
            if file_type == OCTET_STREAM:
                utils.log_warning(
                    f"File could not be identified, using generic binary type. "
                    f"Filename: {file.filename}, Content-Type: {file.content_type}"
                )
        except Exception as e:
            logger.warning(f"Error logging file detection: {str(e)}")
        
        return file_content, file_type

    @staticmethod
    async def extract_text_safely(
        file_content: bytes, 
        file_type: str, 
        filename: Optional[str] = None,
        document_processor = None
    ) -> str:
        """Extract text from a file with enhanced error handling.
        
        Args:
            file_content: File content bytes
            file_type: Detected MIME type
            filename: Original filename (optional)
            document_processor: DocumentProcessor instance (optional)
            
        Returns:
            str: Extracted text content
            
        Raises:
            HTTPException: If text extraction fails
        """
        from infrastructure.document_processor import DocumentProcessor
        
        # Use provided processor or create a new one
        processor = document_processor or DocumentProcessor()
        
        try:
            return await processor.extract_text_from_bytes(file_content, file_type, filename)
        except DocumentProcessingError as e:
            error_message = str(e)
            logger.error(f"Document processing error: {error_message}")
            
            # Create a user-friendly error message
            if "PDF is encrypted" in error_message:
                friendly_message = "The PDF is password-protected. Please remove the password and try again."
            elif "corrupted" in error_message:
                friendly_message = "The file appears to be corrupted. Please check the file and try again."
            elif "No text could be extracted" in error_message:
                friendly_message = "No text could be extracted from the document. The file may be scanned or contain only images."
            else:
                friendly_message = f"Failed to extract text from document: {error_message}"
                
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": friendly_message}
            )
        except Exception as e:
            logger.error(f"Unexpected error extracting text: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": "An unexpected error occurred while processing the file."}
            )


def structure_response(data: Any, extra_metadata: Optional[Dict] = None) -> Dict:
    """Structure API response with consistent format.
    
    Args:
        data: Main response data
        extra_metadata: Additional metadata to include
        
    Returns:
        dict: Structured response with data and metadata
    """
    response = {
        "data": data,
        "metadata": extra_metadata or {}
    }
    
    return response
