#!/usr/bin/env python3
"""
SIGMAX Health Check Script

Performs comprehensive health checks on all SIGMAX components.
Can be run manually or scheduled via cron for continuous monitoring.

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --detailed
    python scripts/health_check.py --json
    python scripts/health_check.py --alert-on-failure
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from enum import Enum

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Individual health check"""

    def __init__(self, name: str, status: HealthStatus, message: str = "", details: Dict = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class HealthCheckRunner:
    """Runs comprehensive health checks"""

    def __init__(self, detailed: bool = False):
        self.detailed = detailed
        self.checks: List[HealthCheck] = []

    def add_check(self, check: HealthCheck):
        """Add a health check result"""
        self.checks.append(check)

    async def check_docker_services(self) -> HealthCheck:
        """Check Docker service health"""
        try:
            import subprocess

            required_services = [
                'sigmax-postgres',
                'sigmax-redis',
                'sigmax-prometheus',
                'sigmax-grafana'
            ]

            running = []
            stopped = []

            for service in required_services:
                result = subprocess.run(
                    ['docker', 'inspect', '--format', '{{.State.Running}}', service],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0 and result.stdout.strip() == "true":
                    running.append(service)
                else:
                    stopped.append(service)

            if not stopped:
                return HealthCheck(
                    "docker_services",
                    HealthStatus.HEALTHY,
                    f"All {len(running)} services running",
                    {"running": running}
                )
            elif running:
                return HealthCheck(
                    "docker_services",
                    HealthStatus.DEGRADED,
                    f"{len(stopped)} services stopped",
                    {"running": running, "stopped": stopped}
                )
            else:
                return HealthCheck(
                    "docker_services",
                    HealthStatus.UNHEALTHY,
                    "All services stopped",
                    {"stopped": stopped}
                )

        except Exception as e:
            return HealthCheck(
                "docker_services",
                HealthStatus.UNKNOWN,
                f"Check failed: {str(e)}"
            )

    async def check_database_postgres(self) -> HealthCheck:
        """Check PostgreSQL database"""
        try:
            import psycopg2

            db_url = os.getenv('POSTGRES_URL', 'postgresql://sigmax:sigmax@localhost:5432/sigmax')

            conn = psycopg2.connect(db_url, connect_timeout=5)
            cursor = conn.cursor()

            # Test query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]

            # Get connection count
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return HealthCheck(
                "database_postgres",
                HealthStatus.HEALTHY,
                "PostgreSQL connected",
                {"size": db_size, "connections": connections}
            )

        except Exception as e:
            return HealthCheck(
                "database_postgres",
                HealthStatus.UNHEALTHY,
                f"Connection failed: {str(e)}"
            )

    async def check_database_redis(self) -> HealthCheck:
        """Check Redis database"""
        try:
            import redis

            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

            client = redis.from_url(redis_url, socket_connect_timeout=5)
            pong = client.ping()

            if pong:
                info = client.info()
                memory_used = info.get('used_memory_human', 'unknown')
                connected_clients = info.get('connected_clients', 0)

                return HealthCheck(
                    "database_redis",
                    HealthStatus.HEALTHY,
                    "Redis connected",
                    {"memory": memory_used, "clients": connected_clients}
                )
            else:
                return HealthCheck(
                    "database_redis",
                    HealthStatus.UNHEALTHY,
                    "Ping failed"
                )

        except Exception as e:
            return HealthCheck(
                "database_redis",
                HealthStatus.UNHEALTHY,
                f"Connection failed: {str(e)}"
            )

    async def check_prometheus(self) -> HealthCheck:
        """Check Prometheus"""
        try:
            import requests

            response = requests.get('http://localhost:9090/api/v1/targets', timeout=5)

            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])

                up = sum(1 for t in targets if t.get('health') == 'up')
                down = len(targets) - up

                if down == 0:
                    status = HealthStatus.HEALTHY
                    message = f"All {up} targets up"
                elif up > down:
                    status = HealthStatus.DEGRADED
                    message = f"{up} up, {down} down"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"{down} targets down"

                return HealthCheck(
                    "prometheus",
                    status,
                    message,
                    {"targets_up": up, "targets_down": down}
                )
            else:
                return HealthCheck(
                    "prometheus",
                    HealthStatus.UNHEALTHY,
                    f"API returned {response.status_code}"
                )

        except Exception as e:
            return HealthCheck(
                "prometheus",
                HealthStatus.UNHEALTHY,
                f"Check failed: {str(e)}"
            )

    async def check_grafana(self) -> HealthCheck:
        """Check Grafana"""
        try:
            import requests

            response = requests.get('http://localhost:3001/api/health', timeout=5)

            if response.status_code == 200:
                data = response.json()
                database = data.get('database', 'unknown')
                version = data.get('version', 'unknown')

                return HealthCheck(
                    "grafana",
                    HealthStatus.HEALTHY,
                    "Grafana healthy",
                    {"database": database, "version": version}
                )
            else:
                return HealthCheck(
                    "grafana",
                    HealthStatus.UNHEALTHY,
                    f"API returned {response.status_code}"
                )

        except Exception as e:
            return HealthCheck(
                "grafana",
                HealthStatus.UNHEALTHY,
                f"Check failed: {str(e)}"
            )

    async def check_disk_space(self) -> HealthCheck:
        """Check disk space"""
        try:
            import shutil

            total, used, free = shutil.disk_usage("/")

            percent_used = (used / total) * 100
            free_gb = free / (1024**3)

            if percent_used < 80:
                status = HealthStatus.HEALTHY
                message = f"{free_gb:.1f}GB free"
            elif percent_used < 90:
                status = HealthStatus.DEGRADED
                message = f"Low disk space: {free_gb:.1f}GB free"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: {free_gb:.1f}GB free"

            return HealthCheck(
                "disk_space",
                status,
                message,
                {
                    "total_gb": total / (1024**3),
                    "used_gb": used / (1024**3),
                    "free_gb": free_gb,
                    "percent_used": percent_used
                }
            )

        except Exception as e:
            return HealthCheck(
                "disk_space",
                HealthStatus.UNKNOWN,
                f"Check failed: {str(e)}"
            )

    async def check_memory(self) -> HealthCheck:
        """Check memory usage"""
        try:
            import psutil

            memory = psutil.virtual_memory()

            if memory.percent < 80:
                status = HealthStatus.HEALTHY
                message = f"{memory.available / (1024**3):.1f}GB available"
            elif memory.percent < 90:
                status = HealthStatus.DEGRADED
                message = f"High memory: {memory.percent:.1f}% used"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: {memory.percent:.1f}% used"

            return HealthCheck(
                "memory",
                status,
                message,
                {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent_used": memory.percent
                }
            )

        except Exception as e:
            return HealthCheck(
                "memory",
                HealthStatus.UNKNOWN,
                f"Check failed: {str(e)}"
            )

    async def check_cpu(self) -> HealthCheck:
        """Check CPU usage"""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)

            if cpu_percent < 70:
                status = HealthStatus.HEALTHY
                message = f"{cpu_percent:.1f}% usage"
            elif cpu_percent < 90:
                status = HealthStatus.DEGRADED
                message = f"High CPU: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: {cpu_percent:.1f}%"

            return HealthCheck(
                "cpu",
                status,
                message,
                {"percent": cpu_percent}
            )

        except Exception as e:
            return HealthCheck(
                "cpu",
                HealthStatus.UNKNOWN,
                f"Check failed: {str(e)}"
            )

    async def run_all_checks(self):
        """Run all health checks"""
        checks = [
            self.check_docker_services(),
            self.check_database_postgres(),
            self.check_database_redis(),
            self.check_prometheus(),
            self.check_grafana(),
            self.check_disk_space(),
            self.check_memory(),
            self.check_cpu()
        ]

        results = await asyncio.gather(*checks)
        for result in results:
            self.add_check(result)

    def print_results(self, json_output: bool = False):
        """Print health check results"""
        if json_output:
            output = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": self.get_overall_status().value,
                "checks": [check.to_dict() for check in self.checks]
            }
            print(json.dumps(output, indent=2))
            return

        # Text output
        print("\n" + "=" * 70)
        print("SIGMAX Health Check Report")
        print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 70 + "\n")

        status_icons = {
            HealthStatus.HEALTHY: "✓",
            HealthStatus.DEGRADED: "⚠",
            HealthStatus.UNHEALTHY: "✗",
            HealthStatus.UNKNOWN: "?"
        }

        status_colors = {
            HealthStatus.HEALTHY: "\033[92m",  # Green
            HealthStatus.DEGRADED: "\033[93m",  # Yellow
            HealthStatus.UNHEALTHY: "\033[91m",  # Red
            HealthStatus.UNKNOWN: "\033[90m",  # Gray
        }
        reset = "\033[0m"

        for check in self.checks:
            icon = status_icons.get(check.status, "?")
            color = status_colors.get(check.status, "")

            print(f"{color}{icon} {check.name:20} {check.status.value:10} {check.message}{reset}")

            if self.detailed and check.details:
                for key, value in check.details.items():
                    print(f"    {key}: {value}")

        print("\n" + "=" * 70)

        overall = self.get_overall_status()
        overall_color = status_colors.get(overall, "")
        print(f"{overall_color}Overall Status: {overall.value.upper()}{reset}")
        print("=" * 70 + "\n")

    def get_overall_status(self) -> HealthStatus:
        """Get overall health status"""
        if not self.checks:
            return HealthStatus.UNKNOWN

        statuses = [check.status for check in self.checks]

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN

    def should_alert(self) -> bool:
        """Determine if an alert should be sent"""
        overall = self.get_overall_status()
        return overall in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]

    def send_alert(self):
        """Send alert (placeholder for future implementation)"""
        overall = self.get_overall_status()

        print(f"\n⚠️  ALERT: System status is {overall.value}")
        print("Unhealthy checks:")

        for check in self.checks:
            if check.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                print(f"  - {check.name}: {check.message}")

        print("\nAlert destinations (not yet configured):")
        print("  - Email: Not configured")
        print("  - Slack: Not configured")
        print("  - PagerDuty: Not configured")
        print("\nTo configure alerts, see docs/MONITORING_SETUP.md")


async def main():
    parser = argparse.ArgumentParser(
        description="SIGMAX Health Check Script"
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed health check information'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--alert-on-failure',
        action='store_true',
        help='Send alert if health checks fail'
    )

    args = parser.parse_args()

    # Run health checks
    runner = HealthCheckRunner(detailed=args.detailed)
    await runner.run_all_checks()

    # Print results
    runner.print_results(json_output=args.json)

    # Send alert if requested and needed
    if args.alert_on_failure and runner.should_alert():
        runner.send_alert()

    # Exit with appropriate code
    overall = runner.get_overall_status()
    if overall == HealthStatus.HEALTHY:
        sys.exit(0)
    elif overall == HealthStatus.DEGRADED:
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
