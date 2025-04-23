"""Health check endpoints for the Resume Customizer API.

This module provides endpoints for monitoring the health and status of the API.
"""

import platform
import sys
import time
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
import psutil

from resume_customizer import __version__
from resume_customizer.api.dependencies import get_http_client, verify_api_key
from resume_customizer.api.responses import HealthCheckResponse
from resume_customizer.core.config import settings
from resume_customizer.core.exceptions import ResumeCustomizerException
from resume_customizer.services.cache import get_cache_provider


# Create router
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    description="Check if the API is up and running."
)
async def health_check():
    """Basic health check endpoint.
    
    Returns:
        HealthCheckResponse: Service health status
    """
    return HealthCheckResponse(
        status="ok",
        version=__version__
    )


@router.get(
    "/health/detail",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    description="Get detailed information about the API's health and environment."
)
async def detailed_health_check(
    http_client: httpx.AsyncClient = Depends(get_http_client),
    api_key: str = Depends(verify_api_key)
):
    """Detailed health check endpoint.
    
    This endpoint requires authentication and provides more detailed information
    about the API's health and environment.
    
    Args:
        http_client: The HTTP client for making requests
        api_key: The API key for authentication
        
    Returns:
        Dict: Detailed health information
    """
    try:
        # Get system information
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
            "cpus": psutil.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
                "available": psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total / (1024 * 1024 * 1024),  # GB
                "free": psutil.disk_usage('/').free / (1024 * 1024 * 1024),  # GB
                "percent": psutil.disk_usage('/').percent
            }
        }
        
        # Test cache connectivity
        cache_provider = get_cache_provider()
        cache_status = "ok"
        cache_type = cache_provider.__class__.__name__
        
        try:
            test_key = f"health_check_{time.time()}"
            await cache_provider.set(test_key, "test_value", 10)
            test_value = await cache_provider.get(test_key)
            
            if test_value != "test_value":
                cache_status = "error: invalid test value"
        except Exception as e:
            cache_status = f"error: {str(e)}"
        
        # Gather health information
        health_info = {
            "status": "ok",
            "version": __version__,
            "environment": settings.ENVIRONMENT if hasattr(settings, "ENVIRONMENT") else "development",
            "uptime": time.time() - psutil.boot_time(),
            "system": system_info,
            "settings": {
                "debug": settings.DEBUG,
                "upload_directory": settings.UPLOAD_DIRECTORY,
                "max_upload_size": settings.MAX_UPLOAD_SIZE,
                "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                "enable_cache": settings.ENABLE_CACHE,
                "cache_ttl": settings.CACHE_TTL,
                "log_level": settings.LOG_LEVEL
            },
            "services": {
                "cache": {
                    "status": cache_status,
                    "type": cache_type
                }
            }
        }
        
        return health_info
        
    except Exception as e:
        logger.exception(f"Health check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/ready",
    response_model=Dict,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Check if the API is ready to handle requests."
)
async def readiness_probe():
    """Readiness probe endpoint.
    
    This endpoint checks if the API is ready to handle requests by verifying
    that all required dependencies are available.
    
    Returns:
        Dict: Readiness status
    """
    # Check if upload directory exists and is writable
    import os
    
    try:
        os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
        test_file_path = os.path.join(settings.UPLOAD_DIRECTORY, ".readiness_test")
        
        with open(test_file_path, "w") as f:
            f.write("test")
        
        os.remove(test_file_path)
        upload_dir_status = "ok"
    except Exception as e:
        upload_dir_status = f"error: {str(e)}"
    
    # Return readiness status
    return {
        "status": "ready" if upload_dir_status == "ok" else "not ready",
        "checks": {
            "upload_directory": upload_dir_status
        }
    }
