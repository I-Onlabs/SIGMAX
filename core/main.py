#!/usr/bin/env python3
"""
SIGMAX - Autonomous Multi-Agent AI Crypto Trading OS
Main Orchestrator Entry Point
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import SIGMAXOrchestrator
from modules.data import DataModule
from modules.execution import ExecutionModule
from modules.quantum import QuantumModule
from modules.rl import RLModule
from modules.arbitrage import ArbitrageModule
from modules.compliance import ComplianceModule
from modules.observability import (
    initialize_observability,
    shutdown_observability,
    SigNozConfig,
    OTEL_AVAILABLE
)
from utils.healthcheck import HealthChecker
from utils.telegram_bot import TelegramBot

# Load environment variables
load_dotenv()

# Validate configuration
from config.validator import ConfigValidator

validator = ConfigValidator()
if not validator.validate_all():
    from rich.console import Console as ErrorConsole
    error_console = ErrorConsole()
    error_console.print("[bold red]❌ Configuration validation failed. Please fix errors above.[/bold red]")
    sys.exit(1)

# Configure logger
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(os.getenv("LOG_FILE", "logs/sigmax.log"))
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL, colorize=True)
logger.add(
    LOG_FILE,
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    compression="zip"
)

console = Console()


class SIGMAX:
    """
    SIGMAX - Autonomous Multi-Agent Trading Operating System

    The main orchestrator that coordinates:
    - Multi-agent debate system (bull/bear/researcher)
    - Quantum portfolio optimization
    - Risk management & compliance
    - Trading execution via Freqtrade
    - Real-time monitoring & reporting
    """

    def __init__(
        self,
        mode: str = "paper",
        risk_profile: str = "conservative",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize SIGMAX

        Args:
            mode: Trading mode ('paper', 'live')
            risk_profile: Risk profile ('conservative', 'balanced', 'aggressive')
            config: Optional configuration overrides
        """
        self.mode = mode
        self.risk_profile = risk_profile
        self.config = config or {}

        self.running = False
        self.start_time = None

        # Initialize modules
        self.orchestrator: Optional[SIGMAXOrchestrator] = None
        self.data_module: Optional[DataModule] = None
        self.execution_module: Optional[ExecutionModule] = None
        self.quantum_module: Optional[QuantumModule] = None
        self.rl_module: Optional[RLModule] = None
        self.arbitrage_module: Optional[ArbitrageModule] = None
        self.compliance_module: Optional[ComplianceModule] = None
        self.observability_manager = None
        self.telegram_bot: Optional[TelegramBot] = None
        self.health_checker: Optional[HealthChecker] = None

        logger.info(f"🚀 SIGMAX initialized in {mode} mode with {risk_profile} profile")

    async def initialize(self):
        """Initialize all modules"""
        try:
            console.print(
                Panel.fit(
                    "[bold cyan]🤖 SIGMAX - Autonomous Multi-Agent AI Trading OS[/bold cyan]\n"
                    f"Mode: {self.mode.upper()} | Profile: {self.risk_profile}",
                    title="Initializing",
                    border_style="cyan"
                )
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:

                # Initialize observability (OpenTelemetry + SigNoz)
                if os.getenv("OBSERVABILITY_ENABLED", "true").lower() == "true" and OTEL_AVAILABLE:
                    task = progress.add_task("Initializing observability (SigNoz)...", total=None)
                    config = SigNozConfig(
                        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"),
                        service_name=os.getenv("OTEL_SERVICE_NAME", "sigmax"),
                        service_version=os.getenv("SIGMAX_VERSION", "1.0.0"),
                        environment=os.getenv("ENVIRONMENT", self.mode),
                        enable_traces=os.getenv("OTEL_TRACES_ENABLED", "true").lower() == "true",
                        enable_metrics=os.getenv("OTEL_METRICS_ENABLED", "true").lower() == "true",
                        enable_logs=os.getenv("OTEL_LOGS_ENABLED", "true").lower() == "true",
                        enable_console=os.getenv("OTEL_CONSOLE_ENABLED", "false").lower() == "true"
                    )
                    self.observability_manager = initialize_observability(config)
                    progress.remove_task(task)
                    logger.info("✓ Observability initialized")

                # Initialize data module
                task = progress.add_task("Initializing data module...", total=None)
                self.data_module = DataModule()
                await self.data_module.initialize()
                progress.remove_task(task)
                logger.info("✓ Data module initialized")

                # Initialize execution module
                task = progress.add_task("Initializing execution module...", total=None)
                self.execution_module = ExecutionModule(mode=self.mode)
                await self.execution_module.initialize()
                progress.remove_task(task)
                logger.info("✓ Execution module initialized")

                # Initialize quantum module (if enabled)
                if os.getenv("QUANTUM_ENABLED", "true").lower() == "true":
                    task = progress.add_task("Initializing quantum optimizer...", total=None)
                    self.quantum_module = QuantumModule()
                    await self.quantum_module.initialize()
                    progress.remove_task(task)
                    logger.info("✓ Quantum module initialized")

                # Initialize RL module
                task = progress.add_task("Initializing RL module...", total=None)
                self.rl_module = RLModule()
                await self.rl_module.initialize()
                progress.remove_task(task)
                logger.info("✓ RL module initialized")

                # Initialize arbitrage module (if enabled)
                if os.getenv("FEATURE_ARBITRAGE", "true").lower() == "true":
                    task = progress.add_task("Initializing arbitrage scanner...", total=None)
                    self.arbitrage_module = ArbitrageModule()
                    await self.arbitrage_module.initialize()
                    progress.remove_task(task)
                    logger.info("✓ Arbitrage module initialized")

                # Initialize compliance module
                task = progress.add_task("Initializing compliance module...", total=None)
                self.compliance_module = ComplianceModule()
                await self.compliance_module.initialize()
                progress.remove_task(task)
                logger.info("✓ Compliance module initialized")

                # Initialize multi-agent orchestrator
                task = progress.add_task("Initializing agent swarm...", total=None)
                self.orchestrator = SIGMAXOrchestrator(
                    data_module=self.data_module,
                    execution_module=self.execution_module,
                    quantum_module=self.quantum_module,
                    rl_module=self.rl_module,
                    arbitrage_module=self.arbitrage_module,
                    compliance_module=self.compliance_module,
                    risk_profile=self.risk_profile
                )
                await self.orchestrator.initialize()
                progress.remove_task(task)
                logger.info("✓ Agent orchestrator initialized")

                # Initialize Telegram bot (if enabled)
                if os.getenv("TELEGRAM_ENABLED", "false").lower() == "true":
                    task = progress.add_task("Initializing Telegram bot...", total=None)
                    self.telegram_bot = TelegramBot(orchestrator=self.orchestrator)
                    await self.telegram_bot.initialize()
                    progress.remove_task(task)
                    logger.info("✓ Telegram bot initialized")

                # Initialize health checker
                task = progress.add_task("Starting health checker...", total=None)
                self.health_checker = HealthChecker(self)
                await self.health_checker.start()
                progress.remove_task(task)
                logger.info("✓ Health checker started")

            console.print("\n[bold green]✓ All modules initialized successfully![/bold green]\n")
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            console.print(f"[bold red]❌ Initialization failed: {e}[/bold red]")
            return False

    async def start(self):
        """Start SIGMAX trading system"""
        if self.running:
            logger.warning("SIGMAX is already running")
            return

        try:
            self.running = True
            self.start_time = datetime.now()

            logger.info("🚀 Starting SIGMAX trading system...")
            console.print("[bold green]🚀 SIGMAX is now running![/bold green]")

            # Start orchestrator
            await self.orchestrator.start()

            # Start Telegram bot if enabled
            if self.telegram_bot:
                await self.telegram_bot.start()

            # Main loop
            while self.running:
                await asyncio.sleep(1)

                # Check health
                health = await self.health_checker.check()
                if not health.get("healthy", False):
                    logger.warning("⚠️ Health check failed, pausing...")
                    await self.pause()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            await self.stop()

    async def pause(self):
        """Pause trading (keep monitoring)"""
        if self.orchestrator:
            await self.orchestrator.pause()
        logger.info("⏸️ SIGMAX paused")

    async def resume(self):
        """Resume trading"""
        if self.orchestrator:
            await self.orchestrator.resume()
        logger.info("▶️ SIGMAX resumed")

    async def stop(self):
        """Stop SIGMAX trading system"""
        logger.info("🛑 Stopping SIGMAX...")

        self.running = False

        # Stop orchestrator
        if self.orchestrator:
            await self.orchestrator.stop()

        # Stop Telegram bot
        if self.telegram_bot:
            await self.telegram_bot.stop()

        # Stop health checker
        if self.health_checker:
            await self.health_checker.stop()

        # Shutdown observability
        if self.observability_manager:
            shutdown_observability()
            logger.info("✓ Observability shutdown complete")

        # Generate session report
        await self._generate_session_report()

        console.print("[bold yellow]👋 SIGMAX stopped gracefully[/bold yellow]")
        logger.info("👋 SIGMAX stopped")

    async def emergency_stop(self):
        """Emergency stop - close all positions immediately"""
        logger.critical("🚨 EMERGENCY STOP INITIATED")
        console.print("[bold red]🚨 EMERGENCY STOP - Closing all positions![/bold red]")

        try:
            if self.execution_module:
                await self.execution_module.close_all_positions()

            await self.stop()

        except Exception as e:
            logger.error(f"Error during emergency stop: {e}", exc_info=True)

    async def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            "running": self.running,
            "mode": self.mode,
            "risk_profile": self.risk_profile,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "modules": {}
        }

        if self.orchestrator:
            status["agents"] = await self.orchestrator.get_status()

        if self.execution_module:
            status["trading"] = await self.execution_module.get_status()

        if self.quantum_module:
            status["quantum"] = await self.quantum_module.get_status()

        return status

    async def _generate_session_report(self):
        """Generate end-of-session report"""
        try:
            if not self.start_time:
                return

            duration = datetime.now() - self.start_time
            status = await self.get_status()

            report = f"""
╔══════════════════════════════════════════════════════════╗
║            SIGMAX SESSION REPORT                         ║
╚══════════════════════════════════════════════════════════╝

Session Duration: {duration}
Mode: {self.mode}
Risk Profile: {self.risk_profile}

{'-' * 60}
"""

            # Add trading stats if available
            if "trading" in status:
                report += "\nTrading Statistics:\n"
                for key, value in status["trading"].items():
                    report += f"  {key}: {value}\n"

            # Save report
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)

            report_file = report_dir / f"session_{self.start_time.strftime('%Y%m%d_%H%M%S')}.txt"
            report_file.write_text(report)

            console.print(f"\n📊 Session report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Error generating session report: {e}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SIGMAX - Autonomous Multi-Agent Trading OS")
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default="paper",
        help="Trading mode"
    )
    parser.add_argument(
        "--risk-profile",
        choices=["conservative", "balanced", "aggressive"],
        default="conservative",
        help="Risk profile"
    )
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run backtest mode"
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Backtest start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end",
        type=str,
        help="Backtest end date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    # Create SIGMAX instance
    sigmax = SIGMAX(
        mode=args.mode,
        risk_profile=args.risk_profile
    )

    # Initialize
    if not await sigmax.initialize():
        logger.error("Failed to initialize SIGMAX")
        sys.exit(1)

    # Run
    if args.backtest:
        logger.info(f"Running backtest from {args.start} to {args.end}")

        if not args.start or not args.end:
            console.print("[red]Error: Backtest requires --start and --end dates (YYYY-MM-DD)[/red]")
            sys.exit(1)

        try:
            import numpy as np
            from modules.backtest import Backtester

            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")

            # Validate date range
            if start_date >= end_date:
                console.print("[red]Error: Start date must be before end date[/red]")
                sys.exit(1)

            if (end_date - start_date).days < 7:
                console.print("[yellow]Warning: Short backtest period (<7 days). Results may not be statistically significant.[/yellow]")

            console.print(f"\n[bold cyan]📊 Starting Backtest[/bold cyan]")
            console.print(f"Period: {args.start} to {args.end}")
            console.print(f"Duration: {(end_date - start_date).days} days\n")

            # Initialize backtester
            initial_capital = float(os.getenv("TOTAL_CAPITAL", 50))
            backtester = Backtester(
                initial_capital=initial_capital,
                commission=0.001,  # 0.1%
                slippage=0.0005    # 0.05%
            )

            # Define strategy function using orchestrator
            symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

            async def backtest_strategy(market_data: dict, timestamp: datetime) -> dict:
                """Strategy that uses SIGMAX orchestrator for decisions"""
                signals = {}

                for symbol in symbols:
                    if symbol not in market_data:
                        continue

                    try:
                        # Prepare market data dict for orchestrator
                        price = float(market_data[symbol][4])  # Close price

                        market_dict = {
                            "symbol": symbol,
                            "price": price,
                            "timestamp": timestamp.isoformat(),
                            "ohlcv": []  # Simplified for backtest
                        }

                        # Get decision from orchestrator
                        decision = await sigmax.orchestrator.analyze_symbol(
                            symbol=symbol,
                            market_data=market_dict
                        )

                        # Convert decision to signal
                        signals[symbol] = {
                            "action": decision.get("action", "hold"),
                            "confidence": decision.get("confidence", 0.5),
                            "reason": decision.get("reasoning", {}).get("technical", "")[:100]
                        }

                    except Exception as e:
                        logger.warning(f"Error analyzing {symbol} in backtest: {e}")
                        signals[symbol] = {"action": "hold", "confidence": 0.0}

                return signals

            # Fetch historical data
            console.print("[cyan]Fetching historical data...[/cyan]")

            data = {}
            for symbol in symbols:
                try:
                    ohlcv = await sigmax.data_module.get_historical_data(
                        symbol=symbol,
                        start=start_date,
                        end=end_date,
                        timeframe="1h"
                    )

                    if ohlcv and len(ohlcv) > 0:
                        data[symbol] = np.array(ohlcv)
                        console.print(f"  ✓ {symbol}: {len(ohlcv)} candles")
                    else:
                        # Use mock data if no real data available
                        from testing.fixtures import MockMarketData
                        logger.warning(f"No historical data for {symbol}, using mock data")

                        mock_ohlcv = MockMarketData.generate_ohlcv(
                            symbol=symbol,
                            periods=(end_date - start_date).days * 24,
                            timeframe_minutes=60
                        )
                        data[symbol] = np.array(mock_ohlcv)
                        console.print(f"  ⚠ {symbol}: {len(mock_ohlcv)} mock candles")

                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")

            if not data:
                console.print("[red]Error: No data available for backtest[/red]")
                sys.exit(1)

            console.print(f"\n[cyan]Running backtest with {len(data)} symbols...[/cyan]\n")

            # Run backtest
            results = await backtester.run(
                strategy_func=backtest_strategy,
                data=data,
                start_date=start_date,
                end_date=end_date
            )

            # Display results
            report = backtester.generate_report(results)
            console.print(report)

            # Save detailed results
            report_dir = Path("reports/backtests")
            report_dir.mkdir(parents=True, exist_ok=True)

            report_file = report_dir / f"backtest_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.txt"
            report_file.write_text(report)

            console.print(f"\n[green]✓ Backtest report saved to: {report_file}[/green]")

            # Exit after backtest
            sys.exit(0)

        except ValueError as e:
            console.print(f"[red]Error: Invalid date format. Use YYYY-MM-DD (e.g., 2024-01-01)[/red]")
            logger.error(f"Date parsing error: {e}")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Backtest failed: {e}[/red]")
            logger.error(f"Backtest error: {e}", exc_info=True)
            sys.exit(1)
    else:
        await sigmax.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
