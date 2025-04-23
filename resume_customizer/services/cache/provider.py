"""Cache providers for the Resume Customizer application.

This module provides functionality for caching expensive operations like
document processing and API calls.
"""

import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

import redis
from loguru import logger

from resume_customizer.core.config import settings


# Type variable for generic function return type
T = TypeVar("T")


class CacheProvider(ABC):
    """Abstract base class for cache providers."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key.
        
        Args:
            key: The cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cached value with optional TTL.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a cached value by key.
        
        Args:
            key: The cache key
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass
    
    def cached(
        self, 
        prefix: str = "", 
        ttl: Optional[int] = None,
        key_builder: Optional[Callable[..., str]] = None
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """Decorator for caching function results.
        
        Args:
            prefix: Prefix for the cache key
            ttl: Time-to-live in seconds
            key_builder: Custom function for building cache keys
            
        Returns:
            A decorator function
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # Default key building strategy
                    key_parts = [prefix, func.__name__]
                    
                    # Handle args (skip self/cls for methods)
                    if args:
                        skip_first = False
                        if len(args) > 0 and hasattr(args[0], "__class__"):
                            if args[0].__class__.__name__ == func.__qualname__.split('.')[0]:
                                skip_first = True
                        
                        serialized_args = [str(arg) for arg in (args[1:] if skip_first else args)]
                        if serialized_args:
                            key_parts.append("-".join(serialized_args))
                    
                    # Handle kwargs
                    if kwargs:
                        serialized_kwargs = [f"{k}={v}" for k, v in sorted(kwargs.items())]
                        key_parts.append("-".join(serialized_kwargs))
                    
                    # Create a hash of the full key to keep it a reasonable length
                    full_key = ":".join(key_parts)
                    cache_key = hashlib.md5(full_key.encode()).hexdigest()
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
                
                # Execute the function
                logger.debug(f"Cache miss for {func.__name__}")
                result = await func(*args, **kwargs)
                
                # Cache the result
                await self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator


class InMemoryCacheProvider(CacheProvider):
    """In-memory cache provider.
    
    This provider stores cached values in memory, which is fast but
    not shared between different instances of the application.
    """
    
    def __init__(self):
        """Initialize the cache provider."""
        self._cache: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        logger.info("Initialized in-memory cache provider")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key.
        
        Args:
            key: The cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        # Check if key exists and is not expired
        if key in self._cache:
            if key in self._expiry and self._expiry[key] < logger.time.time():
                # Key has expired
                del self._cache[key]
                del self._expiry[key]
                return None
            
            return self._cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cached value with optional TTL.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self._cache[key] = value
        
        if ttl is not None:
            self._expiry[key] = logger.time.time() + ttl
    
    async def delete(self, key: str) -> None:
        """Delete a cached value by key.
        
        Args:
            key: The cache key
        """
        if key in self._cache:
            del self._cache[key]
        
        if key in self._expiry:
            del self._expiry[key]
    
    async def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._expiry.clear()


class RedisCacheProvider(CacheProvider):
    """Redis cache provider.
    
    This provider stores cached values in Redis, which allows for sharing
    cache between different instances of the application.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize the cache provider.
        
        Args:
            redis_url: Redis connection URL (defaults to environment variable)
        """
        self._redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[redis.Redis] = None
        self._prefix = "resume_customizer:"
        logger.info(f"Initialized Redis cache provider with URL: {self._redis_url}")
    
    @property
    def client(self) -> redis.Redis:
        """Get the Redis client.
        
        Returns:
            Redis: The Redis client
        """
        if self._redis is None:
            self._redis = redis.from_url(self._redis_url)
        return self._redis
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a cached value by key.
        
        Args:
            key: The cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        try:
            prefixed_key = f"{self._prefix}{key}"
            value = self.client.get(prefixed_key)
            
            if value is None:
                return None
            
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"Redis cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a cached value with optional TTL.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        try:
            prefixed_key = f"{self._prefix}{key}"
            pickled_value = pickle.dumps(value)
            
            if ttl is not None:
                self.client.setex(prefixed_key, ttl, pickled_value)
            else:
                self.client.set(prefixed_key, pickled_value)
        except Exception as e:
            logger.error(f"Redis cache set error: {str(e)}")
    
    async def delete(self, key: str) -> None:
        """Delete a cached value by key.
        
        Args:
            key: The cache key
        """
        try:
            prefixed_key = f"{self._prefix}{key}"
            self.client.delete(prefixed_key)
        except Exception as e:
            logger.error(f"Redis cache delete error: {str(e)}")
    
    async def clear(self) -> None:
        """Clear all cached values with our prefix."""
        try:
            keys = self.client.keys(f"{self._prefix}*")
            if keys:
                self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis cache clear error: {str(e)}")


# Cache provider factory function
def get_cache_provider() -> CacheProvider:
    """Get the appropriate cache provider based on configuration.
    
    Returns:
        CacheProvider: The cache provider
    """
    redis_url = getattr(settings, "REDIS_URL", None)
    
    if redis_url:
        try:
            return RedisCacheProvider(redis_url)
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {str(e)}")
            logger.warning("Falling back to in-memory cache")
    
    return InMemoryCacheProvider()
