"""API middleware components."""
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 60,
        admin_paths: Tuple[str, ...] = ("/docs", "/redoc", "/openapi.json", "/health"),
    ):
        """Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests allowed per minute
            admin_paths: Paths excluded from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.admin_paths = admin_paths
        self.request_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.cleanup_interval = 5 * 60  # Cleanup old data every 5 minutes
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process each request for rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            Response: HTTP response
        """
        # Skip rate limiting for admin paths
        path = request.url.path
        if path in self.admin_paths:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get current minute
        current_minute = int(time.time() / 60)
        
        # Clean up old data occasionally
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_data(current_minute)
            self.last_cleanup = now
        
        # Check rate limit
        if self.request_counts[client_ip][current_minute] >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "message": "Rate limit exceeded",
                    "details": {
                        "limit": self.requests_per_minute,
                        "reset_after_seconds": 60 - int(time.time() % 60)
                    }
                }
            )
        
        # Increment request count
        self.request_counts[client_ip][current_minute] += 1
        
        # Process request
        return await call_next(request)
    
    def _cleanup_old_data(self, current_minute: int) -> None:
        """Remove old request count data.
        
        Args:
            current_minute: Current minute timestamp
        """
        # Keep only the last 5 minutes of data
        for ip in list(self.request_counts.keys()):
            minutes = list(self.request_counts[ip].keys())
            for minute in minutes:
                if minute < current_minute - 5:
                    del self.request_counts[ip][minute]
            
            # Remove IP entries with no data
            if not self.request_counts[ip]:
                del self.request_counts[ip]
