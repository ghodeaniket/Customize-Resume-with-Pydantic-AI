"""Decorators for applying error handling strategies.

This module provides decorators that can be applied to functions to automatically
handle errors using the strategies defined in the strategies module.
"""

import asyncio
import functools
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from loguru import logger

from resume_customizer.core.error_handling.strategies import (
    retry_with_exponential_backoff,
    handle_agent_error,
)


T = TypeVar('T')


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True,
    retry_errors: Optional[List[Type[Exception]]] = None,
):
    """Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        jitter: Whether to add random jitter to delays
        retry_errors: Specific error types to retry, or None for all errors
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_with_exponential_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                jitter=jitter,
                retry_errors=retry_errors,
                **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For synchronous functions, run the async version in an event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Use the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_fallback(
    agent_name: Optional[str] = None,
    fallback_func: Optional[Callable[..., Any]] = None,
):
    """Decorator to apply error handling with fallbacks for agent functions.
    
    Args:
        agent_name: Name of the agent for context
        fallback_func: Optional custom fallback function
        
    Returns:
        A decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Error in {func.__name__}: {str(e)}")
                
                # Prepare context for error handler
                context = {
                    "func": func,
                    "args": args,
                    "kwargs": kwargs,
                    "agent": kwargs.get("agent", None),
                    "agent_kwargs": {k: v for k, v in kwargs.items() if k != "agent"},
                }
                
                # If a custom fallback is provided, use it
                if fallback_func:
                    return await fallback_func(e, agent_name, context)
                
                # Otherwise use the standard error handler
                return await handle_agent_error(e, agent_name, context)
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For synchronous functions, run the async version in an event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Use the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
