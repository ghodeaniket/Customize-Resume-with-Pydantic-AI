"""Middleware for the Resume Customizer application.

This module contains middleware components for request handling, metrics
collection, logging, and other cross-cutting concerns.
"""

import time
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from resume_customizer.core.config import settings
from resume_customizer.core.logging import app_logger as logger
from resume_customizer.core.metrics import track_api_metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API performance metrics.
    
    This middleware tracks request duration, status codes, and other metrics
    for all API endpoints.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and collect metrics.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The response from the next handler
        """
        # Skip metrics collection if disabled
        if not settings.ENABLE_PERFORMANCE_LOGGING:
            return await call_next(request)
        
        # Get start time
        start_time = time.time()
        
        # Process request
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            raise e
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Skip internal endpoints
            path = request.url.path
            if path.startswith(("/docs", "/redoc", "/openapi.json", "/favicon.ico")):
                return response
            
            # Get endpoint name
            # Strip API prefix and parameters for cleaner grouping
            endpoint = path
            if endpoint.startswith(settings.API_V1_PREFIX):
                endpoint = endpoint[len(settings.API_V1_PREFIX):]
            
            # Remove trailing slash if present
            if endpoint.endswith("/"):
                endpoint = endpoint[:-1]
            
            # Handle root endpoint
            if not endpoint:
                endpoint = "/"
            
            # Collect metrics
            metrics: Dict[str, float] = {
                "response_time": duration_ms,
                "error_count": 1.0 if error else 0.0,
            }
            
            # Add status code if available
            if response:
                metrics["status_code"] = float(response.status_code)
                
                # Group status codes
                metrics["is_success"] = 1.0 if 200 <= response.status_code < 300 else 0.0
                metrics["is_redirect"] = 1.0 if 300 <= response.status_code < 400 else 0.0
                metrics["is_client_error"] = 1.0 if 400 <= response.status_code < 500 else 0.0
                metrics["is_server_error"] = 1.0 if 500 <= response.status_code < 600 else 0.0
            
            # Track the metrics
            track_api_metrics(endpoint, metrics)
            
            # Log for monitoring
            logger.debug(
                f"API request: {request.method} {path} - "
                f"{response.status_code if response else 'Error'} - "
                f"{duration_ms:.2f}ms"
            )
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """Set up middleware for the application.
    
    Args:
        app: The FastAPI application instance
    """
    # Add metrics middleware
    if settings.ENABLE_PERFORMANCE_LOGGING:
        app.add_middleware(MetricsMiddleware)
        logger.info("API metrics middleware enabled")
