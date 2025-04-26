"""Tests for the caching system."""
import time
import unittest
from typing import Any, Dict

import pytest

from core.cache import Cache, generate_cache_key


class TestCache(unittest.TestCase):
    """Test the Cache class."""
    
    def test_get_set(self):
        """Test get and set operations."""
        cache = Cache[str](ttl_seconds=10)
        
        # Test set and get
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Test missing key
        assert cache.get("missing_key") is None
    
    def test_expiry(self):
        """Test cache entry expiry."""
        cache = Cache[str](ttl_seconds=1)
        
        # Set a value with a 1-second TTL
        cache.set("expiring_key", "expiring_value")
        
        # Value should be present initially
        assert cache.get("expiring_key") == "expiring_value"
        
        # Wait for the entry to expire
        time.sleep(1.1)
        
        # Value should now be None
        assert cache.get("expiring_key") is None
    
    def test_invalidate(self):
        """Test invalidate operation."""
        cache = Cache[Dict[str, Any]](ttl_seconds=10)
        
        # Set a value
        cache.set("key_to_invalidate", {"test": "data"})
        
        # Value should be present
        assert cache.get("key_to_invalidate") == {"test": "data"}
        
        # Invalidate the key
        cache.invalidate("key_to_invalidate")
        
        # Value should now be None
        assert cache.get("key_to_invalidate") is None
    
    def test_clear(self):
        """Test clear operation."""
        cache = Cache[int](ttl_seconds=10)
        
        # Set multiple values
        cache.set("key1", 1)
        cache.set("key2", 2)
        
        # Values should be present
        assert cache.get("key1") == 1
        assert cache.get("key2") == 2
        
        # Clear the cache
        cache.clear()
        
        # All values should now be None
        assert cache.get("key1") is None
        assert cache.get("key2") is None


def test_generate_cache_key():
    """Test generate_cache_key function."""
    # Test with simple parameters
    key1 = generate_cache_key("endpoint1", {"param1": "value1", "param2": "value2"})
    
    # Test with the same parameters in different order
    key2 = generate_cache_key("endpoint1", {"param2": "value2", "param1": "value1"})
    
    # Keys should be the same
    assert key1 == key2
    
    # Test with different parameters
    key3 = generate_cache_key("endpoint1", {"param1": "value1", "param3": "value3"})
    
    # Keys should be different
    assert key1 != key3
    
    # Test with different endpoint
    key4 = generate_cache_key("endpoint2", {"param1": "value1", "param2": "value2"})
    
    # Keys should be different
    assert key1 != key4
    
    # Test with nested parameters
    key5 = generate_cache_key("endpoint1", {
        "param1": "value1",
        "nested": {
            "subparam1": "subvalue1",
            "subparam2": "subvalue2"
        }
    })
    
    key6 = generate_cache_key("endpoint1", {
        "param1": "value1",
        "nested": {
            "subparam2": "subvalue2",
            "subparam1": "subvalue1"
        }
    })
    
    # Keys should be the same despite order change in nested dict
    assert key5 == key6
