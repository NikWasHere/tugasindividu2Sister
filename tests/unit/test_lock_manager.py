"""Unit tests untuk Distributed Lock Manager"""

import pytest
import asyncio
from src.nodes.lock_manager import LockManager, LockType


@pytest.mark.asyncio
class TestLockManager:
    """Test suite for Lock Manager"""
    
    async def test_lock_manager_initialization(self):
        """Test lock manager can be initialized"""
        lock_mgr = LockManager("test-node-1")
        assert lock_mgr.node_id == "test-node-1"
        assert len(lock_mgr.locks) == 0
    
    async def test_exclusive_lock_acquisition(self):
        """Test exclusive lock acquisition"""
        lock_mgr = LockManager("test-node-1")
        await lock_mgr.start()
        
        # Make this node the leader
        lock_mgr.raft.state = RaftState.LEADER
        
        # Acquire exclusive lock
        success = await lock_mgr.acquire_lock(
            "resource-1", 
            LockType.EXCLUSIVE, 
            "client-1"
        )
        
        assert success
        assert "resource-1" in lock_mgr.locks
        
        await lock_mgr.stop()
    
    async def test_shared_lock_acquisition(self):
        """Test multiple shared locks"""
        lock_mgr = LockManager("test-node-1")
        await lock_mgr.start()
        
        lock_mgr.raft.state = RaftState.LEADER
        
        # Acquire shared locks
        success1 = await lock_mgr.acquire_lock(
            "resource-1", 
            LockType.SHARED, 
            "client-1"
        )
        
        success2 = await lock_mgr.acquire_lock(
            "resource-1", 
            LockType.SHARED, 
            "client-2"
        )
        
        assert success1
        assert success2
        
        await lock_mgr.stop()
    
    async def test_deadlock_detection(self):
        """Test deadlock detection"""
        lock_mgr = LockManager("test-node-1")
        
        # Create circular dependency
        lock_mgr.deadlock_detector.add_edge("client-1", "client-2")
        lock_mgr.deadlock_detector.add_edge("client-2", "client-3")
        lock_mgr.deadlock_detector.add_edge("client-3", "client-1")
        
        cycle = lock_mgr.deadlock_detector.has_cycle()
        assert cycle is not None
        assert len(cycle) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
