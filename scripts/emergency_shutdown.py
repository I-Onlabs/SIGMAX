#!/usr/bin/env python3
"""
SIGMAX Emergency Shutdown Script

Provides emergency shutdown capabilities to immediately stop trading
and shut down all SIGMAX services in case of critical issues.

Usage:
    python scripts/emergency_shutdown.py --panic    # Immediate shutdown, cancel all orders
    python scripts/emergency_shutdown.py --graceful # Graceful shutdown with order cleanup
    python scripts/emergency_shutdown.py --status   # Check current trading status

PANIC BUTTON: Use --panic for immediate emergency stop
"""

import argparse
import asyncio
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class EmergencyShutdown:
    """Handles emergency shutdown procedures"""

    def __init__(self, mode: str = "graceful"):
        self.mode = mode  # "panic" or "graceful"
        self.project_root = Path(__file__).parent.parent
        self.shutdown_log = []

    def log(self, message: str, level: str = "INFO"):
        """Log shutdown message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        self.shutdown_log.append(log_entry)

        color_codes = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "CRITICAL": "\033[95m",
            "RESET": "\033[0m"
        }

        color = color_codes.get(level, "")
        reset = color_codes["RESET"]
        print(f"{color}{log_entry}{reset}")

    def run_command(self, cmd: List[str], check: bool = False) -> subprocess.CompletedProcess:
        """Run shell command"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            if check and result.returncode != 0:
                self.log(f"Command failed: {' '.join(cmd)}", "ERROR")
                self.log(f"Error: {result.stderr}", "ERROR")

            return result

        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {' '.join(cmd)}", "ERROR")
            return subprocess.CompletedProcess(cmd, 1, "", "Timeout")
        except Exception as e:
            self.log(f"Command exception: {e}", "ERROR")
            return subprocess.CompletedProcess(cmd, 1, "", str(e))

    async def cancel_all_orders(self):
        """Cancel all open orders on exchange"""
        self.log("Canceling all open orders...", "CRITICAL")

        try:
            import ccxt.async_support as ccxt
            import os

            # Load exchange credentials from environment
            exchanges_config = {
                'binance': {
                    'apiKey': os.getenv('BINANCE_API_KEY', ''),
                    'secret': os.getenv('BINANCE_API_SECRET', ''),
                    'enableRateLimit': True
                },
                'coinbase': {
                    'apiKey': os.getenv('COINBASE_API_KEY', ''),
                    'secret': os.getenv('COINBASE_API_SECRET', ''),
                    'enableRateLimit': True
                }
            }

            total_cancelled = 0

            for exchange_name, config in exchanges_config.items():
                # Skip if no credentials configured
                if not config['apiKey']:
                    self.log(f"Skipping {exchange_name} (no credentials)", "INFO")
                    continue

                try:
                    # Initialize exchange
                    exchange_class = getattr(ccxt, exchange_name)
                    exchange = exchange_class(config)

                    # Fetch all open orders
                    open_orders = await exchange.fetch_open_orders()

                    self.log(
                        f"Found {len(open_orders)} open orders on {exchange_name}",
                        "INFO"
                    )

                    # Cancel each order
                    for order in open_orders:
                        try:
                            await exchange.cancel_order(order['id'], order['symbol'])
                            self.log(
                                f"Cancelled {order['symbol']} order {order['id']}",
                                "SUCCESS"
                            )
                            total_cancelled += 1
                        except Exception as e:
                            self.log(
                                f"Failed to cancel order {order['id']}: {e}",
                                "ERROR"
                            )

                    await exchange.close()

                except Exception as e:
                    self.log(f"Failed to process {exchange_name}: {e}", "ERROR")

            self.log(f"✓ Cancelled {total_cancelled} orders total", "SUCCESS")

        except Exception as e:
            self.log(f"Failed to cancel orders: {e}", "ERROR")

    async def pause_trading(self):
        """Pause trading system"""
        self.log("Pausing trading system...", "CRITICAL")

        try:
            import redis.asyncio as redis

            # Set pause flag file
            pause_file = self.project_root / ".emergency_pause"
            pause_file.write_text(f"Emergency pause activated at {datetime.utcnow().isoformat()}\n")

            self.log(f"✓ Pause flag set: {pause_file}", "SUCCESS")

            # Send pause signal to running services via Redis
            try:
                redis_client = redis.from_url(
                    os.getenv('REDIS_URL', 'redis://localhost:6379'),
                    decode_responses=True
                )

                # Set pause flag in Redis for all services to read
                await redis_client.set('sigmax:emergency_pause', '1', ex=86400)  # 24h expiry

                # Publish pause event to all services
                await redis_client.publish('sigmax:control', json.dumps({
                    'command': 'pause',
                    'reason': 'emergency_shutdown',
                    'timestamp': datetime.utcnow().isoformat()
                }))

                self.log("✓ Pause signal sent to all services via Redis", "SUCCESS")

                await redis_client.close()

            except Exception as redis_err:
                self.log(f"Failed to send Redis pause signal: {redis_err}", "WARNING")
                self.log("Services will detect pause via file flag", "INFO")

        except Exception as e:
            self.log(f"Failed to set pause flag: {e}", "ERROR")

    def stop_sigmax_processes(self):
        """Stop all SIGMAX Python processes"""
        self.log("Stopping SIGMAX processes...", "CRITICAL")

        try:
            # Find all SIGMAX Python processes
            result = self.run_command(
                ['pgrep', '-f', 'python.*apps\\..*\\.main']
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                self.log(f"Found {len(pids)} SIGMAX processes", "INFO")

                for pid in pids:
                    self.log(f"Killing process {pid}...", "INFO")

                    if self.mode == "panic":
                        # SIGKILL for immediate stop
                        self.run_command(['kill', '-9', pid])
                    else:
                        # SIGTERM for graceful stop
                        self.run_command(['kill', '-15', pid])

                    time.sleep(0.1)

                self.log("✓ All SIGMAX processes stopped", "SUCCESS")
            else:
                self.log("No SIGMAX processes found running", "INFO")

        except Exception as e:
            self.log(f"Failed to stop processes: {e}", "ERROR")

    def stop_docker_services(self):
        """Stop Docker services"""
        self.log("Stopping Docker services...", "CRITICAL")

        try:
            services = [
                'sigmax-postgres',
                'sigmax-redis',
                'sigmax-clickhouse',
                'sigmax-prometheus',
                'sigmax-grafana',
                'sigmax-alertmanager'
            ]

            for service in services:
                self.log(f"Stopping {service}...", "INFO")

                if self.mode == "panic":
                    # Force stop
                    self.run_command(['docker', 'kill', service])
                else:
                    # Graceful stop
                    self.run_command(['docker', 'stop', '-t', '10', service])

            # If panic mode, stop all at once
            if self.mode == "panic":
                self.log("Force stopping all services...", "CRITICAL")
                self.run_command(['docker-compose', 'kill'])

            self.log("✓ Docker services stopped", "SUCCESS")

        except Exception as e:
            self.log(f"Failed to stop Docker services: {e}", "ERROR")

    def create_incident_report(self):
        """Create incident report"""
        self.log("Creating incident report...", "INFO")

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_dir = self.project_root / "incidents"
            report_dir.mkdir(exist_ok=True)

            report_file = report_dir / f"emergency_shutdown_{timestamp}.log"

            with open(report_file, 'w') as f:
                f.write(f"SIGMAX Emergency Shutdown Report\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Shutdown Type: {self.mode.upper()}\n")
                f.write(f"Timestamp: {datetime.utcnow().isoformat()}\n")
                f.write(f"\nShutdown Log:\n")
                f.write(f"{'-'*60}\n")

                for entry in self.shutdown_log:
                    f.write(f"{entry}\n")

                f.write(f"\n{'='*60}\n")
                f.write(f"Report saved: {report_file}\n")

            self.log(f"✓ Incident report created: {report_file}", "SUCCESS")

        except Exception as e:
            self.log(f"Failed to create incident report: {e}", "ERROR")

    async def shutdown(self):
        """Execute emergency shutdown"""
        self.log("\n" + "="*70, "CRITICAL")

        if self.mode == "panic":
            self.log("🚨 EMERGENCY PANIC SHUTDOWN INITIATED 🚨", "CRITICAL")
            self.log("ALL TRADING WILL BE STOPPED IMMEDIATELY", "CRITICAL")
        else:
            self.log("Emergency Graceful Shutdown Initiated", "WARNING")
            self.log("Trading will be stopped with cleanup", "WARNING")

        self.log("="*70 + "\n", "CRITICAL")

        try:
            # Step 1: Cancel all orders
            await self.cancel_all_orders()

            # Step 2: Pause trading
            await self.pause_trading()

            # Step 3: Stop SIGMAX processes
            self.stop_sigmax_processes()

            # Step 4: Stop Docker services (only in panic mode)
            if self.mode == "panic":
                self.stop_docker_services()
            else:
                self.log("Leaving infrastructure running (graceful mode)", "INFO")

            # Step 5: Create incident report
            self.create_incident_report()

            self.log("\n" + "="*70, "SUCCESS")
            self.log(f"Emergency shutdown completed: {self.mode.upper()}", "SUCCESS")
            self.log("="*70 + "\n", "SUCCESS")

            self.print_next_steps()

        except Exception as e:
            self.log(f"\nShutdown failed with error: {e}", "ERROR")
            self.log("Manual intervention may be required", "ERROR")
            import traceback
            traceback.print_exc()

    def print_next_steps(self):
        """Print next steps after shutdown"""
        print("\nNext Steps:")
        print("  1. Review incident report in incidents/ directory")
        print("  2. Investigate root cause of emergency shutdown")
        print("  3. Check exchange for any remaining open orders")
        print("  4. Review system logs for errors")
        print("  5. Run health check: python scripts/health_check.py")
        print()
        print("To Resume Trading:")
        print("  1. Fix the issue that triggered shutdown")
        print("  2. Remove pause flag: rm .emergency_pause")
        print("  3. Restart services: python scripts/deploy.py --env <env>")
        print("  4. Monitor closely using Grafana dashboards")
        print()
        print("Documentation:")
        print("  - Incident Response: docs/OPERATIONAL_RUNBOOK.md#incident-response")
        print("  - Emergency Procedures: docs/OPERATIONAL_RUNBOOK.md#emergency-procedures")
        print()

    def check_status(self):
        """Check current trading status"""
        self.log("Checking trading status...", "INFO")

        print("\n" + "="*70)
        print("SIGMAX Trading Status")
        print("="*70 + "\n")

        # Check for pause flag
        pause_file = self.project_root / ".emergency_pause"
        if pause_file.exists():
            print("⚠️  TRADING IS PAUSED")
            print(f"Pause file: {pause_file}")
            print(f"Content: {pause_file.read_text()}")
        else:
            print("✓ No pause flag detected")

        print()

        # Check SIGMAX processes
        result = self.run_command(['pgrep', '-f', 'python.*apps\\..*\\.main'])
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"✓ SIGMAX Processes: {len(pids)} running")
            for pid in pids:
                # Get process name
                ps_result = self.run_command(['ps', '-p', pid, '-o', 'cmd='])
                if ps_result.returncode == 0:
                    print(f"  - PID {pid}: {ps_result.stdout.strip()[:80]}")
        else:
            print("✗ No SIGMAX processes running")

        print()

        # Check Docker services
        services = ['sigmax-postgres', 'sigmax-redis', 'sigmax-prometheus', 'sigmax-grafana']
        print("Docker Services:")
        for service in services:
            result = self.run_command(['docker', 'inspect', '--format', '{{.State.Running}}', service])
            if result.returncode == 0 and result.stdout.strip() == "true":
                print(f"  ✓ {service}: Running")
            else:
                print(f"  ✗ {service}: Stopped")

        print("\n" + "="*70 + "\n")


