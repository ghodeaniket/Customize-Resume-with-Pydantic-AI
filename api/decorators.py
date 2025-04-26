"""API decorators for common patterns."""
import functools
import logging
from typing import Callable, TypeVar, Any

from fastapi import HTTPException, status

from core.exceptions import ResumeCustomizerError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def handle_api_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for standardized API error handling.
    
    Catches ResumeCustomizerError and converts them to HTTPExceptions.
    Also handles generic exceptions with appropriate HTTP 500 status.
    
    Args:
        func: The API route function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except ResumeCustomizerError as e:
            logger.error(f"{func.__name__} error: {e.message}", extra={"details": e.details, "context": e.details.get("context")})
            raise HTTPException(
                status_code=e.status_code,
                detail={"message": e.message, "details": e.details}
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": f"Internal server error: {str(e)}"}
            )
    
    return wrapper


def add_request_metrics(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for adding metrics to API requests.
    
    Tracks request duration and adds timing information to the response.
    
    Args:
        func: The API route function to decorate
        
    Returns:
        Decorated function with metrics
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        import time
        
        start_time = time.time()
        result = await func(*args, **kwargs)
        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        
        # If result is a dict, add metrics
        if isinstance(result, dict):
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["processing_time_ms"] = processing_time_ms
        
        logger.info(f"{func.__name__} completed in {processing_time_ms}ms")
        return result
    
    return wrapper
