#!/usr/bin/env python3
"""
Automated Testing Script
========================
Script ini menjalankan semua testing secara otomatis:
- Unit tests
- Integration tests
- Performance benchmarks
- Docker health checks
- Generate test reports

Usage:
    python scripts/automated_test.py --all
    python scripts/automated_test.py --unit
    python scripts/automated_test.py --integration
    python scripts/automated_test.py --performance
    python scripts/automated_test.py --docker
"""

import asyncio
import argparse
import subprocess
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import requests
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
logger.add("logs/automated_test_{time}.log", rotation="1 day")


class AutomatedTestRunner:
    """Automated test runner for distributed synchronization system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
        
    def run_command(self, cmd: List[str], cwd: Path = None, timeout: int = 300) -> Dict[str, Any]:
        """Run a shell command and capture output"""
        logger.info(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Timeout after {timeout}s"
            }
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def test_unit(self) -> bool:
        """Run unit tests with pytest"""
        logger.info("=" * 80)
        logger.info("RUNNING UNIT TESTS")
        logger.info("=" * 80)
        
        result = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/unit/",
            "-v",
            "--tb=short",
            "--color=yes",
            "--cov=src",
            "--cov-report=html:reports/coverage",
            "--cov-report=term",
            "--junit-xml=reports/junit_unit.xml"
        ])
        
        self.results["tests"]["unit"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            logger.success("✅ Unit tests PASSED")
        else:
            logger.error("❌ Unit tests FAILED")
            logger.error(result["stderr"])
        
        return result["success"]
    
    def test_integration(self) -> bool:
        """Run integration tests"""
        logger.info("=" * 80)
        logger.info("RUNNING INTEGRATION TESTS")
        logger.info("=" * 80)
        
        result = self.run_command([
            sys.executable, "-m", "pytest",
            "tests/integration/",
            "-v",
            "--tb=short",
            "--color=yes",
            "--junit-xml=reports/junit_integration.xml"
        ])
        
        self.results["tests"]["integration"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            logger.success("✅ Integration tests PASSED")
        else:
            logger.error("❌ Integration tests FAILED")
            logger.error(result["stderr"])
        
        return result["success"]
    
    def test_performance(self) -> bool:
        """Run performance benchmarks"""
        logger.info("=" * 80)
        logger.info("RUNNING PERFORMANCE BENCHMARKS")
        logger.info("=" * 80)
        
        result = self.run_command([
            sys.executable,
            "benchmarks/performance_benchmark.py"
        ], timeout=600)
        
        self.results["tests"]["performance"] = {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"]
        }
        
        if result["success"]:
            logger.success("✅ Performance benchmarks COMPLETED")
            logger.info("Check reports/performance/ for detailed results")
        else:
            logger.error("❌ Performance benchmarks FAILED")
            logger.error(result["stderr"])
        
        return result["success"]
    
    def test_docker_health(self) -> bool:
        """Check Docker container health"""
        logger.info("=" * 80)
        logger.info("CHECKING DOCKER HEALTH")
        logger.info("=" * 80)
        
        # Check if docker-compose is running
        result = self.run_command([
            "docker-compose", "ps"
        ], cwd=self.project_root / "docker")
        
        if not result["success"]:
            logger.warning("⚠️  Docker containers not running. Starting them...")
            start_result = self.run_command([
                "docker-compose", "up", "-d"
            ], cwd=self.project_root / "docker", timeout=120)
            
            if not start_result["success"]:
                logger.error("❌ Failed to start Docker containers")
                return False
            
            logger.info("Waiting 30s for containers to be ready...")
            time.sleep(30)
        
        # Check container health
        containers = ["node-1", "node-2", "node-3", "redis", "prometheus"]
        all_healthy = True
        
        for container in containers:
            logger.info(f"Checking {container}...")
            result = self.run_command([
                "docker", "inspect",
                "--format", "{{.State.Health.Status}}",
                f"distributed-sync-{container}-1"
            ])
            
            # Some containers may not have health checks
            if result["returncode"] == 0:
                status = result["stdout"].strip()
                if status == "healthy" or status == "":
                    logger.success(f"  ✅ {container} is healthy")
                else:
                    logger.error(f"  ❌ {container} status: {status}")
                    all_healthy = False
            else:
                # Check if container is running
                result = self.run_command([
                    "docker", "inspect",
                    "--format", "{{.State.Running}}",
                    f"distributed-sync-{container}-1"
                ])
                if result["stdout"].strip() == "true":
                    logger.success(f"  ✅ {container} is running")
                else:
                    logger.error(f"  ❌ {container} is not running")
                    all_healthy = False
        
        self.results["tests"]["docker"] = {
            "success": all_healthy,
            "containers": containers
        }
        
        if all_healthy:
            logger.success("✅ All Docker containers are healthy")
        else:
            logger.error("❌ Some Docker containers are not healthy")
        
        return all_healthy
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints availability"""
        logger.info("=" * 80)
        logger.info("TESTING API ENDPOINTS")
        logger.info("=" * 80)
        
        base_urls = [
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:8003"
        ]
        
        endpoints = [
            "/health",
            "/metrics",
            "/raft/status"
        ]
        
        all_passed = True
        
        for base_url in base_urls:
            logger.info(f"Testing {base_url}...")
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        logger.success(f"  ✅ {endpoint}: {response.status_code}")
                    else:
                        logger.warning(f"  ⚠️  {endpoint}: {response.status_code}")
                        all_passed = False
                except Exception as e:
                    logger.error(f"  ❌ {endpoint}: {str(e)}")
                    all_passed = False
        
        self.results["tests"]["api"] = {
            "success": all_passed
        }
        
        return all_passed
    
    def generate_report(self):
        """Generate test report"""
        logger.info("=" * 80)
        logger.info("GENERATING TEST REPORT")
        logger.info("=" * 80)
        
        # Calculate summary
        for test_name, test_result in self.results["tests"].items():
            self.results["summary"]["total"] += 1
            if test_result["success"]:
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
        
        # Save JSON report
        report_file = self.project_root / "reports" / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Tests: {self.results['summary']['total']}")
        logger.info(f"Passed: {self.results['summary']['passed']} ✅")
        logger.info(f"Failed: {self.results['summary']['failed']} ❌")
        logger.info(f"Success Rate: {self.results['summary']['passed'] / max(self.results['summary']['total'], 1) * 100:.1f}%")
        logger.info("=" * 80)
        
        return self.results["summary"]["failed"] == 0


