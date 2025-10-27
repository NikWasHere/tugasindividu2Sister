# Scripts Folder - Helper Tools

Folder ini berisi berbagai script helper untuk testing, automation, dan demonstration.

## 📄 File Overview

### 1. `automated_test.py` 🧪
**Automated Testing Runner**

Script untuk menjalankan semua testing secara otomatis dengan satu command.

**Features:**
- ✅ Unit tests dengan pytest
- ✅ Integration tests
- ✅ Performance benchmarks
- ✅ Docker health checks
- ✅ API endpoint testing
- ✅ Automatic report generation (JSON)

**Usage:**
```bash
# Run all tests
python scripts/automated_test.py --all

# Run specific tests
python scripts/automated_test.py --unit
python scripts/automated_test.py --integration
python scripts/automated_test.py --performance
python scripts/automated_test.py --docker
python scripts/automated_test.py --api

# Skip report generation
python scripts/automated_test.py --all --no-report
```

**Output:**
- Console output dengan color-coded results
- JSON report di `reports/test_report_*.json`
- Coverage report di `reports/coverage/`

---

### 2. `api_client.py` 🎮
**Interactive API Client**

Client interaktif untuk testing semua API endpoints dengan interface yang user-friendly.

**Features:**
- 🎯 Interactive CLI menu
- 🔒 Lock Manager operations (acquire, release, status)
- 📬 Queue System operations (produce, consume, acknowledge)
- 💾 Cache operations (read, write, invalidate)
- 🔄 Node switching (round-robin)
- 📊 System health & metrics

**Usage:**
```bash
# Interactive mode (recommended)
python scripts/api_client.py --interactive

# Run all demos
python scripts/api_client.py --demo

# Test specific component
python scripts/api_client.py --test-locks
python scripts/api_client.py --test-queue
python scripts/api_client.py --test-cache
python scripts/api_client.py --test-health

# Custom node URLs
python scripts/api_client.py --nodes http://node1:8001 http://node2:8002
```

**Interactive Menu:**
```
1. Lock Manager        - Demo distributed locking
2. Queue System        - Demo message queue
3. Cache System        - Demo cache coherence
4. System Health       - Check all nodes
5. Switch Node         - Change current node
6. Run All Demos       - Execute all scenarios
q. Quit               - Exit program
```

---

### 3. `simple_api_test.py` 📝
**Simple API Test Examples**

Script sederhana dengan contoh-contoh request/response untuk semua endpoints.

**Features:**
- ✅ Step-by-step demo dengan penjelasan
- ✅ Pretty-printed JSON responses
- ✅ Interactive pauses (press ENTER to continue)
- ✅ No heavy dependencies (only requests)

**Usage:**
```bash
python scripts/simple_api_test.py
```

**Perfect for:**
- Learning how APIs work
- Quick manual testing
- Video demonstrations
- Debugging specific scenarios

---

### 4. `video_presentation_script.md` 🎥
**Video Presentation Guide**

Panduan lengkap untuk recording video demonstration.

**Contents:**
- 📋 Pre-recording checklist
- 🎬 Complete script (narasi bahasa Indonesia)
- ⏱️ Timing guidelines (10-15 minutes)
- 💡 Recording tips & best practices
- 🎨 Post-production checklist
- 📊 Demo data preparation
- ✅ Upload checklist

**Sections:**
1. Pendahuluan (1-2 min)
2. Arsitektur & Overview (2-3 min)
3. Live Demonstration (5-7 min)
   - Lock Manager demo
   - Queue System demo
   - Cache Coherence demo
4. Testing & Performance (2-3 min)
5. Kesimpulan & Penutup (1-2 min)

---

### 5. `QUICKSTART_API.md` 🚀
**API Testing Quick Start**

Tutorial cepat untuk mulai testing API.

**Contents:**
- Prerequisites setup
- Usage examples untuk setiap script
- API examples dengan code snippets
- Troubleshooting tips
- Video recording tips
- Performance testing guide
- Cleanup commands

---

### 6. `run_all.ps1` 🔧
**PowerShell Helper Script** (Windows)

One-stop script untuk semua operations.

