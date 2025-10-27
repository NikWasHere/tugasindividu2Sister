"""Message types dan structures untuk Raft consensus"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    """Raft message types"""
    REQUEST_VOTE = "request_vote"
    VOTE_RESPONSE = "vote_response"
    APPEND_ENTRIES = "append_entries"
    APPEND_ENTRIES_RESPONSE = "append_entries_response"
    HEARTBEAT = "heartbeat"
    CLIENT_REQUEST = "client_request"
    CLIENT_RESPONSE = "client_response"


@dataclass
class RaftMessage:
    """Base Raft message"""
    msg_type: MessageType
    term: int
    sender_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'msg_type': self.msg_type.value,
            'term': self.term,
            'sender_id': self.sender_id,
            'data': self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RaftMessage':
        """Create from dictionary"""
        return cls(
            msg_type=MessageType(data['msg_type']),
            term=data['term'],
            sender_id=data['sender_id'],
            data=data.get('data', {})
        )


@dataclass
class RequestVoteMessage:
    """Request vote message"""
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int


@dataclass
class VoteResponseMessage:
    """Vote response message"""
    term: int
    vote_granted: bool


@dataclass
class AppendEntriesMessage:
    """Append entries message"""
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[Dict[str, Any]]
    leader_commit: int


@dataclass
class AppendEntriesResponseMessage:
    """Append entries response"""
    term: int
    success: bool
    match_index: int = 0
