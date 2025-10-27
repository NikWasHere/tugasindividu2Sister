#!/usr/bin/env python3
"""
Simple API Test Examples
=========================
Contoh sederhana untuk testing API tanpa dependency berat.
Bisa dijalankan langsung dengan requests library.
"""

import requests
import json
import time

# Configuration
BASE_URLS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003"
]

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text}")
    print(f"{'='*60}\n")

# ==================== EXAMPLE 1: HEALTH CHECK ====================

def test_health_check():
    """Test health check endpoint"""
    print("\n🏥 Testing Health Check...")
    
    for i, url in enumerate(BASE_URLS):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            print_response(response, f"Node {i+1} Health")
        except Exception as e:
            print(f"❌ Node {i+1} ({url}) failed: {e}")

# ==================== EXAMPLE 2: LOCK MANAGER ====================

def test_lock_manager():
    """Test distributed lock manager"""
    print("\n🔒 Testing Lock Manager...")
    
    # Acquire exclusive lock
    print("Step 1: Acquire exclusive lock on 'database-1'")
    response = requests.post(
        f"{BASE_URLS[0]}/lock/acquire",
        json={
            "resource_id": "database-1",
            "transaction_id": "tx-001",
            "lock_type": "exclusive",
            "timeout": 30
        }
    )
    print_response(response, "Acquire Lock (Node 1)")
    
    if response.status_code == 200:
        lock_id = response.json().get("lock_id")
        
        # Try to acquire same lock from another node (should fail/wait)
        print("Step 2: Try to acquire same lock from Node 2 (should conflict)")
        response2 = requests.post(
            f"{BASE_URLS[1]}/lock/acquire",
            json={
                "resource_id": "database-1",
                "transaction_id": "tx-002",
                "lock_type": "exclusive",
                "timeout": 5
            }
        )
        print_response(response2, "Acquire Lock (Node 2) - Conflict Expected")
        
        # Release lock
        print("Step 3: Release lock")
        time.sleep(1)
        response3 = requests.post(
            f"{BASE_URLS[0]}/lock/release",
            json={
                "resource_id": "database-1",
                "transaction_id": "tx-001",
                "lock_id": lock_id
            }
        )
        print_response(response3, "Release Lock")
    
    # Test shared locks
    print("\nStep 4: Test multiple shared locks")
    response4 = requests.post(
        f"{BASE_URLS[0]}/lock/acquire",
        json={
            "resource_id": "file-1",
            "transaction_id": "tx-003",
            "lock_type": "shared",
            "timeout": 30
        }
    )
    print_response(response4, "Shared Lock 1 (Node 1)")
    
    response5 = requests.post(
        f"{BASE_URLS[1]}/lock/acquire",
        json={
            "resource_id": "file-1",
            "transaction_id": "tx-004",
            "lock_type": "shared",
            "timeout": 30
        }
    )
    print_response(response5, "Shared Lock 2 (Node 2) - Should Succeed")

# ==================== EXAMPLE 3: QUEUE SYSTEM ====================

def test_queue_system():
    """Test distributed queue system"""
    print("\n📬 Testing Queue System...")
    
    topic = "test-orders"
    
    # Produce messages
    print("Step 1: Produce messages")
    messages = [
        {"order_id": "ORD-001", "product": "Laptop", "price": 15000000},
        {"order_id": "ORD-002", "product": "Mouse", "price": 250000},
        {"order_id": "ORD-003", "product": "Keyboard", "price": 750000},
    ]
    
    produced_ids = []
    for i, msg in enumerate(messages):
        response = requests.post(
            f"{BASE_URLS[i % 3]}/queue/produce",
            json={
                "topic": topic,
                "message": msg,
                "priority": 1
            }
        )
        print_response(response, f"Produce Message {i+1}")
        if response.status_code == 200:
            produced_ids.append(response.json().get("message_id"))
        time.sleep(0.5)
    
    # Get queue stats
    print("\nStep 2: Get queue statistics")
    time.sleep(1)
    response = requests.get(
        f"{BASE_URLS[0]}/queue/stats",
        params={"topic": topic}
    )
    print_response(response, "Queue Stats")
    
    # Consume messages
    print("\nStep 3: Consume messages")
    time.sleep(1)
    response = requests.post(
        f"{BASE_URLS[1]}/queue/consume",
        json={
            "topic": topic,
            "consumer_id": "consumer-test-1",
            "max_messages": 2
        }
    )
    print_response(response, "Consume Messages")
    
    if response.status_code == 200:
        consumed = response.json().get("messages", [])
        message_ids = [msg["message_id"] for msg in consumed]
        
        # Acknowledge messages
        print("\nStep 4: Acknowledge messages")
        time.sleep(1)
        response = requests.post(
            f"{BASE_URLS[1]}/queue/acknowledge",
            json={
                "topic": topic,
                "message_ids": message_ids,
                "consumer_id": "consumer-test-1"
            }
        )
        print_response(response, "Acknowledge Messages")

