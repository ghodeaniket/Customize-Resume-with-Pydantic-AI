"""Custom exceptions for Resume Customizer."""
from typing import Any, Dict, List, Optional, Union


class ResumeCustomizerError(Exception):
    """Base exception for Resume Customizer."""
    
    def __init__(
        self, 
        message: str = "An error occurred",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        
        # Add context to details if provided
        if context:
            self.details["context"] = context
            
        super().__init__(self.message)


class ConfigurationError(ResumeCustomizerError):
    """Exception raised for configuration errors."""
    
    def __init__(
        self, 
        message: str = "Configuration error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=500, details=details, context="configuration")


class ServiceError(ResumeCustomizerError):
    """Exception raised for service-level errors including AI providers and document processing."""
    
    def __init__(
        self, 
        message: str = "Service error",
        service_name: Optional[str] = None,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None
    ):
        if details is None:
            details = {}
        if service_name:
            details["service_name"] = service_name
            
        effective_context = context or service_name or "service"
        super().__init__(message=message, status_code=status_code, details=details, context=effective_context)


# Simplified exceptions - AIProviderError becomes an alias for ServiceError
def AIProviderError(
    message: str = "AI provider error",
    provider_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ServiceError:
    """Create a ServiceError for AI provider issues."""
    service_name = provider_name or "AI Provider"
    return ServiceError(message=message, service_name=service_name, status_code=502, details=details, context="ai_provider")


# DocumentProcessingError becomes an alias for ServiceError with specific defaults
def DocumentProcessingError(
    message: str = "Document processing error",
    file_type: Optional[str] = None,
    file_size: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> ServiceError:
    """Create a ServiceError for document processing issues."""
    if details is None:
        details = {}
    if file_type:
        details["file_type"] = file_type
    if file_size is not None:
        details["file_size"] = file_size
        
    return ServiceError(message=message, service_name="Document Processor", status_code=400, details=details, context="document_processing")


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
            
        super().__init__(message=message, status_code=422, details=details, context="validation")


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
