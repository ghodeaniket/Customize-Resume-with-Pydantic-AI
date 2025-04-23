"""Tests for the cache providers.

This module contains tests for the cache providers.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
import redis

from resume_customizer.services.cache.provider import (
    CacheProvider,
    InMemoryCacheProvider,
    RedisCacheProvider,
    get_cache_provider
)


class TestInMemoryCacheProvider:
    """Test cases for the InMemoryCacheProvider class."""
    
    @pytest.fixture
    def cache(self):
        """Create a cache provider for testing."""
        return InMemoryCacheProvider()
    
    @pytest.mark.asyncio
    async def test_get_set(self, cache):
        """Test getting and setting a value."""
        # Set a value
        await cache.set("test_key", "test_value")
        
        # Get the value
        value = await cache.get("test_key")
        
        # Verify the result
        assert value == "test_value"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, cache):
        """Test getting a nonexistent value."""
        value = await cache.get("nonexistent_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_set_complex_value(self, cache):
        """Test setting a complex value."""
        complex_value = {"key": "value", "nested": {"inner": "value"}}
        await cache.set("complex_key", complex_value)
        
        value = await cache.get("complex_key")
        assert value == complex_value
    
    @pytest.mark.asyncio
    async def test_ttl(self, cache):
        """Test time-to-live functionality."""
        # Set a value with a short TTL
        await cache.set("ttl_key", "ttl_value", ttl=1)
        
        # Verify it exists initially
        value = await cache.get("ttl_key")
        assert value == "ttl_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Verify it's gone
        value = await cache.get("ttl_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_delete(self, cache):
        """Test deleting a value."""
        # Set a value
        await cache.set("delete_key", "delete_value")
        
        # Delete it
        await cache.delete("delete_key")
        
        # Verify it's gone
        value = await cache.get("delete_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all values."""
        # Set some values
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        # Clear the cache
        await cache.clear()
        
        # Verify they're gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


@pytest.mark.asyncio
async def test_cached_decorator():
    """Test the cached decorator."""
    cache = InMemoryCacheProvider()
    
    # Define a function to cache
    call_count = 0
    
    @cache.cached(prefix="test", ttl=10)
    async def test_function(arg1, arg2=None):
        nonlocal call_count
        call_count += 1
        return f"{arg1}-{arg2}"
    
    # Call it multiple times with the same args
    result1 = await test_function("a", arg2="b")
    result2 = await test_function("a", arg2="b")
    
    # Verify caching worked
    assert result1 == "a-b"
    assert result2 == "a-b"
    assert call_count == 1  # Only called once due to caching
    
    # Call with different args
    result3 = await test_function("c", arg2="d")
    
    # Verify new call was made
    assert result3 == "c-d"
    assert call_count == 2


class TestRedisCacheProvider:
    """Test cases for the RedisCacheProvider class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch('redis.from_url') as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def cache(self, mock_redis):
        """Create a cache provider for testing."""
        with patch('resume_customizer.core.config.settings.REDIS_URL', 'redis://localhost'):
            return RedisCacheProvider()
    
    @pytest.mark.asyncio
    async def test_get(self, cache, mock_redis):
        """Test getting a value."""
        # Setup the mock
        mock_redis.get.return_value = b'\x80\x04\x95\x0f\x00\x00\x00\x00\x00\x00\x00\x8c\ntest_value\x94.'  # Pickled "test_value"
        
        # Get the value
        value = await cache.get("test_key")
        
        # Verify the result
        assert value == "test_value"
        mock_redis.get.assert_called_once_with("resume_customizer:test_key")
    
    @pytest.mark.asyncio
    async def test_set(self, cache, mock_redis):
        """Test setting a value."""
        # Set a value
        await cache.set("test_key", "test_value")
        
        # Verify the Redis call
        mock_redis.set.assert_called_once()
        assert mock_redis.set.call_args[0][0] == "resume_customizer:test_key"
    
    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache, mock_redis):
        """Test setting a value with TTL."""
        # Set a value with TTL
        await cache.set("test_key", "test_value", ttl=60)
        
        # Verify the Redis call
        mock_redis.setex.assert_called_once()
        assert mock_redis.setex.call_args[0][0] == "resume_customizer:test_key"
        assert mock_redis.setex.call_args[0][1] == 60
    
    @pytest.mark.asyncio
    async def test_delete(self, cache, mock_redis):
        """Test deleting a value."""
        # Delete a value
        await cache.delete("test_key")
        
        # Verify the Redis call
        mock_redis.delete.assert_called_once_with("resume_customizer:test_key")
    
    @pytest.mark.asyncio
    async def test_clear(self, cache, mock_redis):
        """Test clearing all values."""
        # Setup the mock
        mock_redis.keys.return_value = ["resume_customizer:key1", "resume_customizer:key2"]
        
        # Clear the cache
        await cache.clear()
        
        # Verify the Redis calls
        mock_redis.keys.assert_called_once_with("resume_customizer:*")
        mock_redis.delete.assert_called_once_with("resume_customizer:key1", "resume_customizer:key2")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cache, mock_redis):
        """Test error handling."""
        # Setup the mock to raise an error
        mock_redis.get.side_effect = redis.RedisError("Connection error")
        
        # Get the value (should not raise an error)
        value = await cache.get("test_key")
        
        # Verify the result
        assert value is None


def test_get_cache_provider():
    """Test the get_cache_provider function."""
    # Test with no Redis URL
    with patch('resume_customizer.core.config.settings') as mock_settings:
        mock_settings.REDIS_URL = None
        provider = get_cache_provider()
        assert isinstance(provider, InMemoryCacheProvider)
    
    # Test with Redis URL
    with patch('resume_customizer.core.config.settings') as mock_settings, \
         patch('resume_customizer.services.cache.provider.RedisCacheProvider') as mock_redis_provider:
        
        mock_settings.REDIS_URL = "redis://localhost"
        mock_instance = MagicMock()
        mock_redis_provider.return_value = mock_instance
        
        provider = get_cache_provider()
        assert provider == mock_instance
        mock_redis_provider.assert_called_once_with("redis://localhost")
    
    # Test with Redis error
    with patch('resume_customizer.core.config.settings') as mock_settings, \
         patch('resume_customizer.services.cache.provider.RedisCacheProvider', side_effect=Exception("Redis error")):
        
        mock_settings.REDIS_URL = "redis://localhost"
        provider = get_cache_provider()
        assert isinstance(provider, InMemoryCacheProvider)
