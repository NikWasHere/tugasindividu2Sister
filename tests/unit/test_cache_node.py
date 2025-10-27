"""Unit tests untuk Cache Node"""

import pytest
import asyncio
from src.nodes.cache_node import CacheNode, CacheState, LRUCache


@pytest.mark.asyncio
class TestCacheNode:
    """Test suite for Cache Node"""
    
    async def test_cache_initialization(self):
        """Test cache node initialization"""
        cache_node = CacheNode("test-node-1")
        assert cache_node.node_id == "test-node-1"
        assert cache_node.cache.size() == 0
    
    async def test_lru_cache(self):
        """Test LRU cache"""
        cache = LRUCache(capacity_mb=1)
        
        # Add items
        from src.nodes.cache_node import CacheLine
        cache.put("key1", CacheLine("key1", "value1", CacheState.EXCLUSIVE, 0))
        cache.put("key2", CacheLine("key2", "value2", CacheState.EXCLUSIVE, 0))
        
        # Get item (moves to end)
        line = cache.get("key1")
        assert line is not None
        assert line.value == "value1"
    
    async def test_cache_read_miss(self):
        """Test cache read miss"""
        cache_node = CacheNode("test-node-1")
        await cache_node.start()
        
        # Read non-existent key
        value = await cache_node.read("non-existent")
        
        assert cache_node.stats['misses'] == 1
        
        await cache_node.stop()
    
    async def test_mesi_states(self):
        """Test MESI state transitions"""
        cache_node = CacheNode("test-node-1")
        
        from src.nodes.cache_node import CacheLine
        
        # Invalid -> Exclusive
        line = CacheLine("key1", "value1", CacheState.EXCLUSIVE, 0)
        assert line.state == CacheState.EXCLUSIVE
        
        # Exclusive -> Modified
        line.state = CacheState.MODIFIED
        assert line.dirty == False  # dirty flag set in __post_init__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
