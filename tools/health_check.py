#!/usr/bin/env python3
"""
System Health Check

Verifies all SIGMAX services and infrastructure are running correctly.
"""

import sys
import argparse
import asyncio
import socket
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "✓"
    DEGRADED = "⚠"
    UNHEALTHY = "✗"
    UNKNOWN = "?"


@dataclass
class ServiceHealth:
    """Health status for a service"""
    name: str
    status: HealthStatus
    message: str
    latency_ms: float = 0.0


class HealthChecker:
    """
    Check health of all SIGMAX components.

    Checks:
    - Infrastructure services (Postgres, ClickHouse, Redis, Prometheus)
    - Trading services (ingest, book, features, decision, risk, router, exec)
    - Network connectivity
    - Disk space
    - Memory usage
    """

    def __init__(self):
        self.results: List[ServiceHealth] = []

    async def check_all(self) -> List[ServiceHealth]:
        """Run all health checks"""
        print("\n🏥 SIGMAX Health Check")
        print("=" * 80)

        # Infrastructure checks
        await self._check_postgres()
        await self._check_clickhouse()
        await self._check_redis()
        await self._check_prometheus()

        # Trading service checks
        await self._check_zmq_port('ingest', 5555)
        await self._check_zmq_port('book', 5556)
        await self._check_zmq_port('features', 5557)
        await self._check_zmq_port('decision', 5558)
        await self._check_zmq_port('risk', 5559)
        await self._check_zmq_port('router', 5560)
        await self._check_zmq_port('exec', 5561)

        # System checks
        await self._check_disk_space()
        await self._check_memory()

        return self.results

    async def _check_postgres(self):
        """Check Postgres database"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="sigmax",
                user="sigmax",
                password="sigmax_dev_password",
                connect_timeout=3
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()

            self.results.append(ServiceHealth(
                name="Postgres",
                status=HealthStatus.HEALTHY,
                message="Connected successfully"
            ))
        except ImportError:
            self.results.append(ServiceHealth(
                name="Postgres",
                status=HealthStatus.UNKNOWN,
                message="psycopg2 not installed"
            ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name="Postgres",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)[:50]}"
            ))

    async def _check_clickhouse(self):
        """Check ClickHouse database"""
        try:
            import clickhouse_connect
            client = clickhouse_connect.get_client(
                host='localhost',
                port=8123,
                username='default',
                password='',
                connect_timeout=3
            )
            result = client.command('SELECT 1')

            self.results.append(ServiceHealth(
                name="ClickHouse",
                status=HealthStatus.HEALTHY,
                message="Connected successfully"
            ))
        except ImportError:
            self.results.append(ServiceHealth(
                name="ClickHouse",
                status=HealthStatus.UNKNOWN,
                message="clickhouse-connect not installed"
            ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name="ClickHouse",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)[:50]}"
            ))

    async def _check_redis(self):
        """Check Redis cache"""
        try:
            import redis
            client = redis.Redis(
                host='localhost',
                port=6379,
                socket_connect_timeout=3
            )
            client.ping()

            self.results.append(ServiceHealth(
                name="Redis",
                status=HealthStatus.HEALTHY,
                message="Connected successfully"
            ))
        except ImportError:
            self.results.append(ServiceHealth(
                name="Redis",
                status=HealthStatus.UNKNOWN,
                message="redis not installed"
            ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name="Redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)[:50]}"
            ))

    async def _check_prometheus(self):
        """Check Prometheus monitoring"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:9090/-/healthy', timeout=3) as response:
                    if response.status == 200:
                        self.results.append(ServiceHealth(
                            name="Prometheus",
                            status=HealthStatus.HEALTHY,
                            message="Service healthy"
                        ))
                    else:
                        self.results.append(ServiceHealth(
                            name="Prometheus",
                            status=HealthStatus.DEGRADED,
                            message=f"HTTP {response.status}"
                        ))
        except ImportError:
            self.results.append(ServiceHealth(
                name="Prometheus",
                status=HealthStatus.UNKNOWN,
                message="aiohttp not installed"
            ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name="Prometheus",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection failed: {str(e)[:50]}"
            ))

    async def _check_zmq_port(self, service_name: str, port: int):
        """Check if ZeroMQ port is listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()

            if result == 0:
                self.results.append(ServiceHealth(
                    name=f"Service: {service_name}",
                    status=HealthStatus.HEALTHY,
                    message=f"Port {port} listening"
                ))
            else:
                self.results.append(ServiceHealth(
                    name=f"Service: {service_name}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Port {port} not listening"
                ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name=f"Service: {service_name}",
                status=HealthStatus.UNKNOWN,
                message=f"Check failed: {str(e)[:50]}"
            ))

    async def _check_disk_space(self):
        """Check disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_pct = (free / total) * 100

            if free_pct > 20:
                status = HealthStatus.HEALTHY
                message = f"{free_pct:.1f}% free ({free // (2**30)}GB)"
            elif free_pct > 10:
                status = HealthStatus.DEGRADED
                message = f"Low disk: {free_pct:.1f}% free ({free // (2**30)}GB)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: {free_pct:.1f}% free ({free // (2**30)}GB)"

            self.results.append(ServiceHealth(
                name="Disk Space",
                status=status,
                message=message
            ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name="Disk Space",
                status=HealthStatus.UNKNOWN,
                message=f"Check failed: {str(e)[:50]}"
            ))

    async def _check_memory(self):
        """Check memory usage"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            available_pct = mem.available / mem.total * 100

            if available_pct > 20:
                status = HealthStatus.HEALTHY
                message = f"{available_pct:.1f}% available ({mem.available // (2**30)}GB)"
            elif available_pct > 10:
                status = HealthStatus.DEGRADED
                message = f"Low memory: {available_pct:.1f}% available"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: {available_pct:.1f}% available"

            self.results.append(ServiceHealth(
                name="Memory",
                status=status,
                message=message
            ))
        except ImportError:
            self.results.append(ServiceHealth(
                name="Memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not installed"
            ))
        except Exception as e:
            self.results.append(ServiceHealth(
                name="Memory",
                status=HealthStatus.UNKNOWN,
                message=f"Check failed: {str(e)[:50]}"
            ))

    def print_results(self):
        """Print health check results"""
        print("\n📋 RESULTS")
        print("-" * 80)
        print(f"{'Component':<30} {'Status':<10} {'Details':<40}")
        print("-" * 80)

        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0

        for result in self.results:
            status_symbol = result.status.value
            print(f"{result.name:<30} {status_symbol:<10} {result.message:<40}")

            if result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif result.status == HealthStatus.DEGRADED:
                degraded_count += 1
            elif result.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1

        print("-" * 80)
        print(f"\nSummary: {healthy_count} healthy, {degraded_count} degraded, {unhealthy_count} unhealthy")

        # Overall status
        if unhealthy_count > 0:
            print("\n🔴 SYSTEM STATUS: UNHEALTHY")
            print("Action required: Fix unhealthy components before trading")
            return 1
        elif degraded_count > 0:
            print("\n🟡 SYSTEM STATUS: DEGRADED")
            print("Warning: Some components need attention")
            return 1
        else:
            print("\n🟢 SYSTEM STATUS: HEALTHY")
            print("All systems operational")
            return 0

        print("=" * 80 + "\n")


async def run_health_check(args):
    """Run health check"""
    checker = HealthChecker()
    await checker.check_all()
    exit_code = checker.print_results()

    if args.watch:
        print(f"\nWatching... (press Ctrl+C to stop)")
        print(f"Refresh interval: {args.interval}s\n")
        try:
            while True:
                await asyncio.sleep(args.interval)
                print("\n" * 2)
                checker.results = []
                await checker.check_all()
                checker.print_results()
        except KeyboardInterrupt:
            print("\n\nStopped watching.")

    return exit_code


def main():
    parser = argparse.ArgumentParser(description='SIGMAX Health Check')
    parser.add_argument('--watch', action='store_true',
                       help='Continuously monitor health')
    parser.add_argument('--interval', type=int, default=10,
                       help='Watch interval in seconds (default: 10)')

    args = parser.parse_args()

    exit_code = asyncio.run(run_health_check(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