# ==================== EXAMPLE 4: CACHE SYSTEM ====================

def test_cache_system():
    """Test distributed cache with MESI protocol"""
    print("\n💾 Testing Cache System...")
    
    # Write to cache
    print("Step 1: Write to cache (Node 1)")
    response = requests.post(
        f"{BASE_URLS[0]}/cache/write",
        json={
            "key": "user:test-1001",
            "value": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            },
            "ttl": 300
        }
    )
    print_response(response, "Write to Cache")
    
    # Read from different node
    print("\nStep 2: Read from different node (Node 2)")
    time.sleep(1)
    response = requests.get(
        f"{BASE_URLS[1]}/cache/read",
        params={"key": "user:test-1001"}
    )
    print_response(response, "Read from Cache (Node 2)")
    
    # Update value (invalidates other caches)
    print("\nStep 3: Update value (Node 1) - Should invalidate Node 2 cache")
    time.sleep(1)
    response = requests.post(
        f"{BASE_URLS[0]}/cache/write",
        json={
            "key": "user:test-1001",
            "value": {
                "name": "John Doe Updated",
                "email": "john.new@example.com",
                "age": 31
            }
        }
    )
    print_response(response, "Update Cache")
    
    # Read updated value
    print("\nStep 4: Read updated value (Node 2)")
    time.sleep(1)
    response = requests.get(
        f"{BASE_URLS[1]}/cache/read",
        params={"key": "user:test-1001"}
    )
    print_response(response, "Read Updated Value")
    
    # Get cache stats
    print("\nStep 5: Get cache statistics")
    response = requests.get(f"{BASE_URLS[0]}/cache/stats")
    print_response(response, "Cache Stats")
    
    # Invalidate cache
    print("\nStep 6: Invalidate cache entry")
    response = requests.post(
        f"{BASE_URLS[0]}/cache/invalidate",
        json={"key": "user:test-1001"}
    )
    print_response(response, "Invalidate Cache")

# ==================== EXAMPLE 5: RAFT STATUS ====================

def test_raft_status():
    """Test Raft consensus status"""
    print("\n⚙️  Testing Raft Status...")
    
    for i, url in enumerate(BASE_URLS):
        try:
            response = requests.get(f"{url}/raft/status", timeout=5)
            print_response(response, f"Node {i+1} Raft Status")
        except Exception as e:
            print(f"❌ Node {i+1} failed: {e}")

# ==================== MAIN ====================

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 Distributed Synchronization System - API Tests")
    print("="*60)
    
    try:
        # Check if servers are running
        print("\n📡 Checking server availability...")
        for i, url in enumerate(BASE_URLS):
            try:
                requests.get(f"{url}/health", timeout=2)
                print(f"✅ Node {i+1} ({url}) is available")
            except:
                print(f"❌ Node {i+1} ({url}) is NOT available")
                print(f"\n⚠️  Please start Docker containers first:")
                print(f"   cd docker")
                print(f"   docker-compose up -d")
                return
        
        # Run tests
        print("\n" + "="*60)
        input("Press ENTER to start tests...")
        
        test_health_check()
        input("\nPress ENTER to continue to Lock Manager tests...")
        
        test_lock_manager()
        input("\nPress ENTER to continue to Queue System tests...")
        
        test_queue_system()
        input("\nPress ENTER to continue to Cache System tests...")
        
        test_cache_system()
        input("\nPress ENTER to continue to Raft Status check...")
        
        test_raft_status()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
