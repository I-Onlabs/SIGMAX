"""Configuration validation for SIGMAX"""

from typing import Dict, List, Optional
import os
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class Severity(Enum):
    ERROR = "error"      # Blocks startup
    WARNING = "warning"  # Works but suboptimal
    INFO = "info"        # Just informational


@dataclass
class ValidationResult:
    severity: Severity
    message: str
    variable: str


class ConfigValidator:
    """Validates environment configuration"""

    def __init__(self):
        self.results: List[ValidationResult] = []

    def validate_all(self) -> bool:
        """
        Validate all configuration

        Returns:
            True if no errors, False if any errors found
        """
        self._validate_trading_config()
        self._validate_llm_config()
        self._validate_database_config()
        self._validate_safety_limits()

        # Print results
        for result in self.results:
            if result.severity == Severity.ERROR:
                logger.error(f"❌ {result.variable}: {result.message}")
            elif result.severity == Severity.WARNING:
                logger.warning(f"⚠️  {result.variable}: {result.message}")
            else:
                logger.info(f"ℹ️  {result.variable}: {result.message}")

        # Return False if any errors
        has_errors = any(r.severity == Severity.ERROR for r in self.results)
        return not has_errors

    def _validate_trading_config(self):
        """Validate trading-related config"""
        mode = os.getenv("TRADING_MODE", "paper")
        if mode not in ["paper", "live"]:
            self.results.append(ValidationResult(
                Severity.ERROR,
                f"Invalid trading mode '{mode}'. Must be 'paper' or 'live'",
                "TRADING_MODE"
            ))

        if mode == "live":
            if not os.getenv("API_KEY"):
                self.results.append(ValidationResult(
                    Severity.ERROR,
                    "API_KEY required for live trading",
                    "API_KEY"
                ))
            if not os.getenv("API_SECRET"):
                self.results.append(ValidationResult(
                    Severity.ERROR,
                    "API_SECRET required for live trading",
                    "API_SECRET"
                ))

            # Strongly recommend testnet for first-time live trading
            testnet = os.getenv("TESTNET", "false").lower()
            if testnet != "true":
                self.results.append(ValidationResult(
                    Severity.WARNING,
                    "TESTNET=false with TRADING_MODE=live. Ensure you're ready for real trading!",
                    "TESTNET"
                ))

        # Validate exchange
        exchange = os.getenv("EXCHANGE", "binance").lower()
        supported_exchanges = ["binance", "coinbase", "kraken", "bybit", "okx"]
        if exchange not in supported_exchanges:
            self.results.append(ValidationResult(
                Severity.WARNING,
                f"Exchange '{exchange}' may not be fully supported. Recommended: {supported_exchanges}",
                "EXCHANGE"
            ))

    def _validate_llm_config(self):
        """Validate LLM configuration"""
        has_any_llm = any([
            os.getenv("OLLAMA_BASE_URL"),
            os.getenv("OPENAI_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY")
        ])

        if not has_any_llm:
            self.results.append(ValidationResult(
                Severity.WARNING,
                "No LLM provider configured. System will use fallback logic. "
                "For best results, configure Ollama (local) or OpenAI/Anthropic.",
                "LLM_CONFIG"
            ))
        else:
            # Check which providers are configured
            if os.getenv("OLLAMA_BASE_URL"):
                self.results.append(ValidationResult(
                    Severity.INFO,
                    f"Ollama configured at {os.getenv('OLLAMA_BASE_URL')}",
                    "OLLAMA"
                ))
            if os.getenv("OPENAI_API_KEY"):
                self.results.append(ValidationResult(
                    Severity.INFO,
                    "OpenAI API key configured",
                    "OPENAI"
                ))
            if os.getenv("ANTHROPIC_API_KEY"):
                self.results.append(ValidationResult(
                    Severity.INFO,
                    "Anthropic API key configured",
                    "ANTHROPIC"
                ))

    def _validate_database_config(self):
        """Validate database configuration"""
        if not os.getenv("POSTGRES_URL"):
            self.results.append(ValidationResult(
                Severity.WARNING,
                "POSTGRES_URL not set. Database features will be limited.",
                "POSTGRES_URL"
            ))

        if not os.getenv("REDIS_URL"):
            self.results.append(ValidationResult(
                Severity.INFO,
                "REDIS_URL not set. Caching will use in-memory storage.",
                "REDIS_URL"
            ))

    def _validate_safety_limits(self):
        """Validate safety limits make sense"""
        try:
            max_loss = float(os.getenv("MAX_DAILY_LOSS", 10))
            total_capital = float(os.getenv("TOTAL_CAPITAL", 50))
            max_position = float(os.getenv("MAX_POSITION_SIZE", 15))
            stop_loss = float(os.getenv("STOP_LOSS_PCT", 1.5))

            # Check daily loss vs capital
            if max_loss > total_capital * 0.5:
                self.results.append(ValidationResult(
                    Severity.WARNING,
                    f"MAX_DAILY_LOSS (${max_loss}) is >50% of TOTAL_CAPITAL (${total_capital}). "
                    f"Consider reducing to better protect capital.",
                    "MAX_DAILY_LOSS"
                ))

            # Check position size vs capital
            if max_position > total_capital * 0.5:
                self.results.append(ValidationResult(
                    Severity.WARNING,
                    f"MAX_POSITION_SIZE (${max_position}) is >50% of TOTAL_CAPITAL (${total_capital}). "
                    f"High concentration risk.",
                    "MAX_POSITION_SIZE"
                ))

            # Check stop loss percentage
            if stop_loss > 10:
                self.results.append(ValidationResult(
                    Severity.WARNING,
                    f"STOP_LOSS_PCT ({stop_loss}%) is very high. Typical values are 1-3%.",
                    "STOP_LOSS_PCT"
                ))

            # Check max open trades
            max_trades = int(os.getenv("MAX_OPEN_TRADES", 3))
            if max_trades > 10:
                self.results.append(ValidationResult(
                    Severity.WARNING,
                    f"MAX_OPEN_TRADES ({max_trades}) is high. May be difficult to manage.",
                    "MAX_OPEN_TRADES"
                ))

            # Check leverage
            max_leverage = int(os.getenv("MAX_LEVERAGE", 1))
            if max_leverage > 3:
                self.results.append(ValidationResult(
                    Severity.ERROR,
                    f"MAX_LEVERAGE ({max_leverage}x) exceeds safe limit of 3x. "
                    f"High leverage dramatically increases risk.",
                    "MAX_LEVERAGE"
                ))

        except ValueError as e:
            self.results.append(ValidationResult(
                Severity.ERROR,
                f"Invalid numeric value in safety limits: {e}",
                "SAFETY_LIMITS"
            ))

    def get_summary(self) -> Dict:
        """Get validation summary"""
        errors = [r for r in self.results if r.severity == Severity.ERROR]
        warnings = [r for r in self.results if r.severity == Severity.WARNING]
        infos = [r for r in self.results if r.severity == Severity.INFO]

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "info_count": len(infos),
            "errors": [{"variable": r.variable, "message": r.message} for r in errors],
            "warnings": [{"variable": r.variable, "message": r.message} for r in warnings]
        }
