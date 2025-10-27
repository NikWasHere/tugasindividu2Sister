"""
Failure Detector untuk distributed systems
Implementasi phi-accrual failure detector
"""

import time
import math
from typing import Dict, List, Optional
from collections import deque
from loguru import logger


class FailureDetector:
    """
    Phi Accrual Failure Detector
    
    Mendeteksi node failures dengan probabilistic approach
    """
    
    def __init__(self, threshold: float = 8.0, window_size: int = 100,
                 min_std_dev: float = 0.5):
        self.threshold = threshold
        self.window_size = window_size
        self.min_std_dev = min_std_dev
        
        # Heartbeat history for each node
        self.heartbeat_history: Dict[str, deque] = {}
        self.last_heartbeat: Dict[str, float] = {}
        
        # Failure state
        self.suspected_nodes: set = set()
    
    def heartbeat(self, node_id: str):
        """Record heartbeat from node"""
        now = time.time()
        
        if node_id not in self.heartbeat_history:
            self.heartbeat_history[node_id] = deque(maxlen=self.window_size)
        
        # Record interval
        if node_id in self.last_heartbeat:
            interval = now - self.last_heartbeat[node_id]
            self.heartbeat_history[node_id].append(interval)
        
        self.last_heartbeat[node_id] = now
        
        # Remove from suspected if it was there
        if node_id in self.suspected_nodes:
            self.suspected_nodes.remove(node_id)
            logger.info(f"Node {node_id} recovered")
    
    def phi(self, node_id: str) -> float:
        """Calculate phi value for node"""
        if node_id not in self.last_heartbeat:
            return float('inf')
        
        if node_id not in self.heartbeat_history or len(self.heartbeat_history[node_id]) < 2:
            return 0.0
        
        now = time.time()
        time_since_last = now - self.last_heartbeat[node_id]
        
        # Calculate mean and standard deviation
        intervals = list(self.heartbeat_history[node_id])
        mean = sum(intervals) / len(intervals)
        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std_dev = max(math.sqrt(variance), self.min_std_dev)
        
        # Calculate phi
        phi_value = -math.log10(self._cdf(time_since_last, mean, std_dev))
        
        return phi_value
    
    def _cdf(self, x: float, mean: float, std_dev: float) -> float:
        """Cumulative distribution function (normal distribution)"""
        # Simple approximation
        z = (x - mean) / std_dev
        t = 1.0 / (1.0 + 0.2316419 * abs(z))
        d = 0.3989423 * math.exp(-z * z / 2.0)
        p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
        
        if z > 0:
            return 1.0 - p
        else:
            return p
    
    def is_available(self, node_id: str) -> bool:
        """Check if node is available"""
        phi_value = self.phi(node_id)
        is_available = phi_value < self.threshold
        
        if not is_available and node_id not in self.suspected_nodes:
            self.suspected_nodes.add(node_id)
            logger.warning(f"Node {node_id} suspected as failed (phi={phi_value:.2f})")
        
        return is_available
    
    def get_available_nodes(self, node_ids: List[str]) -> List[str]:
        """Get list of available nodes"""
        return [node_id for node_id in node_ids if self.is_available(node_id)]
    
    def get_suspected_nodes(self) -> set:
        """Get set of suspected nodes"""
        return self.suspected_nodes.copy()
    
    def reset(self, node_id: str):
        """Reset detection for node"""
        if node_id in self.heartbeat_history:
            del self.heartbeat_history[node_id]
        if node_id in self.last_heartbeat:
            del self.last_heartbeat[node_id]
        if node_id in self.suspected_nodes:
            self.suspected_nodes.remove(node_id)
