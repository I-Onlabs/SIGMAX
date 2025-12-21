"""
SIGMAX Load Testing Configuration

Uses Locust to simulate high-frequency trading load and stress test the system.
Tests API rate limits, concurrent users, and SIGMAX-specific endpoints.

Rate Limits (from SDK docs):
- General API: 60 requests/min
- Analysis endpoints: 10 requests/min
- Trading endpoints: 5 requests/min

Usage:
    # Run with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Headless mode
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # Test rate limits specifically
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 20 --spawn-rate 5 --run-time 2m --headless \
           --tags rate-limit

    # Distributed load test
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --master --expect-workers 4

Performance Metrics to Validate:
- Agent decision latency: <30ms (claimed in README)
- SSE streaming latency: <50ms (claimed in docs)
- API throughput: 60 req/min sustained
- Concurrent users: Handle 100+ simultaneous connections
"""

from locust import HttpUser, task, between, events, tag
import random
import time
from datetime import datetime
from collections import defaultdict


# Global metrics collection
rate_limit_violations = defaultdict(int)
latency_stats = defaultdict(list)


class SIGMAXProposalUser(HttpUser):
    """
    Simulates SIGMAX chat API users creating and managing trade proposals.
    Tests the complete workflow: create → approve → execute
    """

    wait_time = between(2, 5)  # Proposals take time to analyze

    def on_start(self):
        """Initialize with API key"""
        self.client.headers.update({
            "X-API-Key": "test-api-key-123",
            "Content-Type": "application/json"
        })
        self.proposal_ids = []

    @task(5)
    @tag('analysis')
    def create_proposal(self):
        """Create a new trade proposal (10 req/min limit)"""
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]
        risk_profiles = ["conservative", "moderate", "aggressive"]

        proposal_data = {
            "symbol": random.choice(symbols),
            "risk_profile": random.choice(risk_profiles),
            "mode": "paper"
        }

        start_time = time.time()

        with self.client.post(
            "/api/v1/chat/proposals",
            json=proposal_data,
            catch_response=True,
            name="/api/v1/chat/proposals [CREATE]"
        ) as response:
            latency = (time.time() - start_time) * 1000
            latency_stats['proposal_create'].append(latency)

            if response.status_code == 200:
                data = response.json()
                if "proposal" in data and data["proposal"] and "id" in data["proposal"]:
                    self.proposal_ids.append(data["proposal"]["id"])
                response.success()
            elif response.status_code == 429:
                rate_limit_violations['proposals'] += 1
                response.failure(f"Rate limit hit: {response.status_code}")
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def list_proposals(self):
        """List all proposals (60 req/min limit)"""
        with self.client.get(
            "/api/v1/chat/proposals",
            catch_response=True,
            name="/api/v1/chat/proposals [LIST]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                rate_limit_violations['general'] += 1
                response.failure("Rate limit hit")
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def approve_proposal(self):
        """Approve a proposal (5 req/min trading limit)"""
        if not self.proposal_ids:
            return

        proposal_id = random.choice(self.proposal_ids)

        with self.client.post(
            f"/api/v1/chat/proposals/{proposal_id}/approve",
            catch_response=True,
            name="/api/v1/chat/proposals/:id/approve"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                rate_limit_violations['trading'] += 1
                response.failure("Trading rate limit hit")
            elif response.status_code == 404:
                response.success()  # Expected if proposal was deleted
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    @tag('trading')
    def execute_proposal(self):
        """Execute a proposal (5 req/min trading limit)"""
        if not self.proposal_ids:
            return

        proposal_id = random.choice(self.proposal_ids)

        start_time = time.time()

        with self.client.post(
            f"/api/v1/chat/proposals/{proposal_id}/execute",
            catch_response=True,
            name="/api/v1/chat/proposals/:id/execute"
        ) as response:
            latency = (time.time() - start_time) * 1000
            latency_stats['proposal_execute'].append(latency)

            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                rate_limit_violations['trading'] += 1
                response.failure("Trading rate limit hit")
            elif response.status_code == 404:
                response.success()  # Expected if proposal was deleted
            else:
                response.failure(f"Got status {response.status_code}")


class TradingAPIUser(HttpUser):
    """Simulates a trading client making API calls"""

    # Wait between 0.1-1 seconds between tasks (simulating HFT)
    wait_time = between(0.1, 1)

    def on_start(self):
        """Called when a user starts"""
        self.client.verify = False  # Disable SSL verification for testing

        # Simulate authentication
        response = self.client.post("/api/auth/login", json={
            "username": f"test_user_{random.randint(1, 1000)}",
            "password": "test_password"
        }, catch_response=True)

        if response.status_code == 200:
            self.token = response.json().get("token", "test_token")
        else:
            self.token = "test_token"

        # Set authorization header
        self.client.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })

    @task(5)
    def get_market_data(self):
        """Fetch market data (most common operation)"""
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]
        symbol = random.choice(symbols)

        with self.client.get(
            f"/api/market/ticker/{symbol}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(3)
    def get_orderbook(self):
        """Fetch orderbook (high frequency)"""
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        symbol = random.choice(symbols)

        with self.client.get(
            f"/api/market/orderbook/{symbol}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def place_order(self):
        """Place a trading order"""
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        sides = ["buy", "sell"]
        types = ["limit", "market"]

        order_data = {
            "symbol": random.choice(symbols),
            "side": random.choice(sides),
            "type": random.choice(types),
            "amount": round(random.uniform(0.01, 1.0), 4),
            "price": round(random.uniform(1000, 5000), 2) if types[0] == "limit" else None
        }

        with self.client.post(
            "/api/orders",
            json=order_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def get_portfolio(self):
        """Get portfolio/balance"""
        with self.client.get(
            "/api/portfolio",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def get_open_orders(self):
        """Get open orders"""
        with self.client.get(
            "/api/orders/open",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def cancel_order(self):
        """Cancel an order"""
        order_id = random.randint(1, 10000)

        with self.client.delete(
            f"/api/orders/{order_id}",
            catch_response=True
        ) as response:
            if response.status_code in [200, 204, 404]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def get_trading_signals(self):
        """Get trading signals"""
        with self.client.get(
            "/api/signals",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class MarketMakerUser(HttpUser):
    """Simulates a market maker with very high frequency requests"""

    wait_time = between(0.05, 0.2)  # Very fast requests

    def on_start(self):
        """Initialize market maker"""
        self.symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        self.client.headers.update({
            "Authorization": "Bearer mm_token",
            "Content-Type": "application/json"
        })

    @task(10)
    def stream_orderbook(self):
        """Continuously stream orderbook updates"""
        symbol = random.choice(self.symbols)

        with self.client.get(
            f"/api/market/orderbook/{symbol}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(5)
    def update_quotes(self):
        """Update market maker quotes"""
        symbol = random.choice(self.symbols)

        quote_data = {
            "symbol": symbol,
            "bids": [
                {"price": 100.0, "amount": 1.0},
                {"price": 99.5, "amount": 2.0}
            ],
            "asks": [
                {"price": 100.5, "amount": 1.0},
                {"price": 101.0, "amount": 2.0}
            ]
        }

        with self.client.post(
            "/api/mm/quotes",
            json=quote_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class StrategyBotUser(HttpUser):
    """Simulates an algorithmic trading strategy"""

    wait_time = between(1, 5)  # Strategy decisions every 1-5 seconds

    def on_start(self):
        """Initialize strategy bot"""
        self.strategy_id = f"strategy_{random.randint(1, 100)}"
        self.client.headers.update({
            "Authorization": "Bearer strategy_token",
            "Content-Type": "application/json"
        })

    @task(3)
    def get_signals(self):
        """Fetch trading signals"""
        with self.client.get(
            "/api/signals",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def execute_strategy(self):
        """Execute strategy decision"""
        strategy_data = {
            "strategy_id": self.strategy_id,
            "action": random.choice(["buy", "sell", "hold"]),
            "confidence": round(random.uniform(0.5, 1.0), 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        with self.client.post(
            "/api/strategy/execute",
            json=strategy_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task(1)
    def get_performance(self):
        """Get strategy performance metrics"""
        with self.client.get(
            f"/api/strategy/{self.strategy_id}/performance",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


# Event handlers for custom metrics and reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("="*70)
    print("SIGMAX Load Test Starting")
    print("="*70)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("\nRate Limits to Test:")
    print("  - General API: 60 req/min")
    print("  - Analysis endpoints: 10 req/min")
    print("  - Trading endpoints: 5 req/min")
    print("\nPerformance Targets:")
    print("  - Agent decision: <30ms")
    print("  - Proposal creation: <5000ms")
    print("  - Proposal execution: <10000ms")
    print("="*70)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - report detailed metrics"""
    print("\n" + "="*70)
    print("SIGMAX Load Test Results")
    print("="*70)

    # Rate limit violations
    if rate_limit_violations:
        print("\n📊 Rate Limit Violations:")
        for endpoint, count in rate_limit_violations.items():
            print(f"  - {endpoint}: {count} violations")
    else:
        print("\n✅ No rate limit violations detected")

    # Latency statistics
    if latency_stats:
        print("\n⏱️  Latency Statistics:")
        for operation, latencies in latency_stats.items():
            if latencies:
                mean = sum(latencies) / len(latencies)
                sorted_lat = sorted(latencies)
                p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
                p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
                p99 = sorted_lat[int(len(sorted_lat) * 0.99)]

                print(f"\n  {operation}:")
                print(f"    Mean: {mean:.2f}ms")
                print(f"    P50:  {p50:.2f}ms")
                print(f"    P95:  {p95:.2f}ms")
                print(f"    P99:  {p99:.2f}ms")
                print(f"    Min:  {min(latencies):.2f}ms")
                print(f"    Max:  {max(latencies):.2f}ms")
                print(f"    Samples: {len(latencies)}")

                # Check against targets
                if operation == 'proposal_create' and mean > 5000:
                    print(f"    ⚠️  Exceeds 5s target")
                elif operation == 'proposal_execute' and mean > 10000:
                    print(f"    ⚠️  Exceeds 10s target")

    # Summary statistics from Locust
    print("\n📈 Overall Statistics:")
    stats = environment.stats
    total_rps = stats.total.current_rps if hasattr(stats.total, 'current_rps') else 0
    total_failures = stats.total.num_failures if hasattr(stats.total, 'num_failures') else 0
    total_requests = stats.total.num_requests if hasattr(stats.total, 'num_requests') else 0

    print(f"  Total requests: {total_requests}")
    print(f"  Total failures: {total_failures}")
    print(f"  Requests/sec: {total_rps:.2f}")

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100
        print(f"  Failure rate: {failure_rate:.2f}%")

    print("\n" + "="*70)
    print("💡 Recommendations:")
    print("  - Check Grafana dashboards for real-time metrics")
    print("  - Review rate limit violations if any")
    print("  - Compare latencies against README claims")
    print("  - Analyze P99 latencies for worst-case performance")
    print("="*70)
