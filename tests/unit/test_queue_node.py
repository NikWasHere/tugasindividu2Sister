"""Unit tests untuk Queue Node"""

import pytest
import asyncio
from src.nodes.queue_node import QueueNode, Message


@pytest.mark.asyncio
class TestQueueNode:
    """Test suite for Queue Node"""
    
    async def test_queue_initialization(self):
        """Test queue node initialization"""
        queue_node = QueueNode("test-node-1")
        assert queue_node.node_id == "test-node-1"
        assert len(queue_node.partitions) == 0
    
    async def test_produce_message(self):
        """Test message production"""
        queue_node = QueueNode("test-node-1")
        await queue_node.start()
        
        msg_id = await queue_node.produce(
            data={"test": "data"},
            partition_key="test-key"
        )
        
        assert msg_id is not None
        assert queue_node.stats['produced'] == 1
        
        await queue_node.stop()
    
    async def test_consume_message(self):
        """Test message consumption"""
        queue_node = QueueNode("test-node-1")
        await queue_node.start()
        
        partition = 0
        queue_node.partitions[partition].append(
            Message(
                message_id="test-msg-1",
                partition=partition,
                data={"test": "data"}
            )
        )
        
        msg = await queue_node.consume(partition, "consumer-1", timeout=1.0)
        
        assert msg is not None
        assert msg.message_id == "test-msg-1"
        
        await queue_node.stop()
    
    async def test_consistent_hashing(self):
        """Test consistent hashing"""
        queue_node = QueueNode("test-node-1")
        
        partition1 = queue_node._get_partition("test-key")
        partition2 = queue_node._get_partition("test-key")
        
        assert partition1 == partition2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
