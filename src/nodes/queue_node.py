"""
Distributed Queue System dengan Consistent Hashing
Support untuk multiple producers/consumers dengan at-least-once delivery
"""

import asyncio
import hashlib
import time
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger
import redis.asyncio as redis

from .base_node import BaseNode
from ..utils.config import Config


@dataclass
class Message:
    """Queue message"""
    message_id: str
    partition: int
    data: Dict
    timestamp: float = field(default_factory=time.time)
    attempts: int = 0
    delivered: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'partition': self.partition,
            'data': self.data,
            'timestamp': self.timestamp,
            'attempts': self.attempts,
            'delivered': self.delivered
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(**data)


class ConsistentHash:
    """Consistent hashing implementation"""
    
    def __init__(self, nodes: List[str], virtual_nodes: int = 150):
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []
        
        for node in nodes:
            self.add_node(node)
    
    def _hash(self, key: str) -> int:
        """Hash function"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str):
        """Add node to ring"""
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node
        
        self.sorted_keys = sorted(self.ring.keys())
        logger.info(f"Added node {node} to consistent hash ring")
    
    def remove_node(self, node: str):
        """Remove node from ring"""
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]
        
        self.sorted_keys = sorted(self.ring.keys())
        logger.info(f"Removed node {node} from consistent hash ring")
    
    def get_node(self, key: str) -> Optional[str]:
        """Get node for key"""
        if not self.ring:
            return None
        
        hash_value = self._hash(key)
        
        # Find first node with hash >= key hash
        for ring_hash in self.sorted_keys:
            if ring_hash >= hash_value:
                return self.ring[ring_hash]
        
        # Wrap around to first node
        return self.ring[self.sorted_keys[0]]


class QueueNode(BaseNode):
    """
    Distributed Queue Node dengan Consistent Hashing
    
    Fitur:
    - Consistent hashing untuk distribusi
    - Multiple producers/consumers
    - Message persistence dengan Redis
    - At-least-once delivery guarantee
    - Node failure recovery
    """
    
    def __init__(self, node_id: str):
        super().__init__(node_id, "QueueNode")
        
        # Consistent hashing
        all_nodes = [self.node_id] + list(self.communication.cluster_nodes.keys())
        self.consistent_hash = ConsistentHash(all_nodes)
        
        # Queue state
        self.partitions: Dict[int, List[Message]] = defaultdict(list)
        self.pending_acks: Dict[str, Message] = {}
        self.consumer_groups: Dict[str, Set[str]] = defaultdict(set)
        
        # Redis for persistence
        self.redis_client: Optional[redis.Redis] = None
        
        # Statistics
        self.stats = {
            'produced': 0,
            'consumed': 0,
            'redelivered': 0,
            'persisted': 0
        }
    
    async def start(self):
        """Start queue node"""
        await super().start()
        
        # Initialize Redis
        if Config.MESSAGE_PERSISTENCE:
            try:
                self.redis_client = await redis.from_url(
                    f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}",
                    password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Connected to Redis for message persistence")
                
                # Recover messages from Redis
                await self._recover_messages()
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
        
        # Start redelivery checker
        task = asyncio.create_task(self._check_redelivery())
        self.tasks.append(task)
    
    async def stop(self):
        """Stop queue node"""
        if self.redis_client:
            await self.redis_client.close()
        await super().stop()
    
    def _get_partition(self, key: str) -> int:
        """Get partition for key using consistent hashing"""
        node = self.consistent_hash.get_node(key)
        # Map node to partition number
        return hash(node) % Config.QUEUE_PARTITIONS
    
    async def produce(self, data: Dict, partition_key: Optional[str] = None) -> str:
        """
        Produce message to queue
        
        Returns:
            Message ID
        """
        # Generate message ID
        message_id = f"{self.node_id}:{time.time()}:{self.stats['produced']}"
        
        # Determine partition
        if partition_key:
            partition = self._get_partition(partition_key)
        else:
            partition = self.stats['produced'] % Config.QUEUE_PARTITIONS
        
        # Create message
        message = Message(
            message_id=message_id,
            partition=partition,
            data=data
        )
        
        # Add to partition
        self.partitions[partition].append(message)
        
        # Persist to Redis
        if self.redis_client:
            await self._persist_message(message)
            self.stats['persisted'] += 1
        
        # Update metrics
        self.metrics.record_message_produced(str(partition))
        self.metrics.update_queue_size(str(partition), len(self.partitions[partition]))
        self.stats['produced'] += 1
        
        logger.info(f"Produced message {message_id} to partition {partition}")
        
        return message_id
    
    async def consume(self, partition: int, consumer_id: str, 
                     timeout: float = 5.0) -> Optional[Message]:
        """
        Consume message from queue
        
        Returns:
            Message if available, None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if partition in self.partitions and self.partitions[partition]:
                # Get next message
                message = self.partitions[partition].pop(0)
                message.attempts += 1
                
                # Add to pending acks (for at-least-once delivery)
                ack_key = f"{consumer_id}:{message.message_id}"
                self.pending_acks[ack_key] = message
                
                # Update metrics
                self.metrics.record_message_consumed(str(partition))
                self.metrics.update_queue_size(str(partition), len(self.partitions[partition]))
                self.stats['consumed'] += 1
                
                logger.info(f"Consumed message {message.message_id} from partition {partition}")
                
                return message
            
            await asyncio.sleep(0.1)
        
        return None
    
    async def acknowledge(self, consumer_id: str, message_id: str) -> bool:
        """Acknowledge message delivery"""
        ack_key = f"{consumer_id}:{message_id}"
        
        if ack_key in self.pending_acks:
            message = self.pending_acks[ack_key]
            message.delivered = True
            del self.pending_acks[ack_key]
            
            # Remove from Redis
            if self.redis_client:
                await self._delete_message(message_id)
            
            logger.info(f"Acknowledged message {message_id}")
            return True
        
        return False
    
    async def _persist_message(self, message: Message):
        """Persist message to Redis"""
        if not self.redis_client:
            return
        
        try:
            key = f"message:{message.message_id}"
            await self.redis_client.set(
                key,
                json.dumps(message.to_dict()),
                ex=86400  # 24 hour TTL
            )
        except Exception as e:
            logger.error(f"Failed to persist message: {e}")
    
    async def _delete_message(self, message_id: str):
        """Delete message from Redis"""
        if not self.redis_client:
            return
        
        try:
            key = f"message:{message_id}"
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
    
    async def _recover_messages(self):
        """Recover messages from Redis on startup"""
        if not self.redis_client:
            return
        
        try:
            # Scan for all messages
            cursor = 0
            recovered = 0
            
            async for key in self.redis_client.scan_iter(match="message:*"):
                data = await self.redis_client.get(key)
                if data:
                    message = Message.from_dict(json.loads(data))
                    if not message.delivered:
                        self.partitions[message.partition].append(message)
                        recovered += 1
            
            logger.info(f"Recovered {recovered} messages from Redis")
            
        except Exception as e:
            logger.error(f"Failed to recover messages: {e}")
    
    async def _check_redelivery(self):
        """Check for messages that need redelivery"""
        while self.running:
            try:
                now = time.time()
                timeout = 30.0  # 30 seconds
                
                # Check pending acks
                expired = []
                for ack_key, message in self.pending_acks.items():
                    if now - message.timestamp > timeout:
                        expired.append(ack_key)
                
                # Redeliver expired messages
                for ack_key in expired:
                    message = self.pending_acks[ack_key]
                    del self.pending_acks[ack_key]
                    
                    # Re-queue message
                    self.partitions[message.partition].insert(0, message)
                    self.stats['redelivered'] += 1
                    
                    logger.warning(f"Redelivering message {message.message_id} (attempt {message.attempts})")
                
                await asyncio.sleep(5.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in redelivery checker: {e}")
    
    def get_partition_sizes(self) -> Dict[int, int]:
        """Get sizes of all partitions"""
        return {p: len(messages) for p, messages in self.partitions.items()}
    
    def get_statistics(self) -> Dict:
        """Get queue statistics"""
        return {
            **self.stats,
            'partitions': len(self.partitions),
            'total_queued': sum(len(msgs) for msgs in self.partitions.values()),
            'pending_acks': len(self.pending_acks)
        }