def main():
    parser = argparse.ArgumentParser(description="Automated Testing Script")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance benchmarks only")
    parser.add_argument("--docker", action="store_true", help="Check Docker health only")
    parser.add_argument("--api", action="store_true", help="Test API endpoints only")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation")
    
    args = parser.parse_args()
    
    # If no specific test is selected, run all
    if not any([args.unit, args.integration, args.performance, args.docker, args.api]):
        args.all = True
    
    runner = AutomatedTestRunner()
    
    logger.info("🚀 Starting Automated Testing")
    logger.info(f"📁 Project Root: {runner.project_root}")
    
    # Create reports directory
    (runner.project_root / "reports").mkdir(exist_ok=True)
    
    success = True
    
    try:
        if args.all or args.docker:
            if not runner.test_docker_health():
                success = False
        
        if args.all or args.api:
            if not runner.test_api_endpoints():
                success = False
        
        if args.all or args.unit:
            if not runner.test_unit():
                success = False
        
        if args.all or args.integration:
            if not runner.test_integration():
                success = False
        
        if args.all or args.performance:
            if not runner.test_performance():
                success = False
        
        if not args.no_report:
            report_success = runner.generate_report()
            if not report_success:
                success = False
        
        if success:
            logger.success("\n✅ ALL TESTS PASSED!")
            return 0
        else:
            logger.error("\n❌ SOME TESTS FAILED!")
            return 1
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Testing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Testing failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