async def main():
    parser = argparse.ArgumentParser(
        description="SIGMAX Emergency Shutdown Script",
        epilog="Use --panic for immediate emergency stop of all trading"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--panic',
        action='store_true',
        help='🚨 PANIC SHUTDOWN: Immediate stop, cancel all orders, kill all processes'
    )
    group.add_argument(
        '--graceful',
        action='store_true',
        help='Graceful shutdown: Stop trading cleanly, leave infrastructure running'
    )
    group.add_argument(
        '--status',
        action='store_true',
        help='Check current trading status without shutting down'
    )

    args = parser.parse_args()

    # Status check
    if args.status:
        manager = EmergencyShutdown()
        manager.check_status()
        sys.exit(0)

    # Determine mode
    mode = "panic" if args.panic else "graceful"

    # Confirmation
    if mode == "panic":
        print("\n" + "="*70)
        print("⚠️  WARNING: PANIC SHUTDOWN MODE ⚠️")
        print("="*70)
        print()
        print("This will IMMEDIATELY:")
        print("  1. Cancel ALL open orders on exchange")
        print("  2. KILL all SIGMAX processes (SIGKILL)")
        print("  3. STOP all Docker services")
        print("  4. Create incident report")
        print()
        print("Use this ONLY in emergency situations!")
        print()
        response = input("Type 'PANIC' to confirm emergency shutdown: ")
        if response != 'PANIC':
            print("Shutdown cancelled.")
            sys.exit(0)
    else:
        print("\n" + "="*70)
        print("Graceful Shutdown Mode")
        print("="*70)
        print()
        print("This will:")
        print("  1. Cancel all open orders")
        print("  2. Pause trading")
        print("  3. Stop SIGMAX processes gracefully")
        print("  4. Leave infrastructure running")
        print()
        response = input("Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("Shutdown cancelled.")
            sys.exit(0)

    # Execute shutdown
    manager = EmergencyShutdown(mode=mode)
    await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
