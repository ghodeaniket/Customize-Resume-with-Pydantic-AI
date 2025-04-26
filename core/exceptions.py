"""Custom exceptions for Resume Customizer."""
from typing import Any, Dict, List, Optional, Union


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
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(ResumeCustomizerError):
    """Exception raised for configuration errors."""
    
    def __init__(
        self, 
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=500, details=details)


class ServiceError(ResumeCustomizerError):
    """Exception raised for service-level errors."""
    
    def __init__(
        self, 
        message: str = "Service error",
        service_name: Optional[str] = None,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if service_name:
            details["service_name"] = service_name
        super().__init__(message=message, status_code=status_code, details=details)


# AIProviderError is now a subclass of ServiceError
class AIProviderError(ServiceError):
    """Exception raised for AI provider errors."""
    
    def __init__(
        self, 
        message: str = "AI provider error",
        provider_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        service_name = provider_name or "AI Provider"
        super().__init__(message=message, service_name=service_name, status_code=502, details=details)


# DocumentProcessingError is now more specific
class DocumentProcessingError(ResumeCustomizerError):
    """Exception raised for document processing errors."""
    
    def __init__(
        self, 
        message: str = "Document processing error",
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if file_type:
            details["file_type"] = file_type
        if file_size is not None:
            details["file_size"] = file_size
            
        super().__init__(message=message, status_code=400, details=details)


# ValidationError remains largely unchanged
class ValidationError(ResumeCustomizerError):
    """Exception raised for validation errors."""
    
    def __init__(
        self, 
        message: str = "Validation error",
        fields: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if fields:
            details["fields"] = fields
            
        super().__init__(message=message, status_code=422, details=details)


# TokenLimitExceededError is now more streamlined
class TokenLimitExceededError(ValidationError):
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
        super().__init__(message=message, details=details)
        # Override status code from ValidationError
        self.status_code = 413
