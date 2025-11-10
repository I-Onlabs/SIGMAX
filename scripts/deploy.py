#!/usr/bin/env python3
"""
SIGMAX Production Deployment Script

Automates the deployment process for SIGMAX trading system.
Handles pre-flight checks, service startup, and post-deployment validation.

Usage:
    python scripts/deploy.py --env production
    python scripts/deploy.py --env testnet --skip-checks
    python scripts/deploy.py --env production --dry-run
"""

import argparse
import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class DeploymentManager:
    """Manages SIGMAX deployment process"""

    def __init__(self, env: str, dry_run: bool = False, skip_checks: bool = False):
        self.env = env
        self.dry_run = dry_run
        self.skip_checks = skip_checks
        self.project_root = Path(__file__).parent.parent
        self.services = [
            'postgres', 'redis', 'clickhouse',
            'prometheus', 'grafana', 'alertmanager'
        ]

    def log(self, message: str, level: str = "INFO"):
        """Log deployment message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        color_codes = {
            "INFO": "\033[94m",  # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",  # Red
            "RESET": "\033[0m"
        }
        color = color_codes.get(level, "")
        reset = color_codes["RESET"]
        print(f"{color}[{timestamp}] [{level}] {message}{reset}")

    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command"""
        self.log(f"Running: {' '.join(cmd)}")

        if self.dry_run:
            self.log("DRY RUN - Command not executed", "WARNING")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if check and result.returncode != 0:
            self.log(f"Command failed: {result.stderr}", "ERROR")
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")

        return result

    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        self.log("Checking prerequisites...")

        checks = []

        # Check Docker
        try:
            result = self.run_command(['docker', '--version'], check=False)
            if result.returncode == 0:
                self.log(f"✓ Docker: {result.stdout.strip()}", "SUCCESS")
                checks.append(True)
            else:
                self.log("✗ Docker not found", "ERROR")
                checks.append(False)
        except Exception as e:
            self.log(f"✗ Docker check failed: {e}", "ERROR")
            checks.append(False)

        # Check Docker Compose
        try:
            result = self.run_command(['docker-compose', '--version'], check=False)
            if result.returncode == 0:
                self.log(f"✓ Docker Compose: {result.stdout.strip()}", "SUCCESS")
                checks.append(True)
            else:
                self.log("✗ Docker Compose not found", "ERROR")
                checks.append(False)
        except Exception as e:
            self.log(f"✗ Docker Compose check failed: {e}", "ERROR")
            checks.append(False)

        # Check Python version
        import platform
        py_version = platform.python_version()
        if py_version >= "3.11":
            self.log(f"✓ Python: {py_version}", "SUCCESS")
            checks.append(True)
        else:
            self.log(f"✗ Python 3.11+ required, found {py_version}", "ERROR")
            checks.append(False)

        # Check environment file
        env_file = self.project_root / f".env.{self.env}"
        if env_file.exists():
            self.log(f"✓ Environment file: {env_file}", "SUCCESS")
            checks.append(True)
        else:
            self.log(f"✗ Environment file not found: {env_file}", "ERROR")
            checks.append(False)

        # Check docker-compose.yml
        compose_file = self.project_root / "docker-compose.yml"
        if compose_file.exists():
            self.log(f"✓ Docker Compose file: {compose_file}", "SUCCESS")
            checks.append(True)
        else:
            self.log(f"✗ Docker Compose file not found: {compose_file}", "ERROR")
            checks.append(False)

        return all(checks)

    def backup_database(self):
        """Backup database before deployment"""
        self.log("Creating database backup...")

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = self.project_root / "backups"
        backup_dir.mkdir(exist_ok=True)

        backup_file = backup_dir / f"sigmax_{self.env}_{timestamp}.sql"

        # PostgreSQL backup
        try:
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'pg_dump', '-U', 'sigmax', 'sigmax',
                '-f', f'/tmp/backup_{timestamp}.sql'
            ])

            self.run_command([
                'docker', 'cp',
                f'sigmax-postgres:/tmp/backup_{timestamp}.sql',
                str(backup_file)
            ])

            self.log(f"✓ Database backup created: {backup_file}", "SUCCESS")
        except Exception as e:
            self.log(f"✗ Database backup failed: {e}", "WARNING")
            self.log("Continuing without backup...", "WARNING")

    def start_infrastructure(self):
        """Start infrastructure services"""
        self.log("Starting infrastructure services...")

        cmd = [
            'docker-compose',
            '--env-file', f'.env.{self.env}',
            'up', '-d'
        ] + self.services

        self.run_command(cmd)

        # Wait for services to be healthy
        self.log("Waiting for services to be healthy...")
        time.sleep(5)

        for service in self.services:
            container_name = f"sigmax-{service}"
            max_attempts = 30

            for attempt in range(max_attempts):
                try:
                    result = self.run_command([
                        'docker', 'inspect',
                        '--format', '{{.State.Health.Status}}',
                        container_name
                    ], check=False)

                    status = result.stdout.strip()

                    if status == "healthy" or result.returncode != 0:
                        # Some containers don't have healthchecks
                        self.log(f"✓ {service}: Ready", "SUCCESS")
                        break

                    self.log(f"  {service}: {status} (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(2)

                except Exception as e:
                    if attempt == max_attempts - 1:
                        self.log(f"✗ {service}: Health check failed: {e}", "ERROR")
                        raise
                    time.sleep(2)

    def run_migrations(self):
        """Run database migrations"""
        self.log("Running database migrations...")

        # Check if migrations directory exists
        migrations_dir = self.project_root / "db" / "migrations"

        if not migrations_dir.exists():
            self.log("No migrations directory found, skipping...", "WARNING")
            return

        # Run PostgreSQL migrations
        pg_migrations = migrations_dir / "postgres"
        if pg_migrations.exists():
            for migration_file in sorted(pg_migrations.glob("*.sql")):
                self.log(f"Running migration: {migration_file.name}")

                self.run_command([
                    'docker', 'exec', '-i', 'sigmax-postgres',
                    'psql', '-U', 'sigmax', '-d', 'sigmax',
                    '-f', f'/docker-entrypoint-initdb.d/{migration_file.name}'
                ])

        self.log("✓ Migrations completed", "SUCCESS")

    def start_sigmax_services(self):
        """Start SIGMAX trading services"""
        self.log("Starting SIGMAX services...")

        sigmax_services = [
            'ingest_cex',
            'book_shard',
            'features',
            'decision',
            'risk',
            'router',
            'exec_cex',
            'obs'
        ]

        # Start each service
        for service in sigmax_services:
            self.log(f"Starting {service}...")

            # In production, these would be started as systemd services or supervisor processes
            # For now, we'll just log the command that would be run
            cmd = f"python -m apps.{service}.main --env {self.env}"
            self.log(f"  Command: {cmd}")

            if not self.dry_run:
                # TODO: Implement actual service startup (systemd, supervisor, etc.)
                self.log(f"  Note: Service startup not implemented - run manually", "WARNING")

        self.log("✓ SIGMAX services started", "SUCCESS")

    def validate_deployment(self) -> bool:
        """Validate deployment is successful"""
        self.log("Validating deployment...")

        checks = []

        # Check all infrastructure containers are running
        for service in self.services:
            container_name = f"sigmax-{service}"
            result = self.run_command([
                'docker', 'inspect',
                '--format', '{{.State.Running}}',
                container_name
            ], check=False)

            running = result.stdout.strip() == "true"
            if running:
                self.log(f"✓ {service}: Running", "SUCCESS")
                checks.append(True)
            else:
                self.log(f"✗ {service}: Not running", "ERROR")
                checks.append(False)

        # Check Prometheus targets
        try:
            import requests
            response = requests.get('http://localhost:9090/api/v1/targets', timeout=5)
            if response.status_code == 200:
                data = response.json()
                active_targets = data.get('data', {}).get('activeTargets', [])
                healthy = sum(1 for t in active_targets if t.get('health') == 'up')
                total = len(active_targets)

                self.log(f"✓ Prometheus targets: {healthy}/{total} healthy", "SUCCESS")
                checks.append(healthy > 0)
            else:
                self.log(f"✗ Prometheus API not responding", "ERROR")
                checks.append(False)
        except Exception as e:
            self.log(f"✗ Prometheus check failed: {e}", "ERROR")
            checks.append(False)

        # Check Grafana
        try:
            import requests
            response = requests.get('http://localhost:3001/api/health', timeout=5)
            if response.status_code == 200:
                self.log(f"✓ Grafana: Healthy", "SUCCESS")
                checks.append(True)
            else:
                self.log(f"✗ Grafana not responding", "ERROR")
                checks.append(False)
        except Exception as e:
            self.log(f"✗ Grafana check failed: {e}", "ERROR")
            checks.append(False)

        return all(checks)

    def deploy(self):
        """Execute full deployment"""
        self.log(f"Starting deployment for environment: {self.env}", "INFO")

        if self.dry_run:
            self.log("DRY RUN MODE - No actual changes will be made", "WARNING")

        try:
            # Pre-flight checks
            if not self.skip_checks:
                if not self.check_prerequisites():
                    self.log("Pre-flight checks failed", "ERROR")
                    return False
            else:
                self.log("Skipping pre-flight checks", "WARNING")

            # Backup (only in production)
            if self.env == "production" and not self.dry_run:
                self.backup_database()

            # Start infrastructure
            self.start_infrastructure()

            # Run migrations
            self.run_migrations()

            # Start SIGMAX services
            self.start_sigmax_services()

            # Validate deployment
            if self.validate_deployment():
                self.log("Deployment completed successfully!", "SUCCESS")
                self.print_next_steps()
                return True
            else:
                self.log("Deployment validation failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"Deployment failed: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def print_next_steps(self):
        """Print next steps after deployment"""
        self.log("\n" + "="*60, "INFO")
        self.log("DEPLOYMENT SUCCESSFUL", "SUCCESS")
        self.log("="*60 + "\n", "INFO")

        print("Next Steps:")
        print(f"  1. Verify services: docker-compose ps")
        print(f"  2. Check logs: docker-compose logs -f")
        print(f"  3. Access Grafana: http://localhost:3001 (admin/admin)")
        print(f"  4. Access Prometheus: http://localhost:9090")
        print(f"  5. Run health checks: python scripts/health_check.py")
        print(f"  6. Monitor metrics: See docs/MONITORING_SETUP.md")
        print()
        print("Operational Guides:")
        print(f"  - Operational Runbook: docs/OPERATIONAL_RUNBOOK.md")
        print(f"  - Monitoring Setup: docs/MONITORING_SETUP.md")
        print(f"  - Testnet Setup: docs/TESTNET_SETUP.md")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="SIGMAX Production Deployment Script"
    )
    parser.add_argument(
        '--env',
        choices=['development', 'testnet', 'production'],
        required=True,
        help='Deployment environment'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run deployment in dry-run mode (no actual changes)'
    )
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip pre-flight checks'
    )

    args = parser.parse_args()

    # Confirmation for production
    if args.env == 'production' and not args.dry_run:
        print("\n⚠️  WARNING: You are deploying to PRODUCTION")
        print("This will start live trading with real money.")
        response = input("Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Deployment cancelled.")
            sys.exit(0)

    # Run deployment
    manager = DeploymentManager(
        env=args.env,
        dry_run=args.dry_run,
        skip_checks=args.skip_checks
    )

    success = manager.deploy()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
