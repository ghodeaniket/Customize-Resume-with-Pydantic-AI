"""Simple caching system for API responses."""
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, TypeVar, Generic, Callable

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Cache(Generic[T]):
    """Simple in-memory cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 300):
        """Initialize cache.
        
        Args:
            ttl_seconds: Time to live in seconds
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        
    def get(self, key: str) -> Optional[T]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[T]: Cached value or None if not found or expired
        """
        if key not in self.cache:
            logger.debug(f"Cache miss: {key}")
            return None
        
        entry = self.cache[key]
        now = time.time()
        
        # Check if entry is expired
        if now > entry['expiry']:
            logger.debug(f"Cache entry expired: {key}")
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return entry['value']
    
    def set(self, key: str, value: T) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        logger.debug(f"Cache set: {key}")
        expiry = time.time() + self.ttl_seconds
        self.cache[key] = {
            'value': value,
            'expiry': expiry
        }
    
    def invalidate(self, key: str) -> None:
        """Remove entry from cache.
        
        Args:
            key: Cache key
        """
        if key in self.cache:
            logger.debug(f"Cache invalidate: {key}")
            del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        logger.debug("Cache clear")
        self.cache.clear()


# Create a global response cache instance
response_cache = Cache[Any]()


def generate_cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    """Generate a cache key from endpoint and parameters.
    
    Args:
        endpoint: API endpoint name
        params: Request parameters
        
    Returns:
        str: Cache key
    """
    # Create a sorted, deterministic JSON representation of parameters
    sorted_params = json.dumps(params, sort_keys=True)
    
    # Create a hash of the endpoint and parameters
    key = f"{endpoint}:{sorted_params}"
    return hashlib.md5(key.encode()).hexdigest()


def cache_response(endpoint: str, ttl_seconds: Optional[int] = None) -> Callable:
    """Decorator for caching API responses.
    
    Args:
        endpoint: Endpoint name
        ttl_seconds: Cache TTL (or global default if None)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        """Decorator function."""
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            """Wrapper function."""
            from core.config import get_settings
            
            settings = get_settings()
            
            # Skip caching if disabled
            if not settings.enable_response_cache:
                return await func(*args, **kwargs)
            
            # Generate cache key from endpoint and kwargs
            cache_key = generate_cache_key(endpoint, kwargs)
            
            # Try to get cached response
            cached_response = response_cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Get fresh response
            response = await func(*args, **kwargs)
            
            # Cache response with TTL
            effective_ttl = ttl_seconds or settings.cache_ttl_seconds
            if effective_ttl > 0:
                # Use custom TTL for this cache instance
                custom_cache = Cache[Any](ttl_seconds=effective_ttl)
                custom_cache.set(cache_key, response)
                response_cache.cache[cache_key] = custom_cache.cache[cache_key]
            
            return response
        
        return wrapper
    
    return decorator
