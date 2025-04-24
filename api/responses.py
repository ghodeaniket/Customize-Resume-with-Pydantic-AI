"""API response models."""
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """API error response model."""
    
    message: str = Field(description="Error message")
    status_code: int = Field(description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(
        description="Additional error details",
        default=None
    )


class HealthCheckResponse(BaseModel):
    """API health check response model."""
    
    status: str = Field(description="Service status")
    version: str = Field(description="API version")
    uptime: float = Field(description="Service uptime in seconds")


class TokenUsage(BaseModel):
    """Token usage statistics."""
    
    requests: int = Field(description="Number of requests made to the AI provider")
    request_tokens: int = Field(description="Number of tokens in the requests")
    response_tokens: int = Field(description="Number of tokens in the responses")
    total_tokens: int = Field(description="Total number of tokens used")
