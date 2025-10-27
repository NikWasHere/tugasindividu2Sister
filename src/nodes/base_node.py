"""
Base Node class untuk semua distributed nodes
"""

import asyncio
from typing import Dict, Any, Optional
from loguru import logger

from ..consensus.raft import RaftNode
from ..communication.message_passing import MessagePassingLayer
from ..communication.failure_detector import FailureDetector
from ..utils.config import Config
from ..utils.metrics import MetricsCollector


class BaseNode:
    """Base class untuk semua distributed nodes"""
    
    def __init__(self, node_id: str, node_type: str):
        self.node_id = node_id
        self.node_type = node_type
        
        # Parse cluster configuration
        Config.parse_cluster_nodes()
        
        # Initialize components
        self.communication = MessagePassingLayer(
            node_id=node_id,
            cluster_nodes={n['id']: n for n in Config.CLUSTER_NODES if n['id'] != node_id}
        )
        
        self.raft = RaftNode(
            node_id=node_id,
            cluster_nodes=Config.CLUSTER_NODES,
            communication_layer=self.communication
        )
        
        self.failure_detector = FailureDetector()
        self.metrics = MetricsCollector(node_id)
        
        # State
        self.running = False
        self.tasks = []
        
        logger.info(f"Initialized {node_type} node: {node_id}")
    
    async def start(self):
        """Start node"""
        logger.info(f"Starting {self.node_type} node {self.node_id}")
        
        # Find this node's configuration
        node_config = None
        for node in Config.CLUSTER_NODES:
            if node['id'] == self.node_id:
                node_config = node
                break
        
        if not node_config:
            raise ValueError(f"Node {self.node_id} not found in cluster configuration")
        
        # Start communication
        await self.communication.start(node_config['host'], node_config['port'])
        
        # Set message handler
        self.communication.set_message_handler(self.raft.handle_message)
        
        # Start Raft
        await self.raft.start()
        
        # Start metrics collection
        if Config.METRICS_ENABLED:
            task = asyncio.create_task(self.metrics.collect_system_metrics())
            self.tasks.append(task)
        
        # Start heartbeat monitoring
        task = asyncio.create_task(self._monitor_heartbeats())
        self.tasks.append(task)
        
        self.running = True
        logger.info(f"{self.node_type} node {self.node_id} started successfully")
    
    async def stop(self):
        """Stop node"""
        logger.info(f"Stopping {self.node_type} node {self.node_id}")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Stop components
        await self.raft.stop()
        await self.communication.stop()
        
        logger.info(f"{self.node_type} node {self.node_id} stopped")
    
    async def _monitor_heartbeats(self):
        """Monitor heartbeats from other nodes"""
        while self.running:
            try:
                # Send heartbeat to failure detector for active nodes
                for node_id in self.communication.cluster_nodes.keys():
                    # Simulate heartbeat check
                    self.failure_detector.heartbeat(node_id)
                
                await asyncio.sleep(Config.HEARTBEAT_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitoring: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get node status"""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'running': self.running,
            'raft_state': self.raft.get_state(),
            'metrics': self.metrics.get_summary(),
            'suspected_nodes': list(self.failure_detector.get_suspected_nodes())
        }
