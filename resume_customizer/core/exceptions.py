"""Custom exception types for the Resume Customizer application."""

from typing import Any, Dict, Optional


class ResumeCustomizerException(Exception):
    """Base exception for all Resume Customizer exceptions."""
    
    def __init__(self, message: str):
        """Initialize the exception with a message.
        
        Args:
            message: The error message.
        """
        self.message = message
        super().__init__(self.message)


class ConfigurationError(ResumeCustomizerException):
    """Raised when there's an error in the application configuration."""
    
    def __init__(self, message: str):
        """Initialize the exception with a message.
        
        Args:
            message: The error message.
        """
        super().__init__(f"Configuration error: {message}")


class AgentError(ResumeCustomizerException):
    """Raised when there's an error in agent execution."""
    
    def __init__(self, message: str, agent_name: str):
        """Initialize the exception with a message and agent name.
        
        Args:
            message: The error message.
            agent_name: The name of the agent that raised the error.
        """
        self.agent_name = agent_name
        super().__init__(f"Agent error ({agent_name}): {message}")


class DocumentProcessingError(ResumeCustomizerException):
    """Raised when there's an error processing a document."""
    
    def __init__(self, message: str, document_type: Optional[str] = None):
        """Initialize the exception with a message and document type.
        
        Args:
            message: The error message.
            document_type: The type of document that failed to process.
        """
        self.document_type = document_type
        doc_info = f" for {document_type}" if document_type else ""
        super().__init__(f"Document processing error{doc_info}: {message}")


class AIProviderError(ResumeCustomizerException):
    """Raised when there's an error with the AI provider (e.g., OpenRouter)."""
    
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None):
        """Initialize the exception with a message, provider name, and status code.
        
        Args:
            message: The error message.
            provider: The name of the AI provider.
            status_code: The HTTP status code if available.
        """
        self.provider = provider
        self.status_code = status_code
        status_info = f" (Status Code: {status_code})" if status_code else ""
        super().__init__(f"{provider} error{status_info}: {message}")


class ValidationError(ResumeCustomizerException):
    """Raised when there's a validation error in user input."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        """Initialize the exception with a message and error details.
        
        Args:
            message: The error message.
            errors: A dictionary containing validation error details.
        """
        self.errors = errors or {}
        super().__init__(f"Validation error: {message}")
