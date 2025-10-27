"""
Distributed Cache dengan MESI Protocol
Implementasi cache coherence untuk multiple cache nodes
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Optional, Any, Set
from dataclasses import dataclass
from collections import OrderedDict
from loguru import logger

from .base_node import BaseNode
from ..utils.config import Config


class CacheState(Enum):
    """MESI Cache states"""
    MODIFIED = "M"    # Modified - cache has only copy, modified
    EXCLUSIVE = "E"   # Exclusive - cache has only copy, clean
    SHARED = "S"      # Shared - other caches may have copy
    INVALID = "I"     # Invalid - cache line is invalid


@dataclass
class CacheLine:
    """Cache line with MESI state"""
    key: str
    value: Any
    state: CacheState
    timestamp: float
    access_count: int = 0
    dirty: bool = False
    
    def __post_init__(self):
        if self.state == CacheState.MODIFIED:
            self.dirty = True


class LRUCache:
    """LRU Cache implementation"""
    
    def __init__(self, capacity_mb: int):
        self.capacity_bytes = capacity_mb * 1024 * 1024
        self.current_size = 0
        self.cache: OrderedDict[str, CacheLine] = OrderedDict()
    
    def get(self, key: str) -> Optional[CacheLine]:
        """Get cache line"""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            line = self.cache[key]
            line.access_count += 1
            return line
        return None
    
    def put(self, key: str, line: CacheLine):
        """Put cache line"""
        if key in self.cache:
            # Remove old entry
            self.cache.pop(key)
        
        # Add new entry
        self.cache[key] = line
        self.cache.move_to_end(key)
        
        # Evict if necessary
        while len(self.cache) > 0 and self._estimate_size() > self.capacity_bytes:
            self._evict_lru()
    
    def remove(self, key: str):
        """Remove cache line"""
        if key in self.cache:
            self.cache.pop(key)
    
    def _evict_lru(self) -> Optional[str]:
        """Evict least recently used"""
        if self.cache:
            key, line = self.cache.popitem(last=False)
            logger.debug(f"Evicted LRU cache line: {key}")
            return key
        return None
    
    def _estimate_size(self) -> int:
        """Estimate cache size in bytes"""
        # Simplified size estimation
        return len(self.cache) * 1024  # Assume 1KB per entry
    
    def size(self) -> int:
        """Get number of cache lines"""
        return len(self.cache)


class CacheNode(BaseNode):
    """
    Distributed Cache Node dengan MESI Protocol
    
    Fitur:
    - MESI cache coherence protocol
    - LRU replacement policy
    - Cache invalidation dan update propagation
    - Performance monitoring
    """
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "CacheNode")
        
        # Cache storage
        self.cache = LRUCache(Config.CACHE_SIZE_MB)
        
        # Track which nodes have which keys
        self.key_locations: Dict[str, Set[str]] = {}
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'writebacks': 0,
            'evictions': 0
        }
        
        # Set Raft commit callback for cache operations
        self.raft.on_commit_callback = self._apply_cache_operation
    
    async def read(self, key: str) -> Optional[Any]:
        """
        Read from cache with MESI protocol
        
        MESI transitions on read:
        - I -> S or E (fetch from memory/other cache)
        - S -> S (no change)
        - E -> E (no change)
        - M -> M (no change)
        """
        line = self.cache.get(key)
        
        if line and line.state != CacheState.INVALID:
            # Cache hit
            self.metrics.record_cache_hit()
            self.stats['hits'] += 1
            logger.debug(f"Cache hit: {key} (state: {line.state.value})")
            return line.value
        
        # Cache miss
        self.metrics.record_cache_miss()
        self.stats['misses'] += 1
        logger.debug(f"Cache miss: {key}")
        
        # Fetch from memory (simulated via Raft)
        if self.raft.is_leader():
            value = await self._fetch_from_memory(key)
            
            if value is not None:
                # Check if other caches have this key
                has_sharers = await self._check_sharers(key)
                
                # Determine state
                state = CacheState.SHARED if has_sharers else CacheState.EXCLUSIVE
                
                # Add to cache
                new_line = CacheLine(
                    key=key,
                    value=value,
                    state=state,
                    timestamp=time.time()
                )
                self.cache.put(key, new_line)
                
                # Register location
                await self._register_location(key)
                
                return value
        
        return None
    
    async def write(self, key: str, value: Any) -> bool:
        """
        Write to cache with MESI protocol
        
        MESI transitions on write:
        - I -> M (invalidate others, write)
        - S -> M (invalidate others, write)
        - E -> M (write)
        - M -> M (write)
        """
        if not self.raft.is_leader():
            logger.warning("Not leader, cannot write to cache")
            return False
        
        line = self.cache.get(key)
        
        # Invalidate other caches
        await self._invalidate_others(key)
        
        # Update cache line
        new_line = CacheLine(
            key=key,
            value=value,
            state=CacheState.MODIFIED,
            timestamp=time.time(),
            dirty=True
        )
        
        self.cache.put(key, new_line)
        
        # Submit to Raft for persistence
        command = {
            'operation': 'write',
            'key': key,
            'value': value,
            'node_id': self.node_id
        }
        await self.raft.submit_command(command)
        
        # Register location
        await self._register_location(key)
        
        logger.info(f"Cache write: {key} -> M")
        return True
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate cache line"""
        line = self.cache.get(key)
        
        if line:
            # Write back if modified
            if line.state == CacheState.MODIFIED:
                await self._write_back(key, line.value)
                self.stats['writebacks'] += 1
            
            # Invalidate
            line.state = CacheState.INVALID
            self.cache.remove(key)
            
            self.metrics.record_cache_invalidation()
            self.stats['invalidations'] += 1
            
            logger.info(f"Cache invalidated: {key}")
            return True
        
        return False
    
    async def _apply_cache_operation(self, command: Dict):
        """Apply cache operation from Raft"""
        operation = command.get('operation')
        
        if operation == 'write':
            key = command['key']
            value = command['value']
            # Store in state machine (memory)
            self.raft.state_machine[key] = value
        elif operation == 'invalidate':
            key = command['key']
            await self.invalidate(key)
        elif operation == 'register':
            key = command['key']
            node_id = command['node_id']
            if key not in self.key_locations:
                self.key_locations[key] = set()
            self.key_locations[key].add(node_id)
    
    async def _fetch_from_memory(self, key: str) -> Optional[Any]:
        """Fetch value from memory (Raft state machine)"""
        # First check Raft state machine
        if key in self.raft.state_machine:
            return self.raft.state_machine[key]
        
        # Simulate fetch from backing store
        return None
    
    async def _check_sharers(self, key: str) -> bool:
        """Check if other caches have this key"""
        if key in self.key_locations:
            # Exclude self
            sharers = self.key_locations[key] - {self.node_id}
            return len(sharers) > 0
        return False
    
    async def _invalidate_others(self, key: str):
        """Invalidate key in other caches"""
        if key not in self.key_locations:
            return
        
        # Get other nodes with this key
        other_nodes = self.key_locations[key] - {self.node_id}
        
        if not other_nodes:
            return
        
        # Send invalidation through Raft
        command = {
            'operation': 'invalidate',
            'key': key,
            'source_node': self.node_id
        }
        
        if self.raft.is_leader():
            await self.raft.submit_command(command)
        
        logger.debug(f"Invalidated {key} in {len(other_nodes)} other caches")
    
    async def _register_location(self, key: str):
        """Register that this node has this key"""
        command = {
            'operation': 'register',
            'key': key,
            'node_id': self.node_id
        }
        
        if self.raft.is_leader():
            await self.raft.submit_command(command)
    
    async def _write_back(self, key: str, value: Any):
        """Write back modified data to memory"""
        command = {
            'operation': 'write',
            'key': key,
            'value': value,
            'node_id': self.node_id
        }
        
        if self.raft.is_leader():
            await self.raft.submit_command(command)
        
        logger.debug(f"Write back: {key}")
    
    def get_cache_statistics(self) -> Dict:
        """Get cache statistics"""
        total_accesses = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_accesses if total_accesses > 0 else 0
        
        return {
            **self.stats,
            'cache_size': self.cache.size(),
            'hit_rate': hit_rate,
            'total_accesses': total_accesses
        }
    
    def get_cache_contents(self) -> Dict[str, Dict]:
        """Get cache contents for debugging"""
        return {
            key: {
                'value': line.value,
                'state': line.state.value,
                'access_count': line.access_count,
                'dirty': line.dirty
            }
            for key, line in self.cache.cache.items()
        }
