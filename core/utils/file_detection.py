"""File type detection utilities."""
import logging
from typing import Dict, Optional, Tuple, Any, Callable

logger = logging.getLogger(__name__)

# Common MIME types for document processing
PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TEXT_MIME_TYPE = "text/plain"
OCTET_STREAM = "application/octet-stream"

# File signatures (magic numbers)
PDF_SIGNATURE = b'%PDF'
DOCX_SIGNATURE = b'PK'


def detect_file_type(
    file_content: bytes, 
    content_type: Optional[str] = None,
    filename: Optional[str] = None
) -> str:
    """Detect file type using a deterministic approach by prioritizing file signatures.
    
    Args:
        file_content: Binary content of the file
        content_type: MIME type from request (optional)
        filename: Original filename (optional)
        
    Returns:
        str: Detected MIME type
    """
    if not file_content or len(file_content) == 0:
        logger.warning("Empty file content")
        return OCTET_STREAM
    
    # 1. First priority: Check file signatures (most reliable)
    # Check for PDF signature
    if len(file_content) >= 4 and file_content[:4] == PDF_SIGNATURE:
        logger.info("PDF signature detected")
        return PDF_MIME_TYPE
        
    # Check for DOCX/ZIP signature (PK header)
    if len(file_content) >= 2 and file_content[:2] == DOCX_SIGNATURE:
        logger.info("DOCX/ZIP signature detected")
        return DOCX_MIME_TYPE
    
    # 2. Second priority: Check for text content
    try:
        # Try to decode a sample of the content as UTF-8
        file_content[:1024].decode('utf-8')
        logger.info("Text content detected")
        return TEXT_MIME_TYPE
    except UnicodeDecodeError:
        pass
    
    # 3. Third priority: Use file extension if available
    if filename:
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        extension_type_map = {
            'pdf': PDF_MIME_TYPE,
            'docx': DOCX_MIME_TYPE,
            'doc': "application/msword",
            'txt': TEXT_MIME_TYPE,
            'rtf': "application/rtf"
        }
        
        if extension in extension_type_map:
            mime_type = extension_type_map[extension]
            logger.info(f"Using file extension for type detection: {mime_type}")
            return mime_type
    
    # 4. Fourth priority: Use provided content type if available
    if content_type and isinstance(content_type, str) and content_type.strip():
        normalized_content_type = content_type.strip().lower()
        if any(type_str in normalized_content_type for type_str in 
               ["pdf", "docx", "msword", "text/plain", "rtf"]):
            logger.info(f"Using provided content type: {content_type}")
            return content_type
    
    # 5. Fallback to generic binary
    logger.info("Using fallback octet-stream type")
    return OCTET_STREAM


def log_file_detection(
    file_content: bytes, 
    detected_type: str, 
    logger_func: Callable[[str, str, int, Optional[Dict[str, Any]]], None]
) -> None:
    """Log file detection results in a standardized way.
    
    Args:
        file_content: Binary content of the file
        detected_type: Detected MIME type
        logger_func: A logging function that takes action, file_type, file_size, and extra params
    """
    file_size = len(file_content) if file_content else 0
    
    # Log the detection result based on the type
    if detected_type == PDF_MIME_TYPE:
        hex_header = " ".join([f"{b:02x}" for b in file_content[:20]]) if file_content else ""
        logger_func("signature_detection", PDF_MIME_TYPE, file_size, 
                   {"signature": "PDF", "header": hex_header})
    
    elif detected_type == DOCX_MIME_TYPE:
        hex_header = " ".join([f"{b:02x}" for b in file_content[:20]]) if file_content else ""
        logger_func("signature_detection", DOCX_MIME_TYPE, file_size,
                   {"signature": "PK", "header": hex_header})
    
    elif detected_type == TEXT_MIME_TYPE:
        sample = ""
        try:
            sample = file_content[:1024].decode('utf-8')[:50] if file_content else ""
        except UnicodeDecodeError:
            pass
            
        logger_func("text_detection", TEXT_MIME_TYPE, file_size,
                   {"sample": sample})
    
    else:
        # Log the first bytes for unknown type
        if file_content and len(file_content) > 0:
            hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
            logger.debug(f"Unknown file type. Header bytes: {hex_header}")
        
        logger_func("fallback_detection", OCTET_STREAM, file_size)


def get_file_extension(mime_type: str) -> str:
    """Get the appropriate file extension for a MIME type.
    
    Args:
        mime_type: MIME type
        
    Returns:
        str: File extension including the dot
    """
    extension_map = {
        PDF_MIME_TYPE: ".pdf",
        DOCX_MIME_TYPE: ".docx",
        "application/msword": ".doc",
        TEXT_MIME_TYPE: ".txt",
        "application/rtf": ".rtf"
    }
    
    return extension_map.get(mime_type, "")
