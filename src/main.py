"""
Main application entry point
Menjalankan distributed synchronization system
"""

import asyncio
import argparse
import signal
import sys
from loguru import logger

from src.nodes.lock_manager import LockManager
from src.nodes.queue_node import QueueNode
from src.nodes.cache_node import CacheNode
from src.utils.logger import setup_logger
from src.utils.config import Config


class DistributedSystem:
    """Main distributed system orchestrator"""
    
    def __init__(self, node_id: str, node_type: str = "all"):
        self.node_id = node_id
        self.node_type = node_type
        
        # Initialize logger
        setup_logger(node_id)
        
        # Initialize nodes based on type
        self.lock_manager = None
        self.queue_node = None
        self.cache_node = None
        
        if node_type in ["all", "lock"]:
            self.lock_manager = LockManager(node_id)
        
        if node_type in ["all", "queue"]:
            self.queue_node = QueueNode(node_id)
        
        if node_type in ["all", "cache"]:
            self.cache_node = CacheNode(node_id)
        
        self.running = False
    
    async def start(self):
        """Start all nodes"""
        logger.info(f"🚀 Starting Distributed System - Node: {self.node_id}")
        
        try:
            if self.lock_manager:
                logger.info("Starting Lock Manager...")
                await self.lock_manager.start()
            
            if self.queue_node:
                logger.info("Starting Queue Node...")
                await self.queue_node.start()
            
            if self.cache_node:
                logger.info("Starting Cache Node...")
                await self.cache_node.start()
            
            self.running = True
            logger.info("✅ All nodes started successfully!")
            
            # Keep running
            await self._run()
            
        except Exception as e:
            logger.error(f"Error starting system: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop all nodes"""
        logger.info("Stopping Distributed System...")
        self.running = False
        
        if self.lock_manager:
            await self.lock_manager.stop()
        
        if self.queue_node:
            await self.queue_node.stop()
        
        if self.cache_node:
            await self.cache_node.stop()
        
        logger.info("System stopped")
    
    async def _run(self):
        """Main run loop"""
        while self.running:
            try:
                await asyncio.sleep(1)
                
                # Periodically log status
                await self._log_status()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
    
    async def _log_status(self):
        """Log system status periodically"""
        # Log every 30 seconds
        if int(asyncio.get_event_loop().time()) % 30 == 0:
            logger.info("=== System Status ===")
            
            if self.lock_manager:
                stats = self.lock_manager.get_statistics()
                logger.info(f"Lock Manager: {stats}")
            
            if self.queue_node:
                stats = self.queue_node.get_statistics()
                logger.info(f"Queue Node: {stats}")
            
            if self.cache_node:
                stats = self.cache_node.get_cache_statistics()
                logger.info(f"Cache Node: {stats}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Distributed Synchronization System")
    parser.add_argument("--node-id", required=True, help="Node ID")
    parser.add_argument("--port", type=int, help="Override port from config")
    parser.add_argument("--type", choices=["all", "lock", "queue", "cache"], 
                       default="all", help="Node type to run")
    
    args = parser.parse_args()
    
    # Override config if needed
    if args.port:
        Config.NODE_PORT = args.port
    Config.NODE_ID = args.node_id
    
    # Create system
    system = DistributedSystem(args.node_id, args.type)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(system.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await system.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
