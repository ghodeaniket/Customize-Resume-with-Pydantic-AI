"""Metrics endpoints for the Resume Customizer API.

This module provides endpoints for monitoring API usage and performance.
"""

import time
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from resume_customizer.api.dependencies import verify_api_key
from resume_customizer.api.middleware import get_request_metrics
from resume_customizer.core.logging import app_logger as logger


# Create router
router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    response_model=Dict[str, Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="API usage metrics",
    description="Get metrics on API endpoint usage and performance."
)
async def get_metrics(
    api_key: str = Depends(verify_api_key)
):
    """Get API usage metrics.
    
    This endpoint requires authentication and provides metrics on API
    endpoint usage and performance.
    
    Args:
        api_key: The API key for authentication
        
    Returns:
        Dict: API usage metrics
    """
    try:
        # Get the metrics
        metrics = await get_request_metrics()
        
        # Add a timestamp
        result = {
            "timestamp": time.time(),
            "metrics": metrics
        }
        
        return result
        
    except Exception as e:
        logger.exception(f"Error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting metrics: {str(e)}"
        )


@router.delete(
    "/metrics/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset API metrics",
    description="Reset the collected API usage metrics."
)
async def reset_metrics(
    api_key: str = Depends(verify_api_key)
):
    """Reset API usage metrics.
    
    This endpoint requires authentication and resets the collected API
    usage metrics.
    
    Args:
        api_key: The API key for authentication
    """
    try:
        # Get the metrics dict
        metrics = await get_request_metrics()
        
        # Clear all metrics
        metrics.clear()
        
        logger.info("API metrics reset")
        
    except Exception as e:
        logger.exception(f"Error resetting metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resetting metrics: {str(e)}"
        )
