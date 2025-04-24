"""Custom exceptions for Resume Customizer."""
from typing import Any, Dict, List, Optional


class ResumeCustomizerError(Exception):
    """Base exception for Resume Customizer."""
    
    def __init__(
        self, 
        message: str = "An error occurred",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ConfigurationError(ResumeCustomizerError):
    """Exception raised for configuration errors."""
    
    def __init__(
        self, 
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=500, details=details)


class AIProviderError(ResumeCustomizerError):
    """Exception raised for AI provider errors."""
    
    def __init__(
        self, 
        message: str = "AI provider error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=502, details=details)


class DocumentProcessingError(ResumeCustomizerError):
    """Exception raised for document processing errors."""
    
    def __init__(
        self, 
        message: str = "Document processing error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=400, details=details)


class ValidationError(ResumeCustomizerError):
    """Exception raised for validation errors."""
    
    def __init__(
        self, 
        message: str = "Validation error",
        fields: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.fields = fields or []
        super().__init__(message=message, status_code=422, details=details)


class TokenLimitExceededError(ResumeCustomizerError):
    """Exception raised when token limit is exceeded."""
    
    def __init__(
        self, 
        message: str = "Token limit exceeded",
        token_count: int = 0,
        token_limit: int = 0,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        details.update({
            "token_count": token_count,
            "token_limit": token_limit
        })
        super().__init__(message=message, status_code=413, details=details)
