#!/usr/bin/env python
"""
Starter script untuk Distributed Synchronization System
Memudahkan untuk start/stop/restart nodes
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_command(cmd, shell=True):
    """Execute shell command"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell)
    return result.returncode


def start_docker():
    """Start dengan Docker Compose"""
    print("🚀 Starting with Docker Compose...")
    os.chdir("docker")
    return run_command("docker-compose up -d")


def stop_docker():
    """Stop Docker Compose"""
    print("🛑 Stopping Docker Compose...")
    os.chdir("docker")
    return run_command("docker-compose down")


def logs_docker(service=None):
    """View Docker logs"""
    os.chdir("docker")
    if service:
        return run_command(f"docker-compose logs -f {service}")
    return run_command("docker-compose logs -f")


def test_system():
    """Run tests"""
    print("🧪 Running tests...")
    return run_command("pytest tests/ -v")


def benchmark():
    """Run performance benchmark"""
    print("📊 Running performance benchmark...")
    return run_command("python benchmarks/performance_benchmark.py")


def load_test():
    """Run load test"""
    print("⚡ Running load test...")
    return run_command("locust -f benchmarks/load_test_scenarios.py --host=http://localhost:5000")


def install_deps():
    """Install dependencies"""
    print("📦 Installing dependencies...")
    return run_command("pip install -r requirements.txt")


def setup_env():
    """Setup environment"""
    print("⚙️ Setting up environment...")
    if not Path(".env").exists():
        run_command("cp .env.example .env")
        print("✅ .env file created. Please edit it before starting.")
    else:
        print("ℹ️ .env file already exists")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Distributed Synchronization System Manager"
    )
    
    parser.add_argument(
        "action",
        choices=[
            "start", "stop", "restart", "logs",
            "test", "benchmark", "load-test",
            "install", "setup"
        ],
        help="Action to perform"
    )
    
    parser.add_argument(
        "--service",
        help="Specific service for logs (e.g., node-1)"
    )
    
    args = parser.parse_args()
    
    if args.action == "start":
        setup_env()
        return start_docker()
    
    elif args.action == "stop":
        return stop_docker()
    
    elif args.action == "restart":
        stop_docker()
        return start_docker()
    
    elif args.action == "logs":
        return logs_docker(args.service)
    
    elif args.action == "test":
        return test_system()
    
    elif args.action == "benchmark":
        return benchmark()
    
    elif args.action == "load-test":
        return load_test()
    
    elif args.action == "install":
        return install_deps()
    
    elif args.action == "setup":
        setup_env()
        return install_deps()


if __name__ == "__main__":
    sys.exit(main())
