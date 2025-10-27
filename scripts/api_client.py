#!/usr/bin/env python3
"""
API Client untuk Testing - Distributed Synchronization System
==============================================================
Client interaktif untuk testing semua API endpoints:
- Distributed Lock Manager
- Distributed Queue System
- Distributed Cache Coherence

Usage:
    python scripts/api_client.py --interactive
    python scripts/api_client.py --demo
    python scripts/api_client.py --test-locks
    python scripts/api_client.py --test-queue
    python scripts/api_client.py --test-cache
"""

import asyncio
import argparse
import sys
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from requests.exceptions import RequestException
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)


class DistributedSyncClient:
    """Client untuk berinteraksi dengan Distributed Synchronization System"""
    
    def __init__(self, base_urls: List[str] = None):
        self.base_urls = base_urls or [
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:8003"
        ]
        self.current_node = 0
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "DistributedSyncClient/1.0"
        })
        
    def get_base_url(self, node_id: Optional[int] = None) -> str:
        """Get base URL for specific node or current node"""
        if node_id is not None:
            return self.base_urls[node_id % len(self.base_urls)]
        return self.base_urls[self.current_node % len(self.base_urls)]
    
    def next_node(self):
        """Switch to next node (round-robin)"""
        self.current_node = (self.current_node + 1) % len(self.base_urls)
        logger.info(f"Switched to node {self.current_node + 1}: {self.get_base_url()}")
    
    def request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        node_id: Optional[int] = None,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.get_base_url(node_id)}{endpoint}"
        
        try:
            logger.info(f"{method.upper()} {url}")
            if data:
                logger.debug(f"Request body: {json.dumps(data, indent=2)}")
            
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                timeout=timeout
            )
            
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code >= 200 and response.status_code < 300:
                result = response.json() if response.content else {}
                logger.success(f"Success: {json.dumps(result, indent=2)}")
                return {"success": True, "data": result, "status": response.status_code}
            else:
                error = response.json() if response.content else {"error": "Unknown error"}
                logger.error(f"Error: {json.dumps(error, indent=2)}")
                return {"success": False, "error": error, "status": response.status_code}
                
        except RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"success": False, "error": str(e), "status": 0}
    
    # ==================== LOCK MANAGER APIs ====================
    
    def acquire_lock(
        self,
        resource_id: str,
        transaction_id: str,
        lock_type: str = "exclusive",
        timeout: int = 30,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Acquire a distributed lock"""
        logger.info(f"📌 Acquiring {lock_type} lock on '{resource_id}' for transaction '{transaction_id}'")
        
        return self.request(
            "POST",
            "/lock/acquire",
            data={
                "resource_id": resource_id,
                "transaction_id": transaction_id,
                "lock_type": lock_type,
                "timeout": timeout
            },
            node_id=node_id
        )
    
    def release_lock(
        self,
        resource_id: str,
        transaction_id: str,
        lock_id: str,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Release a distributed lock"""
        logger.info(f"🔓 Releasing lock '{lock_id}' on '{resource_id}'")
        
        return self.request(
            "POST",
            "/lock/release",
            data={
                "resource_id": resource_id,
                "transaction_id": transaction_id,
                "lock_id": lock_id
            },
            node_id=node_id
        )
    
    def get_lock_status(
        self,
        resource_id: str,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get lock status for a resource"""
        logger.info(f"ℹ️  Getting lock status for '{resource_id}'")
        
        return self.request(
            "GET",
            f"/lock/status",
            params={"resource_id": resource_id},
            node_id=node_id
        )
    
    # ==================== QUEUE SYSTEM APIs ====================
    
    def produce_message(
        self,
        topic: str,
        message: Dict,
        priority: int = 1,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Produce a message to queue"""
        logger.info(f"📤 Producing message to topic '{topic}'")
        
        return self.request(
            "POST",
            "/queue/produce",
            data={
                "topic": topic,
                "message": message,
                "priority": priority
            },
            node_id=node_id
        )
    
    def consume_messages(
        self,
        topic: str,
        consumer_id: str,
        max_messages: int = 10,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Consume messages from queue"""
        logger.info(f"📥 Consuming messages from topic '{topic}' (consumer: {consumer_id})")
        
        return self.request(
            "POST",
            "/queue/consume",
            data={
                "topic": topic,
                "consumer_id": consumer_id,
                "max_messages": max_messages
            },
            node_id=node_id
        )
    
    def acknowledge_messages(
        self,
        topic: str,
        message_ids: List[str],
        consumer_id: str,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Acknowledge processed messages"""
        logger.info(f"✅ Acknowledging {len(message_ids)} messages from topic '{topic}'")
        
        return self.request(
            "POST",
            "/queue/acknowledge",
            data={
                "topic": topic,
                "message_ids": message_ids,
                "consumer_id": consumer_id
            },
            node_id=node_id
        )
    
    def get_queue_stats(
        self,
        topic: str,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get queue statistics"""
        logger.info(f"📊 Getting stats for topic '{topic}'")
        
        return self.request(
            "GET",
            "/queue/stats",
            params={"topic": topic},
            node_id=node_id
        )
    
    # ==================== CACHE SYSTEM APIs ====================
    
    def cache_read(
        self,
        key: str,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read from distributed cache"""
        logger.info(f"📖 Reading key '{key}' from cache")
        
        return self.request(
            "GET",
            "/cache/read",
            params={"key": key},
            node_id=node_id
        )
    
    def cache_write(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Write to distributed cache"""
        logger.info(f"✏️  Writing key '{key}' to cache")
        
        data = {"key": key, "value": value}
        if ttl:
            data["ttl"] = ttl
        
        return self.request(
            "POST",
            "/cache/write",
            data=data,
            node_id=node_id
        )
    
    def cache_invalidate(
        self,
        key: str,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Invalidate cache entry"""
        logger.info(f"❌ Invalidating key '{key}' from cache")
        
        return self.request(
            "POST",
            "/cache/invalidate",
            data={"key": key},
            node_id=node_id
        )
    
    def cache_stats(
        self,
        node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get cache statistics"""
        logger.info(f"📊 Getting cache stats")
        
        return self.request(
            "GET",
            "/cache/stats",
            node_id=node_id
        )
    
    # ==================== SYSTEM APIs ====================
    
    def health_check(self, node_id: Optional[int] = None) -> Dict[str, Any]:
        """Check node health"""
        return self.request("GET", "/health", node_id=node_id)
    
    def get_metrics(self, node_id: Optional[int] = None) -> Dict[str, Any]:
        """Get Prometheus metrics"""
        return self.request("GET", "/metrics", node_id=node_id)
    
    def raft_status(self, node_id: Optional[int] = None) -> Dict[str, Any]:
        """Get Raft consensus status"""
        return self.request("GET", "/raft/status", node_id=node_id)


# ==================== DEMO SCENARIOS ====================

def demo_lock_manager(client: DistributedSyncClient):
    """Demo: Distributed Lock Manager"""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: DISTRIBUTED LOCK MANAGER")
    logger.info("=" * 80)
    
    # Scenario 1: Acquire exclusive lock
    logger.info("\n--- Scenario 1: Acquire Exclusive Lock ---")
    result1 = client.acquire_lock(
        resource_id="database-1",
        transaction_id="tx-001",
        lock_type="exclusive",
        timeout=30,
        node_id=0
    )
    
    if result1["success"]:
        lock_id_1 = result1["data"].get("lock_id")
        
        # Scenario 2: Try to acquire same resource (should conflict)
        logger.info("\n--- Scenario 2: Try to Acquire Same Resource (Conflict) ---")
        time.sleep(1)
        result2 = client.acquire_lock(
            resource_id="database-1",
            transaction_id="tx-002",
            lock_type="exclusive",
            timeout=5,
            node_id=1
        )
        
        # Scenario 3: Release first lock
        logger.info("\n--- Scenario 3: Release First Lock ---")
        time.sleep(1)
        client.release_lock(
            resource_id="database-1",
            transaction_id="tx-001",
            lock_id=lock_id_1,
            node_id=0
        )
    
    # Scenario 4: Shared locks
    logger.info("\n--- Scenario 4: Multiple Shared Locks ---")
    time.sleep(1)
    client.acquire_lock(
        resource_id="file-1",
        transaction_id="tx-003",
        lock_type="shared",
        node_id=0
    )
    time.sleep(0.5)
    client.acquire_lock(
        resource_id="file-1",
        transaction_id="tx-004",
        lock_type="shared",
        node_id=1
    )
    
    # Check status
    logger.info("\n--- Check Lock Status ---")
    time.sleep(1)
    client.get_lock_status("file-1", node_id=0)


def demo_queue_system(client: DistributedSyncClient):
    """Demo: Distributed Queue System"""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: DISTRIBUTED QUEUE SYSTEM")
    logger.info("=" * 80)
    
    topic = "orders"
    
    # Scenario 1: Produce messages
    logger.info("\n--- Scenario 1: Produce Messages ---")
    messages = [
        {"order_id": "ORD-001", "product": "Laptop", "quantity": 2, "price": 15000000},
        {"order_id": "ORD-002", "product": "Mouse", "quantity": 5, "price": 250000},
        {"order_id": "ORD-003", "product": "Keyboard", "quantity": 3, "price": 750000},
    ]
    
    for i, msg in enumerate(messages):
        client.produce_message(
            topic=topic,
            message=msg,
            priority=i % 2 + 1,
            node_id=i % 3
        )
        time.sleep(0.5)
    
    # Scenario 2: Get queue stats
    logger.info("\n--- Scenario 2: Get Queue Stats ---")
    time.sleep(1)
    client.get_queue_stats(topic, node_id=0)
    
    # Scenario 3: Consume messages
    logger.info("\n--- Scenario 3: Consume Messages ---")
    time.sleep(1)
    result = client.consume_messages(
        topic=topic,
        consumer_id="consumer-1",
        max_messages=2,
        node_id=1
    )
    
    if result["success"]:
        consumed_messages = result["data"].get("messages", [])
        message_ids = [msg["message_id"] for msg in consumed_messages]
        
        # Scenario 4: Acknowledge messages
        logger.info("\n--- Scenario 4: Acknowledge Messages ---")
        time.sleep(1)
        if message_ids:
            client.acknowledge_messages(
                topic=topic,
                message_ids=message_ids,
                consumer_id="consumer-1",
                node_id=1
            )


def demo_cache_system(client: DistributedSyncClient):
    """Demo: Distributed Cache Coherence"""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: DISTRIBUTED CACHE COHERENCE (MESI)")
    logger.info("=" * 80)
    
    # Scenario 1: Write to cache
    logger.info("\n--- Scenario 1: Write to Cache (Node 1) ---")
    client.cache_write(
        key="user:1001",
        value={"name": "John Doe", "email": "john@example.com", "age": 30},
        ttl=300,
        node_id=0
    )
    
    # Scenario 2: Read from different node
    logger.info("\n--- Scenario 2: Read from Different Node (Node 2) ---")
    time.sleep(1)
    client.cache_read(key="user:1001", node_id=1)
    
    # Scenario 3: Write again (invalidates other caches)
    logger.info("\n--- Scenario 3: Update Value (Node 1) - Invalidates Node 2 ---")
    time.sleep(1)
    client.cache_write(
        key="user:1001",
        value={"name": "John Doe Updated", "email": "john.new@example.com", "age": 31},
        node_id=0
    )
    
    # Scenario 4: Read updated value from node 2
    logger.info("\n--- Scenario 4: Read Updated Value (Node 2) ---")
    time.sleep(1)
    client.cache_read(key="user:1001", node_id=1)
    
    # Scenario 5: Write multiple keys
    logger.info("\n--- Scenario 5: Write Multiple Keys ---")
    time.sleep(1)
    client.cache_write(key="product:2001", value={"name": "Laptop", "price": 15000000}, node_id=0)
    time.sleep(0.5)
    client.cache_write(key="product:2002", value={"name": "Mouse", "price": 250000}, node_id=1)
    
    # Scenario 6: Get cache stats
    logger.info("\n--- Scenario 6: Get Cache Stats ---")
    time.sleep(1)
    client.cache_stats(node_id=0)
    
    # Scenario 7: Invalidate cache
    logger.info("\n--- Scenario 7: Invalidate Cache Entry ---")
    time.sleep(1)
    client.cache_invalidate(key="user:1001", node_id=0)


def demo_system_health(client: DistributedSyncClient):
    """Demo: System Health and Status"""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: SYSTEM HEALTH & RAFT STATUS")
    logger.info("=" * 80)
    
    for i in range(3):
        logger.info(f"\n--- Node {i + 1} Status ---")
        client.health_check(node_id=i)
        time.sleep(0.5)
        client.raft_status(node_id=i)
        time.sleep(1)


def interactive_mode(client: DistributedSyncClient):
    """Interactive CLI mode"""
    logger.info("\n" + "=" * 80)
    logger.info("INTERACTIVE MODE - Distributed Synchronization Client")
    logger.info("=" * 80)
    
    commands = {
        "1": ("Lock Manager", demo_lock_manager),
        "2": ("Queue System", demo_queue_system),
        "3": ("Cache System", demo_cache_system),
        "4": ("System Health", demo_system_health),
        "5": ("Switch Node", lambda c: c.next_node()),
        "6": ("Run All Demos", lambda c: run_all_demos(c)),
        "q": ("Quit", None)
    }
    
    while True:
        print("\n" + "-" * 80)
        print(f"Current Node: Node {client.current_node + 1} ({client.get_base_url()})")
        print("-" * 80)
        print("Available Commands:")
        for key, (desc, _) in commands.items():
            print(f"  {key}. {desc}")
        print("-" * 80)
        
        choice = input("\nEnter command: ").strip().lower()
        
        if choice == "q":
            logger.info("Exiting interactive mode...")
            break
        
        if choice in commands:
            _, func = commands[choice]
            if func:
                try:
                    func(client)
                except Exception as e:
                    logger.error(f"Error executing command: {e}")
        else:
            logger.warning(f"Invalid command: {choice}")


def run_all_demos(client: DistributedSyncClient):
    """Run all demo scenarios"""
    demo_system_health(client)
    time.sleep(2)
    demo_lock_manager(client)
    time.sleep(2)
    demo_queue_system(client)
    time.sleep(2)
    demo_cache_system(client)
    
    logger.success("\n✅ All demos completed!")


def main():
    parser = argparse.ArgumentParser(description="API Client for Distributed Synchronization System")
    parser.add_argument("--nodes", nargs="+", default=None, help="Base URLs of nodes")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--demo", "-d", action="store_true", help="Run all demos")
    parser.add_argument("--test-locks", action="store_true", help="Test lock manager only")
    parser.add_argument("--test-queue", action="store_true", help="Test queue system only")
    parser.add_argument("--test-cache", action="store_true", help="Test cache system only")
    parser.add_argument("--test-health", action="store_true", help="Test system health only")
    
    args = parser.parse_args()
    
    # Create client
    client = DistributedSyncClient(base_urls=args.nodes)
    
    logger.info("🚀 Distributed Synchronization API Client")
    logger.info(f"📡 Nodes: {', '.join(client.base_urls)}")
    
    try:
        if args.interactive:
            interactive_mode(client)
        elif args.demo:
            run_all_demos(client)
        elif args.test_locks:
            demo_lock_manager(client)
        elif args.test_queue:
            demo_queue_system(client)
        elif args.test_cache:
            demo_cache_system(client)
        elif args.test_health:
            demo_system_health(client)
        else:
            # Default: interactive mode
            interactive_mode(client)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
