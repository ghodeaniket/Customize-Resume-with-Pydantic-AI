"""Middleware for the Resume Customizer API.

This module contains custom middleware for the FastAPI application.
"""

import time
from typing import Callable, Dict, Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from resume_customizer.core.exceptions import ResumeCustomizerException
from resume_customizer.core.logging import app_logger as logger


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors.
    
    This middleware catches exceptions and returns appropriate responses.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process a request and handle any errors.
        
        Args:
            request: The incoming request
            call_next: The next middleware to call
            
        Returns:
            Response: The response
        """
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except ResumeCustomizerException as exc:
            # Log the exception
            logger.error(f"ResumeCustomizerException: {str(exc)}")
            
            # Return a JSON response with error details
            return JSONResponse(
                status_code=500,
                content={"error": str(exc)},
            )
            
        except Exception as exc:
            # Log the exception
            logger.exception(f"Unhandled exception: {str(exc)}")
            
            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={"error": "An unexpected error occurred"},
            )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses.
    
    This middleware logs details about incoming requests and outgoing responses.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Log request and response details.
        
        Args:
            request: The incoming request
            call_next: The next middleware to call
            
        Returns:
            Response: The response
        """
        # Get request details
        request_id = f"{id(request):x}"
        method = request.method
        url = str(request.url)
        
        # Log the request
        logger.info(f"Request {request_id}: {method} {url}")
        
        # Track request processing time
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log the response
        logger.info(
            f"Response {request_id}: status={response.status_code} "
            f"processed in {process_time:.4f}s"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        
        return response


def add_middleware(app: FastAPI) -> None:
    """Add custom middleware to the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    logger.info("Custom middleware configured")