**Commands:**
```powershell
# Setup project
.\scripts\run_all.ps1 setup

# Start Docker cluster
.\scripts\run_all.ps1 start

# Run tests
.\scripts\run_all.ps1 test

# Run demos
.\scripts\run_all.ps1 demo

# Interactive client
.\scripts\run_all.ps1 interactive

# Performance benchmarks
.\scripts\run_all.ps1 benchmark

# Prepare for video recording
.\scripts\run_all.ps1 video-prep

# Stop containers
.\scripts\run_all.ps1 stop

# Clean everything
.\scripts\run_all.ps1 clean

# Show help
.\scripts\run_all.ps1 help
```

---

## 🎯 Quick Start Guide

### First Time Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Docker containers
cd docker
docker-compose up -d
cd ..

# 3. Wait for containers (30 seconds)
Start-Sleep -Seconds 30  # PowerShell
# or
sleep 30  # Bash

# 4. Run tests to verify
python scripts/automated_test.py --all
```

### For Video Recording

```bash
# 1. Prepare environment
.\scripts\run_all.ps1 video-prep  # PowerShell

# 2. Read the script
code scripts/video_presentation_script.md

# 3. Practice with interactive client
python scripts/api_client.py --interactive

# 4. Record using simple test for demo
python scripts/simple_api_test.py
```

### Daily Development

```bash
# Start development environment
.\scripts\run_all.ps1 start

# Test changes
python scripts/automated_test.py --unit

# Manual API testing
python scripts/api_client.py --interactive

# Stop when done
.\scripts\run_all.ps1 stop
```

---

## 📊 Use Cases

### Testing Scenario

| Task | Script | Command |
|------|--------|---------|
| Full test suite | automated_test.py | `--all` |
| Quick unit test | automated_test.py | `--unit` |
| Integration test | automated_test.py | `--integration` |
| Performance test | automated_test.py | `--performance` |
| Docker health check | automated_test.py | `--docker` |

### Demo Scenario

| Task | Script | Command |
|------|--------|---------|
| Interactive demo | api_client.py | `--interactive` |
| Auto demo all | api_client.py | `--demo` |
| Lock demo only | api_client.py | `--test-locks` |
| Queue demo only | api_client.py | `--test-queue` |
| Cache demo only | api_client.py | `--test-cache` |

### Video Recording

| Step | Script | Purpose |
|------|--------|---------|
| 1. Prepare | run_all.ps1 video-prep | Check environment |
| 2. Read | video_presentation_script.md | Learn script |
| 3. Practice | api_client.py -i | Rehearse demo |
| 4. Record | simple_api_test.py | Actual recording |

---

## 🔧 Troubleshooting

### Script not found
```bash
# Make sure you're in project root
cd /path/to/tugasindividu2

# Run with full path
python scripts/automated_test.py --all
```

### Import errors
```bash
# Install dependencies
pip install -r requirements.txt

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Docker not responding
```bash
# Restart containers
cd docker
docker-compose restart
docker-compose logs -f

# Or full rebuild
docker-compose down
docker-compose up -d --build
```

### API connection refused
```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs node-1

# Wait longer (containers need time to start)
Start-Sleep -Seconds 60
```

---

## 📝 Tips & Best Practices

### For Testing
1. **Always start Docker first** before running tests
2. **Wait 30 seconds** after `docker-compose up` for cluster to stabilize
3. **Check logs** if tests fail: `docker-compose logs -f`
4. **Run tests incrementally**: unit → integration → performance

### For Demo
1. **Prepare demo data** beforehand (see video_presentation_script.md)
2. **Increase terminal font** to 16-18pt for visibility
3. **Clear screen** before each demo section
4. **Show both success and failure** scenarios (lock conflicts, etc)

### For Video
1. **Rehearse at least 2x** before final recording
2. **Keep it under 15 minutes** total
3. **Use simple_api_test.py** for step-by-step demo
4. **Record in 1920x1080** resolution minimum
5. **Add timestamps** in YouTube description

---

## 🆘 Need Help?

- **Architecture:** Read `docs/architecture.md`
- **API Spec:** Read `docs/api_spec.yaml`
- **Deployment:** Read `docs/deployment_guide.md`
- **Quick Start:** Read `scripts/QUICKSTART_API.md`
- **Video Guide:** Read `scripts/video_presentation_script.md`

---

## ✅ Checklist Before Submission

- [ ] All scripts tested and working
- [ ] Docker containers can start successfully
- [ ] All automated tests pass
- [ ] API client can connect to all nodes
- [ ] Performance benchmarks generate reports
- [ ] Video recorded and uploaded
- [ ] PDF report completed
- [ ] README updated with video link
- [ ] All documentation complete

**Good luck! 🚀**
