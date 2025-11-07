"""
SIGMAX Service Runner

Orchestrates all services for the trading system.
"""

import asyncio
import sys
import signal
import argparse
from pathlib import Path
from typing import List, Dict
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pkg.common import setup_logging, get_logger, load_config


class ServiceRunner:
    """Orchestrates all SIGMAX services"""
    
    def __init__(self, config, services: List[str]):
        self.config = config
        self.services_to_run = services
        self.logger = get_logger(__name__)
        
        # Service definitions
        self.service_defs = {
            'ingest': {
                'name': 'Market Data Ingestion',
                'module': 'apps.ingest_cex.main',
                'required': True
            },
            'book': {
                'name': 'Order Book Shard',
                'module': 'apps.book_shard.main',
                'required': True
            },
            'features': {
                'name': 'Feature Extraction',
                'module': 'apps.features.main',
                'required': True
            },
            'volatility': {
                'name': 'Volatility Scanner',
                'module': 'apps.signals.volatility_scanner.main',
                'required': False
            },
            'decision': {
                'name': 'Decision Layer',
                'module': 'apps.decision.main',
                'required': True
            },
            'risk': {
                'name': 'Pre-Trade Risk',
                'module': 'apps.risk.main',
                'required': True
            },
            'router': {
                'name': 'Smart Order Router',
                'module': 'apps.router.main',
                'required': True
            },
            'exec': {
                'name': 'Execution Gateway',
                'module': 'apps.exec_cex.main',
                'required': True
            }
        }
        
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        
    async def start(self):
        """Start all services"""
        self.logger.info("starting_sigmax_services",
                        profile=self.config.profile,
                        services=self.services_to_run)
        
        self.running = True
        
        # Start each service
        for service_key in self.services_to_run:
            if service_key not in self.service_defs:
                self.logger.warning("unknown_service", service=service_key)
                continue
            
            service_def = self.service_defs[service_key]
            
            try:
                # Start service process
                cmd = [
                    sys.executable,
                    '-m',
                    service_def['module'],
                    '--profile', self.config.profile
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                self.processes[service_key] = process
                
                self.logger.info("service_started",
                               service=service_key,
                               name=service_def['name'],
                               pid=process.pid)
                
                # Small delay between service starts
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error("service_start_error",
                                service=service_key,
                                error=str(e))
                if service_def['required']:
                    raise
        
        self.logger.info("all_services_started", count=len(self.processes))
        
    async def stop(self):
        """Stop all services"""
        self.logger.info("stopping_sigmax_services")
        self.running = False
        
        # Stop services in reverse order
        for service_key in reversed(self.services_to_run):
            if service_key in self.processes:
                process = self.processes[service_key]
                
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    
                    self.logger.info("service_stopped",
                                   service=service_key,
                                   pid=process.pid)
                except Exception as e:
                    self.logger.error("service_stop_error",
                                    service=service_key,
                                    error=str(e))
                    process.kill()
        
        self.logger.info("all_services_stopped")
    
    async def monitor(self):
        """Monitor service health"""
        while self.running:
            # Check if any process has died
            for service_key, process in list(self.processes.items()):
                if process.poll() is not None:
                    # Process has exited
                    returncode = process.returncode
                    self.logger.error("service_exited",
                                    service=service_key,
                                    returncode=returncode)
                    
                    service_def = self.service_defs[service_key]
                    if service_def['required']:
                        self.logger.error("required_service_failed",
                                        service=service_key)
                        await self.stop()
                        return
            
            await asyncio.sleep(5)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SIGMAX Service Runner")
    parser.add_argument("--profile", default="a", choices=["a", "b"],
                       help="Profile to use (a=simple, b=performance)")
    parser.add_argument("--config", help="Config file path")
    parser.add_argument("--services", nargs="+",
                       default=['ingest', 'book', 'features', 'volatility',
                               'decision', 'risk', 'router', 'exec'],
                       help="Services to run")
    args = parser.parse_args()
    
    # Load config
    config = load_config(profile=args.profile, config_path=args.config)
    
    # Setup logging
    setup_logging(
        level=config.observability.log_level,
        log_path=config.observability.log_path,
        json_logs=config.is_production()
    )
    
    logger = get_logger(__name__)
    logger.info("sigmax_runner_starting",
                profile=config.profile,
                environment=config.environment)
    
    # Create runner
    runner = ServiceRunner(config, args.services)
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("received_signal", signal=sig)
        asyncio.create_task(runner.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run services
    try:
        await runner.start()
        await runner.monitor()
    except Exception as e:
        logger.error("runner_error", error=str(e), exc_info=True)
        raise
    finally:
        await runner.stop()
        logger.info("sigmax_runner_stopped")


if __name__ == "__main__":
    asyncio.run(main())
