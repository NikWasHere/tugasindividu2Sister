"""Configuration management untuk distributed system"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class Config:
    """Centralized configuration management"""
    
    # Node Configuration
    NODE_ID: str = os.getenv('NODE_ID', 'node-1')
    NODE_HOST: str = os.getenv('NODE_HOST', 'localhost')
    NODE_PORT: int = int(os.getenv('NODE_PORT', '5000'))
    
    # Cluster Configuration
    CLUSTER_NODES: List[Dict[str, Any]] = []
    HEARTBEAT_INTERVAL: float = float(os.getenv('HEARTBEAT_INTERVAL', '1.0'))
    ELECTION_TIMEOUT_MIN: float = float(os.getenv('ELECTION_TIMEOUT_MIN', '5.0'))
    ELECTION_TIMEOUT_MAX: float = float(os.getenv('ELECTION_TIMEOUT_MAX', '10.0'))
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: str = os.getenv('REDIS_PASSWORD', '')
    
    # Queue Configuration
    QUEUE_PARTITIONS: int = int(os.getenv('QUEUE_PARTITIONS', '16'))
    QUEUE_REPLICATION_FACTOR: int = int(os.getenv('QUEUE_REPLICATION_FACTOR', '2'))
    MESSAGE_PERSISTENCE: bool = os.getenv('MESSAGE_PERSISTENCE', 'true').lower() == 'true'
    DELIVERY_GUARANTEE: str = os.getenv('DELIVERY_GUARANTEE', 'at-least-once')
    
    # Cache Configuration
    CACHE_PROTOCOL: str = os.getenv('CACHE_PROTOCOL', 'MESI')
    CACHE_SIZE_MB: int = int(os.getenv('CACHE_SIZE_MB', '256'))
    CACHE_REPLACEMENT_POLICY: str = os.getenv('CACHE_REPLACEMENT_POLICY', 'LRU')
    CACHE_INVALIDATION_TIMEOUT: int = int(os.getenv('CACHE_INVALIDATION_TIMEOUT', '60'))
    
    # Consensus Configuration
    CONSENSUS_ALGORITHM: str = os.getenv('CONSENSUS_ALGORITHM', 'raft')
    QUORUM_SIZE: int = int(os.getenv('QUORUM_SIZE', '2'))
    LOG_COMPACTION_THRESHOLD: int = int(os.getenv('LOG_COMPACTION_THRESHOLD', '1000'))
    
    # Performance Configuration
    MAX_CONNECTIONS: int = int(os.getenv('MAX_CONNECTIONS', '1000'))
    WORKER_THREADS: int = int(os.getenv('WORKER_THREADS', '4'))
    BUFFER_SIZE: int = int(os.getenv('BUFFER_SIZE', '8192'))
    
    # Monitoring
    METRICS_ENABLED: bool = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    METRICS_PORT: int = int(os.getenv('METRICS_PORT', '9090'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Security
    ENABLE_ENCRYPTION: bool = os.getenv('ENABLE_ENCRYPTION', 'false').lower() == 'true'
    TLS_CERT_PATH: str = os.getenv('TLS_CERT_PATH', './certs/server.crt')
    TLS_KEY_PATH: str = os.getenv('TLS_KEY_PATH', './certs/server.key')
    
    # Testing
    TEST_MODE: bool = os.getenv('TEST_MODE', 'false').lower() == 'true'
    SIMULATE_FAILURES: bool = os.getenv('SIMULATE_FAILURES', 'false').lower() == 'true'
    FAILURE_RATE: float = float(os.getenv('FAILURE_RATE', '0.01'))
    
    @classmethod
    def parse_cluster_nodes(cls):
        """Parse cluster nodes from environment variable"""
        nodes_str = os.getenv('CLUSTER_NODES', '')
        if not nodes_str:
            return []
        
        nodes = []
        for node_str in nodes_str.split(','):
            parts = node_str.strip().split(':')
            if len(parts) == 3:
                nodes.append({
                    'id': parts[0],
                    'host': parts[1],
                    'port': int(parts[2])
                })
        cls.CLUSTER_NODES = nodes
        return nodes
    
    @classmethod
    def get_node_address(cls, node_id: str) -> tuple:
        """Get node address by ID"""
        for node in cls.CLUSTER_NODES:
            if node['id'] == node_id:
                return (node['host'], node['port'])
        return None
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        cls.parse_cluster_nodes()
        
        # Validate required fields
        assert cls.NODE_ID, "NODE_ID is required"
        assert cls.NODE_HOST, "NODE_HOST is required"
        assert cls.NODE_PORT > 0, "NODE_PORT must be positive"
        
        # Validate cluster
        if len(cls.CLUSTER_NODES) < 3:
            raise ValueError("Minimum 3 nodes required for Raft consensus")
        
        return True


# Initialize configuration on import
Config.validate()
