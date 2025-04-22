"""API dependencies for the Resume Customizer application.

This module contains FastAPI dependencies used across the API.
"""

from typing import Generator

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from resume_customizer.core.config import settings
from resume_customizer.core.logging import app_logger as logger


# API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Depends(api_key_header)
) -> str:
    """Verify the API key.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        str: The verified API key
        
    Raises:
        HTTPException: If the API key is invalid
    """
    # In a production environment, this would validate against a database
    # or external auth service. For this MVP, we're using a simple check.
    if not api_key or api_key != settings.SECRET_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return api_key


async def get_http_client() -> Generator[httpx.AsyncClient, None, None]:
    """Get an HTTP client.
    
    Yields:
        AsyncClient: An HTTP client for making requests
    """
    async with httpx.AsyncClient() as client:
        logger.debug("Created new HTTP client")
        yield client
