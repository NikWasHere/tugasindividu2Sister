"""
Distributed Lock Manager dengan Raft Consensus
Support untuk shared dan exclusive locks dengan deadlock detection
"""

import asyncio
import time
from enum import Enum
from typing import Dict, Set, Optional, List
from dataclasses import dataclass
from loguru import logger

from .base_node import BaseNode


class LockType(Enum):
    """Types of distributed locks"""
    SHARED = "shared"
    EXCLUSIVE = "exclusive"


@dataclass
class LockRequest:
    """Lock request"""
    resource_id: str
    lock_type: LockType
    client_id: str
    timestamp: float
    
    
@dataclass
class LockInfo:
    """Lock information"""
    resource_id: str
    lock_type: LockType
    holders: Set[str]
    waiters: List[LockRequest]
    acquired_at: float


class DeadlockDetector:
    """Deteksi deadlock dalam distributed environment"""
    
    def __init__(self):
        self.wait_for_graph: Dict[str, Set[str]] = {}
    
    def add_edge(self, client_from: str, client_to: str):
        """Add edge to wait-for graph"""
        if client_from not in self.wait_for_graph:
            self.wait_for_graph[client_from] = set()
        self.wait_for_graph[client_from].add(client_to)
    
    def remove_edge(self, client_from: str, client_to: str):
        """Remove edge from wait-for graph"""
        if client_from in self.wait_for_graph:
            self.wait_for_graph[client_from].discard(client_to)
    
    def has_cycle(self) -> Optional[List[str]]:
        """Detect cycle in wait-for graph (deadlock)"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in self.wait_for_graph:
                for neighbor in self.wait_for_graph[node]:
                    if neighbor not in visited:
                        result = dfs(neighbor)
                        if result:
                            return result
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        return path[cycle_start:]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        for node in self.wait_for_graph.keys():
            if node not in visited:
                cycle = dfs(node)
                if cycle:
                    return cycle
        
        return None


class LockManager(BaseNode):
    """
    Distributed Lock Manager dengan Raft Consensus
    
    Fitur:
    - Shared dan exclusive locks
    - Deadlock detection
    - Fair queuing
    - Network partition handling
    """
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "LockManager")
        
        # Lock state
        self.locks: Dict[str, LockInfo] = {}
        self.client_locks: Dict[str, Set[str]] = {}  # client -> resources
        
        # Deadlock detection
        self.deadlock_detector = DeadlockDetector()
        
        # Set Raft commit callback
        self.raft.on_commit_callback = self._apply_lock_operation
        
        # Lock statistics
        self.lock_stats = {
            'acquired': 0,
            'released': 0,
            'deadlocks_detected': 0,
            'timeouts': 0
        }
    
    async def acquire_lock(self, resource_id: str, lock_type: LockType, 
                          client_id: str, timeout: float = 30.0) -> bool:
        """
        Acquire distributed lock
        
        Returns:
            True if lock acquired, False if timeout or deadlock
        """
        start_time = time.time()
        
        # Submit to Raft
        command = {
            'operation': 'acquire',
            'resource_id': resource_id,
            'lock_type': lock_type.value,
            'client_id': client_id,
            'timestamp': start_time
        }
        
        if not self.raft.is_leader():
            logger.warning(f"Not leader, cannot acquire lock for {resource_id}")
            return False
        
        # Submit command through Raft consensus
        success = await self.raft.submit_command(command)
        
        if not success:
            return False
        
        # Wait for lock to be acquired
        while time.time() - start_time < timeout:
            if self._is_lock_held(resource_id, client_id):
                wait_time = time.time() - start_time
                self.metrics.record_lock(lock_type.value, True, wait_time)
                self.lock_stats['acquired'] += 1
                logger.info(f"Lock acquired: {resource_id} by {client_id} ({lock_type.value})")
                return True
            
            # Check for deadlock
            cycle = self.deadlock_detector.has_cycle()
            if cycle and client_id in cycle:
                logger.error(f"Deadlock detected involving {client_id}: {cycle}")
                self.lock_stats['deadlocks_detected'] += 1
                await self._resolve_deadlock(cycle)
                return False
            
            await asyncio.sleep(0.1)
        
        # Timeout
        logger.warning(f"Lock acquisition timeout for {resource_id} by {client_id}")
        self.lock_stats['timeouts'] += 1
        return False
    
    async def release_lock(self, resource_id: str, client_id: str) -> bool:
        """Release distributed lock"""
        command = {
            'operation': 'release',
            'resource_id': resource_id,
            'client_id': client_id
        }
        
        if not self.raft.is_leader():
            logger.warning(f"Not leader, cannot release lock for {resource_id}")
            return False
        
        success = await self.raft.submit_command(command)
        
        if success:
            self.metrics.record_lock_release(lock_type="unknown")
            self.lock_stats['released'] += 1
            logger.info(f"Lock released: {resource_id} by {client_id}")
        
        return success
    
    async def _apply_lock_operation(self, command: Dict):
        """Apply lock operation to state machine"""
        operation = command.get('operation')
        
        if operation == 'acquire':
            await self._apply_acquire(command)
        elif operation == 'release':
            await self._apply_release(command)
    
    async def _apply_acquire(self, command: Dict):
        """Apply lock acquisition"""
        resource_id = command['resource_id']
        lock_type = LockType(command['lock_type'])
        client_id = command['client_id']
        timestamp = command['timestamp']
        
        # Initialize lock if doesn't exist
        if resource_id not in self.locks:
            self.locks[resource_id] = LockInfo(
                resource_id=resource_id,
                lock_type=lock_type,
                holders=set(),
                waiters=[],
                acquired_at=timestamp
            )
        
        lock = self.locks[resource_id]
        
        # Check if can grant lock
        can_grant = False
        
        if not lock.holders:
            # No holders, can grant
            can_grant = True
        elif lock_type == LockType.SHARED and lock.lock_type == LockType.SHARED:
            # Both shared, can grant
            can_grant = True
        
        if can_grant:
            lock.holders.add(client_id)
            lock.lock_type = lock_type
            
            # Update client locks
            if client_id not in self.client_locks:
                self.client_locks[client_id] = set()
            self.client_locks[client_id].add(resource_id)
        else:
            # Add to waiters
            request = LockRequest(
                resource_id=resource_id,
                lock_type=lock_type,
                client_id=client_id,
                timestamp=timestamp
            )
            lock.waiters.append(request)
            
            # Update wait-for graph
            for holder in lock.holders:
                self.deadlock_detector.add_edge(client_id, holder)
    
    async def _apply_release(self, command: Dict):
        """Apply lock release"""
        resource_id = command['resource_id']
        client_id = command['client_id']
        
        if resource_id not in self.locks:
            return
        
        lock = self.locks[resource_id]
        
        # Remove from holders
        lock.holders.discard(client_id)
        
        # Remove from client locks
        if client_id in self.client_locks:
            self.client_locks[client_id].discard(resource_id)
        
        # Remove from wait-for graph
        for holder in lock.holders:
            self.deadlock_detector.remove_edge(client_id, holder)
        
        # Grant to waiters if possible
        if not lock.holders and lock.waiters:
            # Sort waiters by timestamp (FIFO)
            lock.waiters.sort(key=lambda x: x.timestamp)
            
            # Grant to first waiter
            first_waiter = lock.waiters[0]
            lock.waiters.pop(0)
            
            # Re-submit acquire
            await self._apply_acquire({
                'resource_id': first_waiter.resource_id,
                'lock_type': first_waiter.lock_type.value,
                'client_id': first_waiter.client_id,
                'timestamp': first_waiter.timestamp
            })
    
    def _is_lock_held(self, resource_id: str, client_id: str) -> bool:
        """Check if lock is held by client"""
        if resource_id in self.locks:
            return client_id in self.locks[resource_id].holders
        return False
    
    async def _resolve_deadlock(self, cycle: List[str]):
        """Resolve deadlock by aborting youngest transaction"""
        # Find youngest (most recent) client in cycle
        youngest = None
        youngest_time = 0
        
        for client_id in cycle:
            if client_id in self.client_locks:
                for resource_id in self.client_locks[client_id]:
                    if resource_id in self.locks:
                        lock = self.locks[resource_id]
                        if lock.acquired_at > youngest_time:
                            youngest_time = lock.acquired_at
                            youngest = client_id
        
        if youngest:
            logger.warning(f"Aborting {youngest} to resolve deadlock")
            # Release all locks for youngest client
            if youngest in self.client_locks:
                resources = list(self.client_locks[youngest])
                for resource_id in resources:
                    await self.release_lock(resource_id, youngest)
    
    def get_lock_status(self, resource_id: str) -> Optional[Dict]:
        """Get status of a lock"""
        if resource_id not in self.locks:
            return None
        
        lock = self.locks[resource_id]
        return {
            'resource_id': resource_id,
            'lock_type': lock.lock_type.value,
            'holders': list(lock.holders),
            'waiters': len(lock.waiters),
            'acquired_at': lock.acquired_at
        }
    
    def get_statistics(self) -> Dict:
        """Get lock manager statistics"""
        return {
            **self.lock_stats,
            'active_locks': len(self.locks),
            'total_holders': sum(len(lock.holders) for lock in self.locks.values()),
            'total_waiters': sum(len(lock.waiters) for lock in self.locks.values())
        }
