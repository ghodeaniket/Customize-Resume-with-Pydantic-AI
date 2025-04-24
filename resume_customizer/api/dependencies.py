"""API dependencies for the Resume Customizer application.

This module contains FastAPI dependencies used across the API.
"""

from typing import Dict, Generator, Optional

import httpx
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader

from resume_customizer.core.config import settings
from resume_customizer.core.logging import app_logger as logger


# API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


from base64 import b64encode
from hashlib import sha256
import secrets
import hmac

# Dictionary to store valid API keys in memory (replace with a database in production)
# For development only - this would be replaced with a proper database in production
_api_keys = {}

# Function to generate an API key (for testing/development)
def generate_api_key() -> str:
    """Generate a random API key.
    
    Returns:
        str: A random API key
    """
    key = secrets.token_urlsafe(32)
    # Store hashed key
    hashed_key = sha256(key.encode()).hexdigest()
    _api_keys[hashed_key] = {"active": True}
    return key

# Initialize with the SECRET_KEY for development
if settings.DEBUG:
    # In development, initialize with the SECRET_KEY for convenience
    hashed_key = sha256(settings.SECRET_KEY.encode()).hexdigest()
    _api_keys[hashed_key] = {"active": True}
    logger.warning("Using SECRET_KEY as API key in development mode")

async def verify_api_key(
    api_key: str = Depends(api_key_header)
) -> str:
    """Verify the API key using secure comparison.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        str: The verified API key
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if not api_key:
        logger.warning("Missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "APIKey"},
        )
    
    # Hash the provided key
    hashed_key = sha256(api_key.encode()).hexdigest()
    
    # For development/MVP: support the SECRET_KEY for convenience
    if settings.DEBUG and hmac.compare_digest(hashed_key, sha256(settings.SECRET_KEY.encode()).hexdigest()):
        return api_key
    
    # Check against stored keys (constant time comparison to prevent timing attacks)
    if hashed_key in _api_keys and _api_keys[hashed_key].get("active", False):
        return api_key
    
    logger.warning("Invalid API key attempt")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "APIKey"},
    )


async def get_http_client() -> Generator[httpx.AsyncClient, None, None]:
    """Get an HTTP client.
    
    Yields:
        AsyncClient: An HTTP client for making requests
    """
    async with httpx.AsyncClient() as client:
        logger.debug("Created new HTTP client")
        yield client


# Dictionary to store admin credentials in memory (replace with a database in production)
# For development only - this would be replaced with a proper database in production
_admin_users = {}

# In development, initialize with the admin username/password from settings
if settings.DEBUG:
    # Default admin user for development
    admin_username = "admin"
    # In production, this would be securely hashed
    admin_password = settings.SECRET_KEY[:16]  # Use part of SECRET_KEY as temp password in dev
    _admin_users[admin_username] = {
        "active": True,
        "password": admin_password,
        "role": "admin"
    }
    logger.warning(f"Using default admin credentials in development mode: {admin_username}:{admin_password}")


async def get_admin_user(
    authorization: Optional[str] = Header(None)
) -> Dict:
    """Verify admin credentials for access to protected endpoints.
    
    This dependency is used to restrict access to admin-only endpoints like
    metrics and monitoring dashboards.
    
    Args:
        authorization: The Authorization header (Basic auth)
        
    Returns:
        Dict: The admin user details
        
    Raises:
        HTTPException: If the credentials are invalid or missing
    """
    if not authorization:
        logger.warning("Missing Authorization header for admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin credentials required",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Simplified auth for MVP - in production, use proper Basic auth parsing
    # This is just for development convenience
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "basic":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication method",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    try:
        import base64
        decoded = base64.b64decode(parts[1]).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials format",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # Check against stored users
    if (username in _admin_users and
        _admin_users[username].get("active", False) and
        _admin_users[username].get("password") == password and
        _admin_users[username].get("role") == "admin"):
        
        # Return user details without sensitive info
        return {
            "username": username,
            "role": "admin"
        }
    
    logger.warning(f"Invalid admin authentication attempt for user: {username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin credentials",
        headers={"WWW-Authenticate": "Basic"},
    )
