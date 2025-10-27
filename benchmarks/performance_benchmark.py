"""
Performance benchmarking and visualization
"""

import asyncio
import time
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict
import sys
sys.path.append('..')

from src.nodes.lock_manager import LockManager, LockType
from src.nodes.queue_node import QueueNode
from src.nodes.cache_node import CacheNode


class PerformanceBenchmark:
    """Benchmark suite for distributed system"""
    
    def __init__(self):
        self.results = {
            'lock_manager': [],
            'queue': [],
            'cache': []
        }
    
    async def benchmark_lock_manager(self, num_operations=1000):
        """Benchmark lock manager performance"""
        print("Benchmarking Lock Manager...")
        
        lock_mgr = LockManager("bench-node-1")
        await lock_mgr.start()
        
        # Make it leader
        from src.consensus.raft import RaftState
        lock_mgr.raft.state = RaftState.LEADER
        
        latencies = []
        
        for i in range(num_operations):
            start = time.time()
            
            # Acquire lock
            success = await lock_mgr.acquire_lock(
                f"resource-{i % 100}",
                LockType.EXCLUSIVE,
                f"client-{i}"
            )
            
            end = time.time()
            latencies.append((end - start) * 1000)  # ms
        
        await lock_mgr.stop()
        
        self.results['lock_manager'] = latencies
        print(f"Lock Manager - Avg Latency: {np.mean(latencies):.2f}ms")
    
    async def benchmark_queue(self, num_operations=1000):
        """Benchmark queue performance"""
        print("Benchmarking Queue...")
        
        queue = QueueNode("bench-node-1")
        await queue.start()
        
        produce_latencies = []
        consume_latencies = []
        
        # Produce
        for i in range(num_operations):
            start = time.time()
            
            await queue.produce(
                data={"message": f"msg-{i}"},
                partition_key=f"key-{i % 10}"
            )
            
            end = time.time()
            produce_latencies.append((end - start) * 1000)
        
        # Consume
        for i in range(num_operations):
            partition = i % 16
            start = time.time()
            
            msg = await queue.consume(partition, f"consumer-{i}", timeout=0.1)
            
            end = time.time()
            if msg:
                consume_latencies.append((end - start) * 1000)
        
        await queue.stop()
        
        self.results['queue'] = {
            'produce': produce_latencies,
            'consume': consume_latencies
        }
        
        print(f"Queue Produce - Avg Latency: {np.mean(produce_latencies):.2f}ms")
        print(f"Queue Consume - Avg Latency: {np.mean(consume_latencies):.2f}ms")
    
    async def benchmark_cache(self, num_operations=1000):
        """Benchmark cache performance"""
        print("Benchmarking Cache...")
        
        cache = CacheNode("bench-node-1")
        await cache.start()
        
        # Make it leader
        from src.consensus.raft import RaftState
        cache.raft.state = RaftState.LEADER
        
        read_latencies = []
        write_latencies = []
        
        # Write
        for i in range(num_operations):
            start = time.time()
            
            await cache.write(f"key-{i % 100}", f"value-{i}")
            
            end = time.time()
            write_latencies.append((end - start) * 1000)
        
        # Read
        for i in range(num_operations):
            start = time.time()
            
            value = await cache.read(f"key-{i % 100}")
            
            end = time.time()
            read_latencies.append((end - start) * 1000)
        
        await cache.stop()
        
        self.results['cache'] = {
            'read': read_latencies,
            'write': write_latencies
        }
        
        print(f"Cache Read - Avg Latency: {np.mean(read_latencies):.2f}ms")
        print(f"Cache Write - Avg Latency: {np.mean(write_latencies):.2f}ms")
    
    def generate_plots(self):
        """Generate performance visualization plots"""
        print("Generating plots...")
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (15, 10)
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Lock Manager
        if self.results['lock_manager']:
            data = self.results['lock_manager']
            
            # Histogram
            axes[0, 0].hist(data, bins=50, edgecolor='black')
            axes[0, 0].set_title('Lock Manager - Latency Distribution')
            axes[0, 0].set_xlabel('Latency (ms)')
            axes[0, 0].set_ylabel('Frequency')
            
            # CDF
            sorted_data = np.sort(data)
            cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
            axes[1, 0].plot(sorted_data, cdf)
            axes[1, 0].set_title('Lock Manager - Cumulative Distribution')
            axes[1, 0].set_xlabel('Latency (ms)')
            axes[1, 0].set_ylabel('CDF')
            axes[1, 0].grid(True)
        
        # Queue
        if 'queue' in self.results and self.results['queue']:
            produce_data = self.results['queue']['produce']
            consume_data = self.results['queue']['consume']
            
            # Box plot
            axes[0, 1].boxplot([produce_data, consume_data], 
                              labels=['Produce', 'Consume'])
            axes[0, 1].set_title('Queue - Latency Comparison')
            axes[0, 1].set_ylabel('Latency (ms)')
            
            # Time series
            axes[1, 1].plot(produce_data[:100], label='Produce', alpha=0.7)
            axes[1, 1].plot(consume_data[:100], label='Consume', alpha=0.7)
            axes[1, 1].set_title('Queue - Latency Over Time')
            axes[1, 1].set_xlabel('Operation Number')
            axes[1, 1].set_ylabel('Latency (ms)')
            axes[1, 1].legend()
        
        # Cache
        if 'cache' in self.results and self.results['cache']:
            read_data = self.results['cache']['read']
            write_data = self.results['cache']['write']
            
            # Violin plot
            df = pd.DataFrame({
                'Read': read_data,
                'Write': write_data
            })
            axes[0, 2].violinplot([read_data, write_data], 
                                 positions=[1, 2],
                                 showmeans=True)
            axes[0, 2].set_title('Cache - Latency Distribution')
            axes[0, 2].set_ylabel('Latency (ms)')
            axes[0, 2].set_xticks([1, 2])
            axes[0, 2].set_xticklabels(['Read', 'Write'])
            
            # Percentiles
            percentiles = [50, 75, 90, 95, 99]
            read_percentiles = [np.percentile(read_data, p) for p in percentiles]
            write_percentiles = [np.percentile(write_data, p) for p in percentiles]
            
            x = np.arange(len(percentiles))
            width = 0.35
            
            axes[1, 2].bar(x - width/2, read_percentiles, width, label='Read')
            axes[1, 2].bar(x + width/2, write_percentiles, width, label='Write')
            axes[1, 2].set_title('Cache - Percentile Latencies')
            axes[1, 2].set_xlabel('Percentile')
            axes[1, 2].set_ylabel('Latency (ms)')
            axes[1, 2].set_xticks(x)
            axes[1, 2].set_xticklabels([f'P{p}' for p in percentiles])
            axes[1, 2].legend()
        
        plt.tight_layout()
        plt.savefig('performance_analysis.png', dpi=300, bbox_inches='tight')
        print("Plot saved as performance_analysis.png")
        
        plt.show()
    
    def save_results(self, filename='benchmark_results.json'):
        """Save results to JSON"""
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = {}
        for key, value in self.results.items():
            if isinstance(value, dict):
                serializable_results[key] = {
                    k: [float(x) for x in v] for k, v in value.items()
                }
            else:
                serializable_results[key] = [float(x) for x in value]
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to {filename}")


async def main():
    """Run all benchmarks"""
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks
    await benchmark.benchmark_lock_manager(num_operations=500)
    await benchmark.benchmark_queue(num_operations=500)
    await benchmark.benchmark_cache(num_operations=500)
    
    # Generate visualizations
    benchmark.generate_plots()
    
    # Save results
    benchmark.save_results()


if __name__ == "__main__":
    asyncio.run(main())
