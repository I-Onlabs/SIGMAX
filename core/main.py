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
from modules.alerts import AlertManager, TradingAlerts, get_alert_manager, set_alert_manager
from modules.performance_monitor import PerformanceMonitor, get_performance_monitor, set_performance_monitor
from modules.ml_predictor import MLPredictor
from modules.backtest import Backtester
from modules.portfolio_rebalancer import PortfolioRebalancer
from modules.regime_detector import RegimeDetector
from agents.sentiment import SentimentAgent
from utils.healthcheck import HealthChecker
from utils.telegram_bot import TelegramBot

# Load environment variables
load_dotenv()

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
        self.alert_manager: Optional[AlertManager] = None
        self.trading_alerts: Optional[TradingAlerts] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.ml_predictor: Optional[MLPredictor] = None
        self.sentiment_agent: Optional[SentimentAgent] = None
        self.backtester: Optional[Backtester] = None
        self.portfolio_rebalancer: Optional[PortfolioRebalancer] = None
        self.regime_detector: Optional[RegimeDetector] = None
        self.telegram_bot: Optional[TelegramBot] = None
        self.health_checker: Optional[HealthChecker] = None

        logger.info(f"🚀 SIGMAX initialized in {mode} mode with {risk_profile} profile")

    def _get_llm(self):
        """Get configured LLM"""
        # Priority: Ollama (local) > OpenAI > Mock
        if os.getenv("OLLAMA_BASE_URL"):
            from langchain_ollama import ChatOllama
            return ChatOllama(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "llama3.1"),
                temperature=0.7
            )
        elif os.getenv("OPENAI_API_KEY"):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                temperature=0.7
            )
        else:
            logger.warning("No LLM configured, using mock responses")
            return None

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

                # Initialize alert manager
                task = progress.add_task("Initializing alert system...", total=None)
                self.alert_manager = AlertManager(
                    enabled_channels=[],  # Configure in production
                    webhook_urls={},
                    throttle_seconds=60
                )
                self.trading_alerts = TradingAlerts(self.alert_manager)
                set_alert_manager(self.alert_manager)
                progress.remove_task(task)
                logger.info("✓ Alert manager initialized")

                # Initialize performance monitor
                task = progress.add_task("Initializing performance monitor...", total=None)
                self.performance_monitor = PerformanceMonitor(
                    history_size=10000,
                    aggregate_interval=60
                )
                await self.performance_monitor.start()
                set_performance_monitor(self.performance_monitor)
                progress.remove_task(task)
                logger.info("✓ Performance monitor initialized")

                # Initialize ML predictor
                task = progress.add_task("Initializing ML predictor...", total=None)
                self.ml_predictor = MLPredictor()
                progress.remove_task(task)
                logger.info("✓ ML predictor initialized")

                # Initialize sentiment agent
                task = progress.add_task("Initializing sentiment agent...", total=None)
                from langchain_openai import ChatOpenAI
                llm = self._get_llm()
                self.sentiment_agent = SentimentAgent(llm)
                progress.remove_task(task)
                logger.info("✓ Sentiment agent initialized")

                # Initialize market regime detector
                task = progress.add_task("Initializing regime detector...", total=None)
                self.regime_detector = RegimeDetector()
                progress.remove_task(task)
                logger.info("✓ Regime detector initialized")

                # Initialize portfolio rebalancer
                task = progress.add_task("Initializing portfolio rebalancer...", total=None)
                self.portfolio_rebalancer = PortfolioRebalancer(
                    target_weights={'BTC/USDT': 0.6, 'ETH/USDT': 0.3, 'SOL/USDT': 0.1},
                    rebalance_threshold=0.05
                )
                progress.remove_task(task)
                logger.info("✓ Portfolio rebalancer initialized")

                # Initialize backtester
                task = progress.add_task("Initializing backtester...", total=None)
                self.backtester = Backtester(initial_capital=50.0)
                progress.remove_task(task)
                logger.info("✓ Backtester initialized")

                # Initialize multi-agent orchestrator
                task = progress.add_task("Initializing agent swarm...", total=None)
                self.orchestrator = SIGMAXOrchestrator(
                    data_module=self.data_module,
                    execution_module=self.execution_module,
                    quantum_module=self.quantum_module,
                    rl_module=self.rl_module,
                    arbitrage_module=self.arbitrage_module,
                    compliance_module=self.compliance_module,
                    alert_manager=self.alert_manager,
                    trading_alerts=self.trading_alerts,
                    performance_monitor=self.performance_monitor,
                    ml_predictor=self.ml_predictor,
                    sentiment_agent=self.sentiment_agent,
                    regime_detector=self.regime_detector,
                    portfolio_rebalancer=self.portfolio_rebalancer,
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

        # Stop performance monitor
        if self.performance_monitor:
            await self.performance_monitor.stop()

        # Stop health checker
        if self.health_checker:
            await self.health_checker.stop()

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
        if not args.start or not args.end:
            console.print("[red]Error: --start and --end dates required for backtest mode[/red]")
            console.print("Example: python main.py --backtest --start 2024-01-01 --end 2024-12-31")
            sys.exit(1)

        logger.info(f"Running backtest from {args.start} to {args.end}")
        console.print(f"[cyan]Running backtest: {args.start} to {args.end}[/cyan]")

        from datetime import datetime as dt
        import numpy as np

        # Parse dates
        start_date = dt.strptime(args.start, "%Y-%m-%d")
        end_date = dt.strptime(args.end, "%Y-%m-%d")

        # Generate synthetic data for demonstration
        days = (end_date - start_date).days
        timestamps = [start_date.timestamp() + i * 86400 for i in range(days)]

        # Mock OHLCV data
        data = {
            'BTC/USDT': np.random.rand(days, 6)
        }
        data['BTC/USDT'][:, 0] = timestamps
        data['BTC/USDT'][:, 4] = 50000 + np.cumsum(np.random.randn(days) * 500)  # Close prices

        # Simple strategy function
        async def simple_strategy(market_data, timestamp):
            """Simple moving average crossover strategy"""
            signals = []
            for symbol, ohlcv in market_data.items():
                if len(ohlcv) < 20:
                    continue

                closes = ohlcv[:, 4]
                sma_fast = np.mean(closes[-5:])
                sma_slow = np.mean(closes[-20:])

                if sma_fast > sma_slow:
                    signals.append({'symbol': symbol, 'action': 'buy', 'size': 0.01})
                elif sma_fast < sma_slow:
                    signals.append({'symbol': symbol, 'action': 'sell', 'size': 0.01})

            return signals

        # Run backtest
        result = await sigmax.backtester.run(
            strategy_func=simple_strategy,
            data=data,
            start_date=start_date,
            end_date=end_date
        )

        # Display results
        console.print("\n[bold green]Backtest Results:[/bold green]")
        console.print(f"Total Trades: {result.total_trades}")
        console.print(f"Winning Trades: {result.winning_trades}")
        console.print(f"Win Rate: {result.win_rate:.2%}")
        console.print(f"Total PnL: ${result.total_pnl:.2f}")
        console.print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        console.print(f"Sortino Ratio: {result.sortino_ratio:.2f}")
        console.print(f"Max Drawdown: ${result.max_drawdown:.2f}")
        console.print(f"Profit Factor: {result.profit_factor:.2f}")

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
