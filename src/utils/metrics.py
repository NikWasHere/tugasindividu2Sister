"""Metrics collection untuk monitoring performa sistem"""

import time
import psutil
from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from collections import defaultdict
import asyncio


class MetricsCollector:
    """Collect and expose system metrics"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.registry = CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'requests_total',
            'Total number of requests',
            ['node_id', 'operation', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['node_id', 'operation'],
            registry=self.registry
        )
        
        # Lock metrics
        self.locks_acquired = Counter(
            'locks_acquired_total',
            'Total locks acquired',
            ['node_id', 'lock_type'],
            registry=self.registry
        )
        
        self.locks_released = Counter(
            'locks_released_total',
            'Total locks released',
            ['node_id', 'lock_type'],
            registry=self.registry
        )
        
        self.lock_wait_time = Histogram(
            'lock_wait_time_seconds',
            'Time waiting for lock',
            ['node_id', 'lock_type'],
            registry=self.registry
        )
        
        # Queue metrics
        self.messages_produced = Counter(
            'messages_produced_total',
            'Total messages produced',
            ['node_id', 'partition'],
            registry=self.registry
        )
        
        self.messages_consumed = Counter(
            'messages_consumed_total',
            'Total messages consumed',
            ['node_id', 'partition'],
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'queue_size',
            'Current queue size',
            ['node_id', 'partition'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['node_id'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['node_id'],
            registry=self.registry
        )
        
        self.cache_invalidations = Counter(
            'cache_invalidations_total',
            'Total cache invalidations',
            ['node_id'],
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'cache_size_bytes',
            'Current cache size in bytes',
            ['node_id'],
            registry=self.registry
        )
        
        # Consensus metrics
        self.raft_term = Gauge(
            'raft_term',
            'Current Raft term',
            ['node_id'],
            registry=self.registry
        )
        
        self.raft_log_entries = Gauge(
            'raft_log_entries',
            'Number of log entries',
            ['node_id'],
            registry=self.registry
        )
        
        self.raft_commit_index = Gauge(
            'raft_commit_index',
            'Commit index',
            ['node_id'],
            registry=self.registry
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            ['node_id'],
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['node_id'],
            registry=self.registry
        )
        
        self.network_sent = Counter(
            'network_bytes_sent',
            'Network bytes sent',
            ['node_id'],
            registry=self.registry
        )
        
        self.network_recv = Counter(
            'network_bytes_received',
            'Network bytes received',
            ['node_id'],
            registry=self.registry
        )
        
        # Custom stats
        self.stats = defaultdict(lambda: defaultdict(int))
        self.timings = defaultdict(list)
    
    def record_request(self, operation: str, status: str, duration: float):
        """Record a request"""
        self.request_count.labels(
            node_id=self.node_id,
            operation=operation,
            status=status
        ).inc()
        
        self.request_duration.labels(
            node_id=self.node_id,
            operation=operation
        ).observe(duration)
    
    def record_lock(self, lock_type: str, acquired: bool, wait_time: float = 0):
        """Record lock acquisition"""
        if acquired:
            self.locks_acquired.labels(
                node_id=self.node_id,
                lock_type=lock_type
            ).inc()
        
        if wait_time > 0:
            self.lock_wait_time.labels(
                node_id=self.node_id,
                lock_type=lock_type
            ).observe(wait_time)
    
    def record_lock_release(self, lock_type: str):
        """Record lock release"""
        self.locks_released.labels(
            node_id=self.node_id,
            lock_type=lock_type
        ).inc()
    
    def record_message_produced(self, partition: str):
        """Record message production"""
        self.messages_produced.labels(
            node_id=self.node_id,
            partition=partition
        ).inc()
    
    def record_message_consumed(self, partition: str):
        """Record message consumption"""
        self.messages_consumed.labels(
            node_id=self.node_id,
            partition=partition
        ).inc()
    
    def update_queue_size(self, partition: str, size: int):
        """Update queue size"""
        self.queue_size.labels(
            node_id=self.node_id,
            partition=partition
        ).set(size)
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits.labels(node_id=self.node_id).inc()
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses.labels(node_id=self.node_id).inc()
    
    def record_cache_invalidation(self):
        """Record cache invalidation"""
        self.cache_invalidations.labels(node_id=self.node_id).inc()
    
    def update_cache_size(self, size_bytes: int):
        """Update cache size"""
        self.cache_size.labels(node_id=self.node_id).set(size_bytes)
    
    def update_raft_metrics(self, term: int, log_entries: int, commit_index: int):
        """Update Raft consensus metrics"""
        self.raft_term.labels(node_id=self.node_id).set(term)
        self.raft_log_entries.labels(node_id=self.node_id).set(log_entries)
        self.raft_commit_index.labels(node_id=self.node_id).set(commit_index)
    
    async def collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.labels(node_id=self.node_id).set(cpu_percent)
                
                # Memory usage
                memory = psutil.Process().memory_info()
                self.memory_usage.labels(node_id=self.node_id).set(memory.rss)
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.network_sent.labels(node_id=self.node_id).inc(net_io.bytes_sent)
                self.network_recv.labels(node_id=self.node_id).inc(net_io.bytes_recv)
                
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
            
            await asyncio.sleep(5)  # Collect every 5 seconds
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        cache_total = self.stats['cache']['hits'] + self.stats['cache']['misses']
        hit_rate = self.stats['cache']['hits'] / cache_total if cache_total > 0 else 0
        
        return {
            'node_id': self.node_id,
            'requests': dict(self.stats['requests']),
            'locks': dict(self.stats['locks']),
            'queue': dict(self.stats['queue']),
            'cache': {
                'hits': self.stats['cache']['hits'],
                'misses': self.stats['cache']['misses'],
                'hit_rate': hit_rate,
                'invalidations': self.stats['cache']['invalidations']
            },
            'system': {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024
            }
        }
