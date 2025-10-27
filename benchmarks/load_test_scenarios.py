"""
Locust load testing scenarios for performance benchmarking
"""

from locust import HttpUser, task, between, events
import json
import random
import time


class DistributedSystemUser(HttpUser):
    """Simulate user interacting with distributed system"""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Initialize user session"""
        self.client_id = f"client-{random.randint(1, 1000)}"
        self.resource_ids = [f"resource-{i}" for i in range(100)]
    
    @task(3)
    def acquire_lock(self):
        """Test lock acquisition"""
        resource_id = random.choice(self.resource_ids)
        lock_type = random.choice(["shared", "exclusive"])
        
        payload = {
            "operation": "acquire_lock",
            "resource_id": resource_id,
            "lock_type": lock_type,
            "client_id": self.client_id
        }
        
        with self.client.post(
            "/lock/acquire",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(2)
    def release_lock(self):
        """Test lock release"""
        resource_id = random.choice(self.resource_ids)
        
        payload = {
            "operation": "release_lock",
            "resource_id": resource_id,
            "client_id": self.client_id
        }
        
        with self.client.post(
            "/lock/release",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(5)
    def produce_message(self):
        """Test message production"""
        payload = {
            "data": {
                "message": f"Test message from {self.client_id}",
                "timestamp": time.time()
            },
            "partition_key": f"key-{random.randint(1, 10)}"
        }
        
        with self.client.post(
            "/queue/produce",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(4)
    def consume_message(self):
        """Test message consumption"""
        partition = random.randint(0, 15)
        
        with self.client.get(
            f"/queue/consume?partition={partition}&consumer_id={self.client_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(6)
    def cache_read(self):
        """Test cache read"""
        key = f"cache-key-{random.randint(1, 50)}"
        
        with self.client.get(
            f"/cache/read?key={key}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")
    
    @task(3)
    def cache_write(self):
        """Test cache write"""
        key = f"cache-key-{random.randint(1, 50)}"
        
        payload = {
            "key": key,
            "value": {
                "data": f"Value from {self.client_id}",
                "timestamp": time.time()
            }
        }
        
        with self.client.post(
            "/cache/write",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line options"""
    parser.add_argument("--node-count", type=int, default=3,
                       help="Number of nodes in cluster")


# Performance metrics collection
request_times = []
failure_count = 0
success_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Collect request metrics"""
    global request_times, failure_count, success_count
    
    request_times.append(response_time)
    
    if exception:
        failure_count += 1
    else:
        success_count += 1


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print statistics at test end"""
    if request_times:
        print("\n" + "="*50)
        print("PERFORMANCE STATISTICS")
        print("="*50)
        print(f"Total Requests: {len(request_times)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failure_count}")
        print(f"Average Response Time: {sum(request_times)/len(request_times):.2f}ms")
        print(f"Min Response Time: {min(request_times):.2f}ms")
        print(f"Max Response Time: {max(request_times):.2f}ms")
        
        # Calculate percentiles
        sorted_times = sorted(request_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print(f"P50: {p50:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"P99: {p99:.2f}ms")
        print("="*50)
