"""API utility functions."""
import logging
from typing import Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, UploadFile, status

from core.utils.file_detection import detect_file_type, log_file_detection, OCTET_STREAM
from core.logging import LoggerMixin

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
            HTTPException: If file is empty
        """
        logger.info(f"Processing uploaded file: {file.filename}, content_type: {file.content_type}")
        
        # Read file content
        file_content = await file.read()
        if not file_content or len(file_content) == 0:
            logger.error("Empty file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Empty file uploaded"}
            )
        
        # Detect file type
        file_type = detect_file_type(file_content, file.content_type, file.filename)
        logger.info(f"Detected file type: {file_type}, size: {len(file_content)} bytes")
        
        # Log detailed file information
        try:
            utils = APIUtils()
            log_file_detection(file_content, file_type, utils.log_file_processing)
        except Exception as e:
            logger.warning(f"Error logging file detection: {str(e)}")
        
        return file_content, file_type


def structure_response(data: any, extra_metadata: Optional[Dict] = None) -> Dict:
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
