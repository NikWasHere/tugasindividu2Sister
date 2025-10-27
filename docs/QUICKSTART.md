# Quick Start Guide

Panduan cepat untuk menjalankan Distributed Synchronization System.

## Prerequisites

- Python 3.8+
- Docker & Docker Compose (optional)
- Redis (jika tidak menggunakan Docker)

## Quick Start dengan Docker (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd tugasindividu2

# 2. Copy environment file
cp .env.example .env

# 3. Start dengan docker-compose
cd docker
docker-compose up -d

# 4. Check status
docker-compose ps

# 5. View logs
docker-compose logs -f

# 6. Test system
curl http://localhost:5000/health
```

## Quick Start Manual

```bash
# 1. Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis (di terminal terpisah)
redis-server

# 4. Copy dan edit .env
cp .env.example .env

# 5. Start nodes (masing-masing di terminal terpisah)
# Terminal 1
python -m src.main --node-id node-1 --port 5000

# Terminal 2  
python -m src.main --node-id node-2 --port 5001

# Terminal 3
python -m src.main --node-id node-3 --port 5002
```

## Testing

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run performance benchmark
python benchmarks/performance_benchmark.py

# Run load test (memerlukan locust)
locust -f benchmarks/load_test_scenarios.py --host=http://localhost:5000
```

## Common Commands

```bash
# Stop all services
docker-compose down

# Restart a specific node
docker-compose restart node-1

# View metrics
curl http://localhost:9090/metrics

# Check Raft state
curl http://localhost:5000/status

# Scale nodes
docker-compose up -d --scale node-2=2
```

## Troubleshooting

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
# Linux/Mac
lsof -i :5000
```

### Redis connection failed
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Restart Redis
docker-compose restart redis
```

### Cannot connect to cluster
- Verify CLUSTER_NODES in .env
- Check firewall settings
- Ensure all nodes are running

## Next Steps

1. Read [Architecture Documentation](docs/architecture.md)
2. Review [API Specification](docs/api_spec.yaml)
3. Check [Deployment Guide](docs/deployment_guide.md)
4. Watch [Video Demonstration](#) (link TBD)

## Support

- Issues: GitHub Issues
- Documentation: /docs folder
- Email: [your-email]
