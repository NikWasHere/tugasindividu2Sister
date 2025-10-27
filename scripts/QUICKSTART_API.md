# Quick Start Guide - API Client Testing

## Prerequisites

```powershell
# Install dependencies
pip install -r requirements.txt

# Start Docker cluster
cd docker
docker-compose up -d
cd ..

# Wait 30 seconds for containers to be ready
Start-Sleep -Seconds 30
```

## Usage Examples

### 1. Interactive Mode (Recommended)

```powershell
python scripts/api_client.py --interactive
```

Menu akan muncul dengan opsi:
- `1` - Test Lock Manager
- `2` - Test Queue System
- `3` - Test Cache System
- `4` - Check System Health
- `5` - Switch to next node
- `6` - Run all demos
- `q` - Quit

### 2. Run All Demos Automatically

```powershell
python scripts/api_client.py --demo
```

Akan menjalankan semua demo scenario secara berurutan.

### 3. Test Specific Component

```powershell
# Test Lock Manager only
python scripts/api_client.py --test-locks

# Test Queue System only
python scripts/api_client.py --test-queue

# Test Cache System only
python scripts/api_client.py --test-cache

# Test System Health only
python scripts/api_client.py --test-health
```

### 4. Custom Node URLs

```powershell
python scripts/api_client.py --nodes http://node1:8001 http://node2:8002 http://node3:8003
```

## API Examples

### Lock Manager

**Acquire Lock:**
```python
from scripts.api_client import DistributedSyncClient

client = DistributedSyncClient()

# Acquire exclusive lock
result = client.acquire_lock(
    resource_id="database-1",
    transaction_id="tx-001",
    lock_type="exclusive",
    timeout=30
)

lock_id = result["data"]["lock_id"]

# Release lock
client.release_lock(
    resource_id="database-1",
    transaction_id="tx-001",
    lock_id=lock_id
)
```

### Queue System

**Produce & Consume:**
```python
# Produce message
result = client.produce_message(
    topic="orders",
    message={"order_id": "ORD-001", "product": "Laptop"},
    priority=1
)

# Consume messages
result = client.consume_messages(
    topic="orders",
    consumer_id="consumer-1",
    max_messages=10
)

messages = result["data"]["messages"]
message_ids = [msg["message_id"] for msg in messages]

# Acknowledge messages
client.acknowledge_messages(
    topic="orders",
    message_ids=message_ids,
    consumer_id="consumer-1"
)
```

### Cache System

**Read & Write:**
```python
# Write to cache
client.cache_write(
    key="user:1001",
    value={"name": "John Doe", "email": "john@example.com"},
    ttl=300
)

# Read from cache
result = client.cache_read(key="user:1001")
data = result["data"]["value"]

# Invalidate cache
client.cache_invalidate(key="user:1001")
```

## Automated Testing

```powershell
# Run all tests
python scripts/automated_test.py --all

# Run specific tests
python scripts/automated_test.py --unit
python scripts/automated_test.py --integration
python scripts/automated_test.py --performance
python scripts/automated_test.py --docker
```

## Troubleshooting

### Container not responding

```powershell
cd docker
docker-compose restart
docker-compose logs -f node-1
```

### Check container health

```powershell
docker-compose ps
docker inspect distributed-sync-node-1-1 --format '{{.State.Health.Status}}'
```

### View logs

```powershell
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f node-1
```

## Video Recording Tips

1. **Prepare terminals:**
   - Terminal 1: Docker logs (`docker-compose logs -f`)
   - Terminal 2: API client (`python scripts/api_client.py -i`)
   - Terminal 3: Monitoring (`watch -n 1 docker-compose ps`)

2. **Run demo in order:**
   - Start with system health check
   - Demo lock manager with conflicts
   - Demo queue produce/consume
   - Demo cache with MESI states
   - Show performance metrics

3. **Show interesting scenarios:**
   - Lock conflicts between transactions
   - Multiple shared locks
   - Queue message persistence
   - Cache invalidation across nodes
   - Leader election (stop leader container)

## Performance Testing

```powershell
# Run performance benchmarks
python benchmarks/performance_benchmark.py

# Run load tests
cd benchmarks
locust -f load_test_scenarios.py --host=http://localhost:8001
```

Open browser: http://localhost:8089

## Clean Up

```powershell
# Stop containers
cd docker
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v

# Remove all data
docker-compose down -v --rmi all
```
