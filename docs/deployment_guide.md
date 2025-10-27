# Deployment Guide

## Prerequisites

### Software Requirements
- **Python**: 3.8 atau lebih tinggi
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **Redis**: 7.0+ (jika tidak menggunakan Docker)
- **Git**: Untuk clone repository

### Hardware Requirements (Minimum)
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 10 GB free space
- **Network**: Stable internet connection

### Hardware Requirements (Recommended)
- **CPU**: 8+ cores
- **RAM**: 16 GB
- **Disk**: 20+ GB SSD
- **Network**: Low-latency network untuk cluster

## Installation Methods

### Method 1: Docker Compose (Recommended)

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd tugasindividu2
```

#### Step 2: Configure Environment
```bash
cp .env.example .env
# Edit .env sesuai kebutuhan
```

#### Step 3: Build Images
```bash
cd docker
docker-compose build
```

#### Step 4: Start Services
```bash
docker-compose up -d
```

#### Step 5: Verify Deployment
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f node-1

# Test health endpoint
curl http://localhost:5000/health
```

#### Step 6: Scale Nodes (Optional)
```bash
docker-compose up -d --scale node-2=2
```

### Method 2: Manual Installation

#### Step 1: Setup Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

#### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 3: Setup Redis
```bash
# Windows (using Chocolatey)
choco install redis-64

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server

# Mac (using Homebrew)
brew install redis

# Start Redis
redis-server
```

#### Step 4: Configure Cluster
Edit `.env` file untuk konfigurasi cluster:

```env
# Node 1
NODE_ID=node-1
NODE_HOST=localhost
NODE_PORT=5000
CLUSTER_NODES=node-1:localhost:5000,node-2:localhost:5001,node-3:localhost:5002
```

#### Step 5: Start Nodes

**Terminal 1 - Node 1:**
```bash
python -m src.main --node-id node-1 --port 5000
```

**Terminal 2 - Node 2:**
```bash
# Update .env: NODE_ID=node-2, NODE_PORT=5001
python -m src.main --node-id node-2 --port 5001
```

**Terminal 3 - Node 3:**
```bash
# Update .env: NODE_ID=node-3, NODE_PORT=5002
python -m src.main --node-id node-3 --port 5002
```

## Configuration

### Environment Variables

```env
# Node Configuration
NODE_ID=node-1                    # Unique node identifier
NODE_HOST=localhost               # Node hostname
NODE_PORT=5000                    # Node port

# Cluster Configuration
CLUSTER_NODES=node-1:localhost:5000,node-2:localhost:5001,node-3:localhost:5002
HEARTBEAT_INTERVAL=1.0            # Heartbeat interval (seconds)
ELECTION_TIMEOUT_MIN=5.0          # Min election timeout
ELECTION_TIMEOUT_MAX=10.0         # Max election timeout

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                   # Leave empty if no password

# Queue Configuration
QUEUE_PARTITIONS=16               # Number of queue partitions
QUEUE_REPLICATION_FACTOR=2        # Replication factor
MESSAGE_PERSISTENCE=true          # Enable message persistence

# Cache Configuration
CACHE_PROTOCOL=MESI               # Cache coherence protocol
CACHE_SIZE_MB=256                 # Cache size in MB
CACHE_REPLACEMENT_POLICY=LRU      # Replacement policy

# Performance
MAX_CONNECTIONS=1000
WORKER_THREADS=4
BUFFER_SIZE=8192

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR

# Security (Optional)
ENABLE_ENCRYPTION=false
TLS_CERT_PATH=./certs/server.crt
TLS_KEY_PATH=./certs/server.key
```

### Docker Compose Configuration

Edit `docker/docker-compose.yml` untuk customize deployment:

```yaml
services:
  node-1:
    environment:
      - NODE_ID=node-1
      - NODE_PORT=5000
      # Add more environment variables
    ports:
      - "5000:5000"
      - "9090:9090"
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

## Verification

### Health Checks

```bash
# Check node health
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "node_id": "node-1"
}
```

### Status Checks

```bash
# Check node status
curl http://localhost:5000/status

# Expected response:
{
  "node_id": "node-1",
  "host": "localhost",
  "port": 5000
}
```

### Log Verification

```bash
# Check logs directory
ls logs/

# Expected files:
node-1_all.log
node-1_error.log

# Tail logs
tail -f logs/node-1_all.log
```

## Testing Deployment

### Test Lock Manager

```python
import requests

# Acquire lock
response = requests.post('http://localhost:5000/lock/acquire', json={
    'resource_id': 'test-resource',
    'lock_type': 'exclusive',
    'client_id': 'test-client'
})

print(response.json())
```

### Test Queue

```python
# Produce message
response = requests.post('http://localhost:5000/queue/produce', json={
    'data': {'message': 'Hello World'},
    'partition_key': 'test-key'
})

