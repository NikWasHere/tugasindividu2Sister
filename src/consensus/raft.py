"""
Raft Consensus Algorithm Implementation
Implementasi lengkap Raft consensus untuk distributed lock manager
"""

import asyncio
import random
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from loguru import logger

from ..utils.config import Config
from .message import (
    MessageType, RaftMessage, RequestVoteMessage,
    VoteResponseMessage, AppendEntriesMessage, AppendEntriesResponseMessage
)


class RaftState(Enum):
    """Raft node states"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    """Raft log entry"""
    term: int
    index: int
    command: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'term': self.term,
            'index': self.index,
            'command': self.command,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        return cls(
            term=data['term'],
            index=data['index'],
            command=data['command'],
            timestamp=data.get('timestamp', time.time())
        )


class RaftNode:
    """
    Implementasi Raft Consensus Node
    
    Fitur:
    - Leader election
    - Log replication
    - Safety guarantees
    - Network partition handling
    """
    
    def __init__(self, node_id: str, cluster_nodes: List[Dict[str, Any]], 
                 communication_layer=None):
        self.node_id = node_id
        self.cluster_nodes = {n['id']: n for n in cluster_nodes if n['id'] != node_id}
        self.communication = communication_layer
        
        # Persistent state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[LogEntry] = []
        
        # Volatile state (all servers)
        self.commit_index = 0
        self.last_applied = 0
        self.state = RaftState.FOLLOWER
        
        # Volatile state (leaders)
        self.next_index: Dict[str, int] = {}
        self.match_index: Dict[str, int] = {}
        
        # Election state
        self.election_timeout = self._random_election_timeout()
        self.last_heartbeat = time.time()
        self.votes_received: Set[str] = set()
        
        # State machine
        self.state_machine: Dict[str, Any] = {}
        
        # Tasks
        self.election_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_commit_callback = None
        
        logger.info(f"Raft node {node_id} initialized with {len(self.cluster_nodes)} peers")
    
    def _random_election_timeout(self) -> float:
        """Generate random election timeout"""
        return random.uniform(
            Config.ELECTION_TIMEOUT_MIN,
            Config.ELECTION_TIMEOUT_MAX
        )
    
    async def start(self):
        """Start Raft node"""
        logger.info(f"Starting Raft node {self.node_id}")
        self.election_task = asyncio.create_task(self._election_timer())
        
    async def stop(self):
        """Stop Raft node"""
        logger.info(f"Stopping Raft node {self.node_id}")
        if self.election_task:
            self.election_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
    
    async def _election_timer(self):
        """Election timeout timer"""
        while True:
            try:
                await asyncio.sleep(0.1)
                
                if self.state == RaftState.LEADER:
                    continue
                
                elapsed = time.time() - self.last_heartbeat
                if elapsed >= self.election_timeout:
                    logger.warning(f"Election timeout! Starting election (elapsed: {elapsed:.2f}s)")
                    await self._start_election()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in election timer: {e}")
    
    async def _start_election(self):
        """Start leader election"""
        # Transition to candidate
        self.state = RaftState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = {self.node_id}
        self.election_timeout = self._random_election_timeout()
        self.last_heartbeat = time.time()
        
        logger.info(f"Starting election for term {self.current_term}")
        
        # Request votes from all peers
        last_log_index = len(self.log) - 1
        last_log_term = self.log[-1].term if self.log else 0
        
        vote_request = RequestVoteMessage(
            term=self.current_term,
            candidate_id=self.node_id,
            last_log_index=last_log_index,
            last_log_term=last_log_term
        )
        
        # Send vote requests to all peers
        tasks = []
        for peer_id in self.cluster_nodes.keys():
            task = asyncio.create_task(
                self._send_vote_request(peer_id, vote_request)
            )
            tasks.append(task)
        
        # Wait for responses
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if we won the election
        quorum = (len(self.cluster_nodes) + 1) // 2 + 1
        if len(self.votes_received) >= quorum and self.state == RaftState.CANDIDATE:
            await self._become_leader()
    
    async def _send_vote_request(self, peer_id: str, vote_request: RequestVoteMessage):
        """Send vote request to peer"""
        try:
            if not self.communication:
                return
            
            message = RaftMessage(
                msg_type=MessageType.REQUEST_VOTE,
                term=self.current_term,
                sender_id=self.node_id,
                data=vote_request.__dict__
            )
            
            response = await self.communication.send_message(peer_id, message)
            if response:
                await self._handle_vote_response(peer_id, response)
                
        except Exception as e:
            logger.error(f"Error sending vote request to {peer_id}: {e}")
    
    async def _handle_vote_response(self, peer_id: str, response: RaftMessage):
        """Handle vote response"""
        if response.term > self.current_term:
            await self._step_down(response.term)
            return
        
        if response.term == self.current_term and response.data.get('vote_granted'):
            self.votes_received.add(peer_id)
            logger.info(f"Received vote from {peer_id} ({len(self.votes_received)} total)")
    
    async def _become_leader(self):
        """Become leader"""
        logger.info(f"🎉 Node {self.node_id} became LEADER for term {self.current_term}")
        self.state = RaftState.LEADER
        
        # Initialize leader state
        last_log_index = len(self.log)
        for peer_id in self.cluster_nodes.keys():
            self.next_index[peer_id] = last_log_index
            self.match_index[peer_id] = 0
        
        # Start sending heartbeats
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        self.heartbeat_task = asyncio.create_task(self._send_heartbeats())
    
    async def _send_heartbeats(self):
        """Send periodic heartbeats to all followers"""
        while self.state == RaftState.LEADER:
            try:
                tasks = []
                for peer_id in self.cluster_nodes.keys():
                    task = asyncio.create_task(self._send_append_entries(peer_id))
                    tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                await asyncio.sleep(Config.HEARTBEAT_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeats: {e}")
    
    async def _send_append_entries(self, peer_id: str, entries: List[LogEntry] = None):
        """Send append entries to follower"""
        if entries is None:
            entries = []
        
        try:
            next_idx = self.next_index.get(peer_id, len(self.log))
            prev_log_index = next_idx - 1
            prev_log_term = self.log[prev_log_index].term if prev_log_index >= 0 else 0
            
            # Get entries to send
            entries_to_send = []
            if not entries:
                # Heartbeat or catch-up
                if next_idx < len(self.log):
                    entries_to_send = self.log[next_idx:]
            else:
                entries_to_send = entries
            
            append_msg = AppendEntriesMessage(
                term=self.current_term,
                leader_id=self.node_id,
                prev_log_index=prev_log_index,
                prev_log_term=prev_log_term,
                entries=[e.to_dict() for e in entries_to_send],
                leader_commit=self.commit_index
            )
            
            if self.communication:
                message = RaftMessage(
                    msg_type=MessageType.APPEND_ENTRIES,
                    term=self.current_term,
                    sender_id=self.node_id,
                    data=append_msg.__dict__
                )
                
                response = await self.communication.send_message(peer_id, message)
                if response:
                    await self._handle_append_entries_response(peer_id, response)
                    
        except Exception as e:
            logger.error(f"Error sending append entries to {peer_id}: {e}")
    
    async def _handle_append_entries_response(self, peer_id: str, response: RaftMessage):
        """Handle append entries response"""
        if response.term > self.current_term:
            await self._step_down(response.term)
            return
        
        if self.state != RaftState.LEADER:
            return
        
        success = response.data.get('success', False)
        match_index = response.data.get('match_index', 0)
        
        if success:
            # Update next_index and match_index
            self.next_index[peer_id] = match_index + 1
            self.match_index[peer_id] = match_index
            
            # Update commit index
            await self._update_commit_index()
        else:
            # Decrement next_index and retry
            self.next_index[peer_id] = max(0, self.next_index[peer_id] - 1)
    
    async def _update_commit_index(self):
        """Update commit index based on match indices"""
        if self.state != RaftState.LEADER:
            return
        
        # Find highest N such that majority of match_index[i] >= N
        for n in range(len(self.log) - 1, self.commit_index, -1):
            if self.log[n].term == self.current_term:
                count = 1  # Count self
                for peer_id in self.cluster_nodes.keys():
                    if self.match_index.get(peer_id, 0) >= n:
                        count += 1
                
                quorum = (len(self.cluster_nodes) + 1) // 2 + 1
                if count >= quorum:
                    self.commit_index = n
                    await self._apply_committed_entries()
                    break
    
    async def _apply_committed_entries(self):
        """Apply committed entries to state machine"""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied]
            
            # Apply to state machine
            await self._apply_to_state_machine(entry)
            
            logger.info(f"Applied entry {self.last_applied} to state machine")
    
    async def _apply_to_state_machine(self, entry: LogEntry):
        """Apply log entry to state machine"""
        command = entry.command
        
        # Execute command on state machine
        # This is where locks, queue operations, etc. are applied
        if self.on_commit_callback:
            await self.on_commit_callback(command)
    
    async def _step_down(self, new_term: int):
        """Step down to follower"""
        logger.info(f"Stepping down to follower (term {self.current_term} -> {new_term})")
        self.current_term = new_term
        self.state = RaftState.FOLLOWER
        self.voted_for = None
        self.last_heartbeat = time.time()
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
    
    async def handle_message(self, message: RaftMessage) -> Optional[RaftMessage]:
        """Handle incoming Raft message"""
        # Update term if necessary
        if message.term > self.current_term:
            await self._step_down(message.term)
        
        if message.msg_type == MessageType.REQUEST_VOTE:
            return await self._handle_request_vote(message)
        elif message.msg_type == MessageType.APPEND_ENTRIES:
            return await self._handle_append_entries(message)
        elif message.msg_type == MessageType.CLIENT_REQUEST:
            return await self._handle_client_request(message)
        
        return None
    
    async def _handle_request_vote(self, message: RaftMessage) -> RaftMessage:
        """Handle request vote message"""
        data = message.data
        vote_granted = False
        
        # Check if we can grant vote
        if message.term < self.current_term:
            vote_granted = False
        elif self.voted_for is None or self.voted_for == message.sender_id:
            # Check if candidate's log is at least as up-to-date
            last_log_index = len(self.log) - 1
            last_log_term = self.log[-1].term if self.log else 0
            
            candidate_last_index = data.get('last_log_index', -1)
            candidate_last_term = data.get('last_log_term', 0)
            
            if (candidate_last_term > last_log_term or 
                (candidate_last_term == last_log_term and candidate_last_index >= last_log_index)):
                vote_granted = True
                self.voted_for = message.sender_id
                self.last_heartbeat = time.time()
        
        logger.info(f"Vote request from {message.sender_id}: {vote_granted}")
        
        return RaftMessage(
            msg_type=MessageType.VOTE_RESPONSE,
            term=self.current_term,
            sender_id=self.node_id,
            data={'vote_granted': vote_granted}
        )
    
    async def _handle_append_entries(self, message: RaftMessage) -> RaftMessage:
        """Handle append entries message"""
        data = message.data
        success = False
        match_index = 0
        
        if message.term < self.current_term:
            success = False
        else:
            # Valid leader, reset election timeout
            self.last_heartbeat = time.time()
            
            if self.state == RaftState.CANDIDATE:
                self.state = RaftState.FOLLOWER
            
            prev_log_index = data.get('prev_log_index', -1)
            prev_log_term = data.get('prev_log_term', 0)
            
            # Check if log matches
            if prev_log_index == -1 or (
                prev_log_index < len(self.log) and 
                self.log[prev_log_index].term == prev_log_term
            ):
                success = True
                
                # Append new entries
                entries_data = data.get('entries', [])
                if entries_data:
                    # Remove conflicting entries
                    new_index = prev_log_index + 1
                    if new_index < len(self.log):
                        self.log = self.log[:new_index]
                    
                    # Append new entries
                    for entry_data in entries_data:
                        entry = LogEntry.from_dict(entry_data)
                        self.log.append(entry)
                
                match_index = prev_log_index + len(entries_data)
                
                # Update commit index
                leader_commit = data.get('leader_commit', 0)
                if leader_commit > self.commit_index:
                    self.commit_index = min(leader_commit, len(self.log) - 1)
                    await self._apply_committed_entries()
        
        return RaftMessage(
            msg_type=MessageType.APPEND_ENTRIES_RESPONSE,
            term=self.current_term,
            sender_id=self.node_id,
            data={'success': success, 'match_index': match_index}
        )
    
    async def _handle_client_request(self, message: RaftMessage) -> RaftMessage:
        """Handle client request"""
        if self.state != RaftState.LEADER:
            # Redirect to leader
            return RaftMessage(
                msg_type=MessageType.CLIENT_RESPONSE,
                term=self.current_term,
                sender_id=self.node_id,
                data={'success': False, 'error': 'Not leader'}
            )
        
        # Append to log
        command = message.data.get('command', {})
        entry = LogEntry(
            term=self.current_term,
            index=len(self.log),
            command=command
        )
        self.log.append(entry)
        
        # Replicate to followers
        tasks = []
        for peer_id in self.cluster_nodes.keys():
            task = asyncio.create_task(
                self._send_append_entries(peer_id, [entry])
            )
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Wait for commit (simplified - in production, wait for actual commit)
        await asyncio.sleep(0.1)
        
        return RaftMessage(
            msg_type=MessageType.CLIENT_RESPONSE,
            term=self.current_term,
            sender_id=self.node_id,
            data={'success': True, 'index': entry.index}
        )
    
    async def submit_command(self, command: Dict[str, Any]) -> bool:
        """Submit command to Raft (client API)"""
        if self.state != RaftState.LEADER:
            return False
        
        message = RaftMessage(
            msg_type=MessageType.CLIENT_REQUEST,
            term=self.current_term,
            sender_id=self.node_id,
            data={'command': command}
        )
        
        response = await self._handle_client_request(message)
        return response.data.get('success', False)
    
    def is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self.state == RaftState.LEADER
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return {
            'node_id': self.node_id,
            'state': self.state.value,
            'term': self.current_term,
            'commit_index': self.commit_index,
            'last_applied': self.last_applied,
            'log_size': len(self.log),
            'voted_for': self.voted_for
        }
