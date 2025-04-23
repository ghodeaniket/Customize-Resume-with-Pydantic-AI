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


# Dictionary to store request metrics
request_metrics: Dict[str, Dict[str, Any]] = {}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses.
    
    This middleware logs details about incoming requests and outgoing responses,
    and tracks performance metrics.
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
        # Generate a unique request ID
        request_id = f"{id(request):x}"
        
        # Get request details
        method = request.method
        url = str(request.url)
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Extract route details if available
        route = getattr(request.scope.get("route"), "path", path)
        
        # Log the request
        logger.info(
            f"Request {request_id}: {method} {url} from {client_host} "
            f"(Route: {route})"
        )
        
        # Track request processing time
        start_time = time.time()
        
        # Initialize metrics for this endpoint
        endpoint_key = f"{method}:{route}"
        if endpoint_key not in request_metrics:
            request_metrics[endpoint_key] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "avg_time": 0,
                "status_counts": {}
            }
        
        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.exception(f"Error processing request {request_id}: {str(e)}")
            status_code = 500
            raise
        finally:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Update metrics
            metrics = request_metrics[endpoint_key]
            metrics["count"] += 1
            metrics["total_time"] += process_time
            metrics["min_time"] = min(metrics["min_time"], process_time)
            metrics["max_time"] = max(metrics["max_time"], process_time)
            metrics["avg_time"] = metrics["total_time"] / metrics["count"]
            
            if status_code not in metrics["status_counts"]:
                metrics["status_counts"][status_code] = 0
            metrics["status_counts"][status_code] += 1
            
            # Log the response
            logger.info(
                f"Response {request_id}: status={status_code} "
                f"processed in {process_time:.4f}s"
            )
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = request_id
        
        return response


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking performance metrics.
    
    This middleware tracks memory usage and other performance metrics.
    """
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Track performance metrics.
        
        Args:
            request: The incoming request
            call_next: The next middleware to call
            
        Returns:
            Response: The response
        """
        # Only log detailed performance metrics for certain endpoints
        should_log_performance = (
            request.url.path.startswith("/api/v1/resumes") and 
            request.method in ["POST", "PUT"]
        )
        
        if should_log_performance:
            import psutil
            process = psutil.Process()
            
            # Memory before request
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent_before = process.cpu_percent()
            
            # Process the request
            response = await call_next(request)
            
            # Memory after request
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent_after = process.cpu_percent()
            
            # Log memory usage
            logger.info(
                f"Performance: Memory before={memory_before:.2f}MB, "
                f"after={memory_after:.2f}MB, "
                f"diff={memory_after-memory_before:.2f}MB, "
                f"CPU={cpu_percent_after:.2f}%"
            )
            
            # Add performance headers
            response.headers["X-Memory-Usage"] = f"{memory_after:.2f}MB"
            response.headers["X-Memory-Diff"] = f"{memory_after-memory_before:.2f}MB"
            response.headers["X-CPU-Usage"] = f"{cpu_percent_after:.2f}%"
            
            return response
        else:
            # For non-tracked endpoints, just process normally
            return await call_next(request)


def add_middleware(app: FastAPI) -> None:
    """Add custom middleware to the FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(PerformanceMiddleware)
    
    logger.info("Custom middleware configured")


# Endpoint to get request metrics
async def get_request_metrics() -> Dict[str, Dict[str, Any]]:
    """Get the collected request metrics.
    
    Returns:
        Dict: The request metrics
    """
    return request_metrics
