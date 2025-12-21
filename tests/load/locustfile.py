"""
SIGMAX Load Testing Configuration

Uses Locust to simulate high-frequency trading load and stress test the system.

Usage:
    # Run with web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Headless mode
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # Distributed load test
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --master --expect-workers 4
"""

from locust import HttpUser, task, between, events
import random
from datetime import datetime


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


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("="*70)
    print("SIGMAX Load Test Starting")
    print("="*70)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*70)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\n" + "="*70)
    print("SIGMAX Load Test Completed")
    print("="*70)
    print("Check Grafana dashboards for detailed metrics")
    print("="*70)
