#!/usr/bin/env python3
"""
Mock API Server untuk Demo Video
==================================
Server sederhana yang mensimulasikan distributed synchronization system
untuk keperluan video demonstration.
"""

from flask import Flask, request, jsonify
import uuid
import time
from datetime import datetime
import random
from threading import Lock

# Data storage
locks = {}
queue_messages = {}
cache_data = {}
raft_state = {"state": "leader", "term": 1, "leader_id": "node-1"}

# Thread locks
lock_lock = Lock()
queue_lock = Lock()
cache_lock = Lock()

def create_app(node_id, port):
    app = Flask(f"node-{node_id}")
    
    # Health endpoint
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            "status": "healthy",
            "node_id": node_id,
            "timestamp": datetime.now().isoformat()
        })
    
    # Raft status
    @app.route('/raft/status', methods=['GET'])
    def raft_status():
        return jsonify({
            "node_id": node_id,
            "state": raft_state["state"] if node_id == 1 else "follower",
            "term": raft_state["term"],
            "leader_id": raft_state["leader_id"]
        })
    
    # Lock Manager - Acquire
    @app.route('/lock/acquire', methods=['POST'])
    def acquire_lock():
        data = request.json
        resource_id = data.get('resource_id')
        transaction_id = data.get('transaction_id')
        lock_type = data.get('lock_type', 'exclusive')
        
        with lock_lock:
            # Check if resource is locked
            if resource_id in locks:
                existing = locks[resource_id]
                if lock_type == 'exclusive' or existing['lock_type'] == 'exclusive':
                    return jsonify({
                        "success": False,
                        "error": "Resource already locked",
                        "existing_lock": existing
                    }), 409
                # Allow multiple shared locks
                elif lock_type == 'shared':
                    lock_id = str(uuid.uuid4())
                    existing['holders'].append({
                        "transaction_id": transaction_id,
                        "lock_id": lock_id
                    })
                    return jsonify({
                        "success": True,
                        "lock_id": lock_id,
                        "resource_id": resource_id,
                        "lock_type": lock_type,
                        "acquired_at": datetime.now().isoformat()
                    })
            
            # Create new lock
            lock_id = str(uuid.uuid4())
            locks[resource_id] = {
                "resource_id": resource_id,
                "transaction_id": transaction_id,
                "lock_type": lock_type,
                "lock_id": lock_id,
                "acquired_at": datetime.now().isoformat(),
                "holders": [{"transaction_id": transaction_id, "lock_id": lock_id}]
            }
            
            return jsonify({
                "success": True,
                "lock_id": lock_id,
                "resource_id": resource_id,
                "lock_type": lock_type,
                "acquired_at": datetime.now().isoformat()
            })
    
    # Lock Manager - Release
    @app.route('/lock/release', methods=['POST'])
    def release_lock():
        data = request.json
        resource_id = data.get('resource_id')
        lock_id = data.get('lock_id')
        
        with lock_lock:
            if resource_id in locks:
                del locks[resource_id]
                return jsonify({
                    "success": True,
                    "message": "Lock released",
                    "resource_id": resource_id
                })
            return jsonify({
                "success": False,
                "error": "Lock not found"
            }), 404
    
    # Lock Manager - Status
    @app.route('/lock/status', methods=['GET'])
    def lock_status():
        resource_id = request.args.get('resource_id')
        with lock_lock:
            if resource_id in locks:
                return jsonify(locks[resource_id])
            return jsonify({
                "resource_id": resource_id,
                "locked": False
            })
    
    # Queue - Produce
    @app.route('/queue/produce', methods=['POST'])
    def produce_message():
        data = request.json
        topic = data.get('topic')
        message = data.get('message')
        priority = data.get('priority', 1)
        
        message_id = str(uuid.uuid4())
        
        with queue_lock:
            if topic not in queue_messages:
                queue_messages[topic] = []
            
            queue_messages[topic].append({
                "message_id": message_id,
                "message": message,
                "priority": priority,
                "produced_at": datetime.now().isoformat(),
                "consumed": False
            })
        
        return jsonify({
            "success": True,
            "message_id": message_id,
            "topic": topic
        })
    
    # Queue - Consume
    @app.route('/queue/consume', methods=['POST'])
    def consume_messages():
        data = request.json
        topic = data.get('topic')
        max_messages = data.get('max_messages', 10)
        
        with queue_lock:
            if topic not in queue_messages:
                return jsonify({
                    "success": True,
                    "messages": [],
                    "count": 0
                })
            
            available = [m for m in queue_messages[topic] if not m['consumed']]
            to_consume = available[:max_messages]
            
            for msg in to_consume:
                msg['consumed'] = True
                msg['consumed_at'] = datetime.now().isoformat()
            
            return jsonify({
                "success": True,
                "messages": to_consume,
                "count": len(to_consume)
            })
    
    # Queue - Acknowledge
    @app.route('/queue/acknowledge', methods=['POST'])
    def acknowledge_messages():
        data = request.json
        topic = data.get('topic')
        message_ids = data.get('message_ids', [])
        
        with queue_lock:
            if topic in queue_messages:
                queue_messages[topic] = [
                    m for m in queue_messages[topic]
                    if m['message_id'] not in message_ids
                ]
        
        return jsonify({
            "success": True,
            "acknowledged": len(message_ids)
        })
    
    # Queue - Stats
    @app.route('/queue/stats', methods=['GET'])
    def queue_stats():
        topic = request.args.get('topic')
        
        with queue_lock:
            if topic not in queue_messages:
                return jsonify({
                    "topic": topic,
                    "total_messages": 0,
                    "consumed": 0,
                    "pending": 0
                })
            
            messages = queue_messages[topic]
            consumed_count = sum(1 for m in messages if m['consumed'])
            
            return jsonify({
                "topic": topic,
                "total_messages": len(messages),
                "consumed": consumed_count,
                "pending": len(messages) - consumed_count
            })
    
    # Cache - Read
    @app.route('/cache/read', methods=['GET'])
    def cache_read():
        key = request.args.get('key')
        
        with cache_lock:
            if key in cache_data:
                entry = cache_data[key]
                return jsonify({
                    "success": True,
                    "key": key,
                    "value": entry['value'],
                    "state": entry.get('state', 'shared'),
                    "cached_at": entry.get('cached_at')
                })
            
            return jsonify({
                "success": False,
                "error": "Cache miss",
                "key": key
            }), 404
    
    # Cache - Write
    @app.route('/cache/write', methods=['POST'])
    def cache_write():
        data = request.json
        key = data.get('key')
        value = data.get('value')
        ttl = data.get('ttl')
        
        with cache_lock:
            cache_data[key] = {
                "key": key,
                "value": value,
                "state": "modified",
                "cached_at": datetime.now().isoformat(),
                "ttl": ttl
            }
        
        return jsonify({
            "success": True,
            "key": key,
            "state": "modified",
            "invalidated_nodes": 2  
        })
    
    # Cache - Invalidate
    @app.route('/cache/invalidate', methods=['POST'])
    def cache_invalidate():
        data = request.json
        key = data.get('key')
        
        with cache_lock:
            if key in cache_data:
                del cache_data[key]
                return jsonify({
                    "success": True,
                    "key": key,
                    "invalidated": True
                })
            return jsonify({
                "success": False,
                "error": "Key not found"
            }), 404
    
    # Cache - Stats
    @app.route('/cache/stats', methods=['GET'])
    def cache_stats():
        with cache_lock:
            return jsonify({
                "total_entries": len(cache_data),
                "memory_usage_bytes": sum(len(str(v)) for v in cache_data.values()),
                "hit_rate": round(random.uniform(0.85, 0.95), 2),
                "miss_rate": round(random.uniform(0.05, 0.15), 2)
            })
    
    # Metrics (simplified)
    @app.route('/metrics', methods=['GET'])
    def metrics():
        return f"""# HELP node_health Node health status
# TYPE node_health gauge
node_health{{node="{node_id}"}} 1

# HELP lock_operations_total Total lock operations
# TYPE lock_operations_total counter
lock_operations_total{{node="{node_id}"}} {random.randint(100, 1000)}

# HELP queue_messages_total Total queue messages
# TYPE queue_messages_total counter
queue_messages_total{{node="{node_id}"}} {random.randint(500, 5000)}

# HELP cache_hits_total Total cache hits
# TYPE cache_hits_total counter
cache_hits_total{{node="{node_id}"}} {random.randint(1000, 10000)}
"""
    
    return app

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python mock_server.py <node_id> <port>")
        sys.exit(1)
    
    node_id = int(sys.argv[1])
    port = int(sys.argv[2])
    
    app = create_app(node_id, port)
    print(f"Starting Mock Node {node_id} on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