# Consume message
response = requests.get('http://localhost:5000/queue/consume?partition=0&consumer_id=test-consumer')
```

### Test Cache

```python
# Write to cache
response = requests.post('http://localhost:5000/cache/write', json={
    'key': 'test-key',
    'value': 'test-value'
})

# Read from cache
response = requests.get('http://localhost:5000/cache/read?key=test-key')
```

## Monitoring

### Prometheus Metrics

Access Prometheus UI:
```
http://localhost:9093
```

Query examples:
```promql
# Request rate
rate(requests_total[5m])

# Cache hit rate
cache_hits_total / (cache_hits_total + cache_misses_total)

# Queue size
queue_size
```

### Log Monitoring

```bash
# Real-time logs
docker-compose logs -f

# Filter by service
docker-compose logs -f node-1

# Grep for errors
docker-compose logs | grep ERROR
```

## Troubleshooting

### Common Issues

#### Issue 1: Port Already in Use
```bash
# Find process using port
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # Linux/Mac

# Kill process or change port in .env
```

#### Issue 2: Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# Expected: PONG

# Restart Redis
# Windows
net stop redis
net start redis

# Linux
sudo systemctl restart redis
```

#### Issue 3: Node Cannot Connect to Cluster
```bash
# Check network connectivity
ping node-2

# Check firewall rules
# Windows
netsh advfirewall show allprofiles

# Verify CLUSTER_NODES configuration
```

#### Issue 4: Leader Election Fails
```bash
# Check logs for election messages
grep "election" logs/node-1_all.log

# Verify minimum 3 nodes running
docker-compose ps

# Check election timeout settings
```

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

Restart services to apply:
```bash
docker-compose restart
```

## Performance Tuning

### Optimize for High Throughput

```env
MAX_CONNECTIONS=5000
WORKER_THREADS=8
BUFFER_SIZE=16384
CACHE_SIZE_MB=512
```

### Optimize for Low Latency

```env
HEARTBEAT_INTERVAL=0.5
ELECTION_TIMEOUT_MIN=3.0
CACHE_SIZE_MB=1024
```

### Optimize for Reliability

```env
QUEUE_REPLICATION_FACTOR=3
MESSAGE_PERSISTENCE=true
LOG_COMPACTION_THRESHOLD=500
```

## Backup & Recovery

### Backup Redis Data

```bash
# Create backup
docker exec distributed-redis redis-cli SAVE

# Copy backup file
docker cp distributed-redis:/data/dump.rdb ./backup/
```

### Restore from Backup

```bash
# Stop Redis
docker-compose stop redis

# Replace data
docker cp ./backup/dump.rdb distributed-redis:/data/

# Start Redis
docker-compose start redis
```

## Scaling

### Add New Node

1. Update `docker-compose.yml`:
```yaml
node-4:
  ...
  environment:
    - NODE_ID=node-4
    - NODE_PORT=5003
    - CLUSTER_NODES=node-1:node-1:5000,...,node-4:node-4:5003
```

2. Update all nodes' CLUSTER_NODES

3. Restart cluster:
```bash
docker-compose up -d
```

### Remove Node

1. Stop node:
```bash
docker-compose stop node-3
```

2. Update CLUSTER_NODES in remaining nodes

3. Restart:
```bash
docker-compose restart
```

## Security Hardening

### Enable TLS

1. Generate certificates:
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```

2. Update configuration:
```env
ENABLE_ENCRYPTION=true
TLS_CERT_PATH=/app/certs/cert.pem
TLS_KEY_PATH=/app/certs/key.pem
```

3. Mount certificates in docker-compose:
```yaml
volumes:
  - ./certs:/app/certs:ro
```

### Network Isolation

```yaml
networks:
  distributed-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

## Maintenance

### Update System

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose build

# Rolling update
docker-compose up -d --no-deps --build node-1
docker-compose up -d --no-deps --build node-2
docker-compose up -d --no-deps --build node-3
```

### Clean Up

```bash
# Remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker rmi $(docker images -q distributed-*)

# Clean logs
rm -rf logs/*
```

## Production Deployment Checklist

- [ ] Configure production environment variables
- [ ] Enable TLS/SSL encryption
- [ ] Setup monitoring dan alerting
- [ ] Configure log rotation
- [ ] Setup automated backups
- [ ] Test disaster recovery
- [ ] Configure firewall rules
- [ ] Setup load balancer
- [ ] Enable authentication
- [ ] Document runbooks
- [ ] Setup CI/CD pipeline
- [ ] Perform load testing
- [ ] Configure auto-scaling
- [ ] Setup health checks
- [ ] Document escalation procedures

## Support

Untuk bantuan lebih lanjut:
- Check logs: `docker-compose logs`
- Review architecture: `docs/architecture.md`
- Check issues: GitHub Issues
- Contact: [Your Email]
