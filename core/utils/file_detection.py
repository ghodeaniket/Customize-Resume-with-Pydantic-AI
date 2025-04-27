"""File type detection utilities."""
import logging
import os
from typing import Dict, Optional, Tuple, Any, Callable, List

logger = logging.getLogger(__name__)

# Common MIME types for document processing
PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TEXT_MIME_TYPE = "text/plain"
OCTET_STREAM = "application/octet-stream"

# File signatures (magic numbers)
FILE_SIGNATURES = {
    # PDF signature
    PDF_MIME_TYPE: [(0, b'%PDF')],
    
    # DOCX/ZIP signature (PK header)
    DOCX_MIME_TYPE: [(0, b'PK')],
    
    # Additional formats could be added here
    "application/msword": [(0, b'\xD0\xCF\x11\xE0')],  # DOC file
    "application/rtf": [(0, b'{\\rtf')],  # RTF file
}

# File extensions to MIME types mapping
EXTENSION_MIME_MAP = {
    'pdf': PDF_MIME_TYPE,
    'docx': DOCX_MIME_TYPE,
    'doc': "application/msword",
    'txt': TEXT_MIME_TYPE,
    'rtf': "application/rtf"
}


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
    detected_type = _detect_by_signature(file_content)
    if detected_type:
        logger.info(f"File type detected by signature: {detected_type}")
        return detected_type
    
    # 2. Second priority: Check for text content
    if _is_text_file(file_content):
        logger.info("Text content detected")
        return TEXT_MIME_TYPE
    
    # 3. Third priority: Use file extension if available
    if filename:
        detected_type = _detect_by_extension(filename)
        if detected_type:
            logger.info(f"File type detected by extension: {detected_type}")
            return detected_type
    
    # 4. Fourth priority: Use provided content type if available
    if content_type:
        detected_type = _validate_content_type(content_type)
        if detected_type:
            logger.info(f"Using provided content type: {detected_type}")
            return detected_type
    
    # 5. Fallback to generic binary
    logger.info("Using fallback octet-stream type")
    return OCTET_STREAM


def _detect_by_signature(file_content: bytes) -> Optional[str]:
    """Detect file type by checking known file signatures.
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        str or None: Detected MIME type or None if no match
    """
    # Only check if we have enough content to examine
    if not file_content or len(file_content) < 4:
        return None
        
    # Check each known signature
    for mime_type, signatures in FILE_SIGNATURES.items():
        for offset, signature in signatures:
            if len(file_content) >= offset + len(signature):
                if file_content[offset:offset+len(signature)] == signature:
                    return mime_type
    
    return None


def _is_text_file(file_content: bytes) -> bool:
    """Check if the file content is likely a text file.
    
    Args:
        file_content: Binary content of the file
        
    Returns:
        bool: True if content is likely text, False otherwise
    """
    # Try to decode a sample of the content as UTF-8
    try:
        # Take a larger sample to improve accuracy
        sample_size = min(4096, len(file_content))
        file_content[:sample_size].decode('utf-8')
        
        # Additional check: text files typically have a high percentage of printable ASCII chars
        sample = file_content[:sample_size]
        printable_count = sum(32 <= b <= 126 or b in (9, 10, 13) for b in sample)
        text_ratio = printable_count / sample_size
        
        # More than 90% printable characters suggests a text file
        if text_ratio > 0.9:
            return True
        else:
            logger.debug(f"File has {text_ratio:.2%} printable characters, below threshold for text")
            return False
            
    except UnicodeDecodeError:
        return False


def _detect_by_extension(filename: str) -> Optional[str]:
    """Detect file type based on file extension.
    
    Args:
        filename: Original filename
        
    Returns:
        str or None: Detected MIME type or None if no match
    """
    if not filename or '.' not in filename:
        return None
        
    extension = filename.lower().split('.')[-1]
    return EXTENSION_MIME_MAP.get(extension)


def _validate_content_type(content_type: str) -> Optional[str]:
    """Validate and normalize the provided content type.
    
    Args:
        content_type: MIME type from request
        
    Returns:
        str or None: Validated MIME type or None if invalid
    """
    if not content_type or not isinstance(content_type, str):
        return None
        
    normalized_type = content_type.strip().lower()
    
    # Check if it's one of our known types
    for mime_type in list(FILE_SIGNATURES.keys()) + [TEXT_MIME_TYPE]:
        if mime_type.lower() in normalized_type:
            return mime_type
            
    # Check if it's a known type by extension marker
    for ext_marker in ["pdf", "docx", "msword", "text/plain", "rtf"]:
        if ext_marker in normalized_type:
            for ext, mime in EXTENSION_MIME_MAP.items():
                if ext in ext_marker:
                    return mime
    
    return None


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
    
    # Create a hex header representation for debugging
    hex_header = ""
    if file_content and len(file_content) > 0:
        hex_header = " ".join([f"{b:02x}" for b in file_content[:20]])
    
    # Log based on the detected type
    if detected_type == PDF_MIME_TYPE:
        logger_func("signature_detection", PDF_MIME_TYPE, file_size, 
                   {"signature": "PDF", "header": hex_header})
    
    elif detected_type == DOCX_MIME_TYPE:
        logger_func("signature_detection", DOCX_MIME_TYPE, file_size,
                   {"signature": "PK", "header": hex_header})
    
    elif detected_type == TEXT_MIME_TYPE:
        sample = ""
        try:
            sample = file_content[:1024].decode('utf-8')[:50] if file_content else ""
        except UnicodeDecodeError:
            sample = "<non-decodable content>"
            
        logger_func("text_detection", TEXT_MIME_TYPE, file_size,
                   {"sample": sample, "header": hex_header})
    
    else:
        logger_func("fallback_detection", detected_type, file_size, 
                  {"header": hex_header})


def get_file_extension(mime_type: str) -> str:
    """Get the appropriate file extension for a MIME type.
    
    Args:
        mime_type: MIME type
        
    Returns:
        str: File extension including the dot
    """
    for ext, mime in EXTENSION_MIME_MAP.items():
        if mime == mime_type:
            return f".{ext}"
    
    return ""


def get_detailed_file_info(file_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed diagnostic information about a file.
    
    Args:
        file_content: Binary content of the file
        filename: Original filename (optional)
        
    Returns:
        Dict: Detailed file information
    """
    if not file_content:
        return {"error": "Empty file content"}
    
    # Basic file information
    file_size = len(file_content)
    detected_type = detect_file_type(file_content, None, filename)
    
    # Header analysis
    header_bytes = file_content[:min(32, file_size)]
    hex_header = " ".join([f"{b:02x}" for b in header_bytes])
    ascii_header = "".join([chr(b) if 32 <= b <= 126 else "." for b in header_bytes])
    
    # Text detection test
    is_text = _is_text_file(file_content)
    
    # Extension match check
    ext_matches_content = False
    if filename and "." in filename:
        extension = filename.lower().split(".")[-1]
        detected_by_ext = _detect_by_extension(filename)
        ext_matches_content = detected_by_ext == detected_type
    
    return {
        "file_size": file_size,
        "detected_type": detected_type,
        "filename": filename,
        "header": {
            "hex": hex_header,
            "ascii": ascii_header
        },
        "analysis": {
            "is_text": is_text,
            "extension_matches_content": ext_matches_content if filename else None
        }
    }
