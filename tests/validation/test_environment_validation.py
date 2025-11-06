"""
Environment variable validation tests.
Tests the ConfigValidator with various configuration scenarios.
"""

import pytest
import os
from unittest.mock import patch
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.config.validator import ConfigValidator, Severity


class TestEnvironmentValidation:
    """Test environment variable validation"""

    @pytest.fixture
    def clean_env(self):
        """Provide a clean environment for testing"""
        original_env = os.environ.copy()
        # Clear all SIGMAX-related env vars
        for key in list(os.environ.keys()):
            if any(prefix in key for prefix in ['TRADING_', 'OLLAMA_', 'OPENAI_', 'ANTHROPIC_', 'POSTGRES_', 'REDIS_', 'MAX_', 'STOP_', 'API_', 'EXCHANGE', 'TESTNET', 'TOTAL_CAPITAL']):
                del os.environ[key]
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    def test_minimal_valid_config(self, clean_env):
        """Test minimal valid configuration"""
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Minimal Valid Config ===")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")
        print(f"Valid: {result}")

        # Should have some warnings (no LLM, no DB) but no errors
        assert summary['error_count'] == 0
        assert result == True

    def test_live_trading_requires_api_keys(self, clean_env):
        """Test that live trading requires API keys"""
        os.environ.update({
            'TRADING_MODE': 'live',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Live Trading Without API Keys ===")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")

        # Should have errors for missing API keys
        assert summary['error_count'] > 0
        assert result == False

    def test_live_trading_with_api_keys(self, clean_env):
        """Test live trading with proper API keys"""
        os.environ.update({
            'TRADING_MODE': 'live',
            'API_KEY': 'test_api_key_12345',
            'API_SECRET': 'test_api_secret_67890',
            'EXCHANGE': 'binance',
            'TESTNET': 'True',  # Using testnet for safety
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Live Trading With API Keys ===")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")

        # Should pass validation
        assert summary['error_count'] == 0
        assert result == True

    def test_dangerous_leverage_fails(self, clean_env):
        """Test that excessive leverage is rejected"""
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '10'  # Too high!
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Dangerous Leverage Test ===")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")

        # Should have errors for excessive leverage
        assert summary['error_count'] > 0
        assert result == False

    def test_excessive_risk_limits_warning(self, clean_env):
        """Test that excessive risk limits generate warnings"""
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '6000',  # 60% of capital - excessive
            'MAX_POSITION_SIZE': '7000',  # 70% of capital - excessive
            'STOP_LOSS_PCT': '15',  # 15% stop loss - excessive
            'MAX_OPEN_TRADES': '15',  # Too many trades
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Excessive Risk Limits ===")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")

        # Should have multiple warnings
        assert summary['warning_count'] > 0

    def test_llm_configuration_validation(self, clean_env):
        """Test LLM configuration validation"""

        # Test 1: No LLM configured
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        validator.validate_all()
        summary = validator.get_summary()

        print(f"\n=== No LLM Configured ===")
        print(f"Warnings: {summary['warning_count']}")
        assert summary['warning_count'] > 0  # Should warn about no LLM

        # Test 2: With Ollama
        os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
        validator2 = ConfigValidator()
        validator2.validate_all()
        summary2 = validator2.get_summary()

        print(f"\n=== Ollama Configured ===")
        print(f"Info count should include Ollama enabled")

        # Test 3: With OpenAI
        del os.environ['OLLAMA_BASE_URL']
        os.environ['OPENAI_API_KEY'] = 'sk-test1234567890'
        validator3 = ConfigValidator()
        validator3.validate_all()

        print(f"\n=== OpenAI Configured ===")

        # Test 4: Multiple LLMs
        os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test1234567890'
        validator4 = ConfigValidator()
        validator4.validate_all()

        print(f"\n=== Multiple LLMs Configured ===")

    def test_database_configuration_validation(self, clean_env):
        """Test database configuration validation"""

        # Test 1: No database
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        validator.validate_all()
        summary = validator.get_summary()

        print(f"\n=== No Database Configured ===")
        print(f"Warnings: {summary['warning_count']}")
        assert summary['warning_count'] > 0

        # Test 2: With PostgreSQL
        os.environ['POSTGRES_URL'] = 'postgresql://user:pass@localhost/sigmax'
        validator2 = ConfigValidator()
        validator2.validate_all()

        print(f"\n=== PostgreSQL Configured ===")

        # Test 3: With Redis
        os.environ['REDIS_URL'] = 'redis://localhost:6379'
        validator3 = ConfigValidator()
        validator3.validate_all()

        print(f"\n=== Redis Also Configured ===")

    def test_exchange_configuration(self, clean_env):
        """Test exchange configuration validation"""

        valid_exchanges = ['binance', 'coinbase', 'kraken', 'bybit', 'okx']

        for exchange in valid_exchanges:
            os.environ.update({
                'TRADING_MODE': 'paper',
                'EXCHANGE': exchange,
                'TOTAL_CAPITAL': '10000',
                'MAX_DAILY_LOSS': '1000',
                'MAX_POSITION_SIZE': '2000',
                'STOP_LOSS_PCT': '5',
                'MAX_OPEN_TRADES': '5',
                'MAX_LEVERAGE': '2'
            })

            validator = ConfigValidator()
            result = validator.validate_all()

            print(f"\n=== Exchange: {exchange} ===")
            print(f"Valid: {result}")

            assert result == True  # Should all be valid

    def test_invalid_trading_mode(self, clean_env):
        """Test invalid trading mode"""
        os.environ.update({
            'TRADING_MODE': 'invalid_mode',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Invalid Trading Mode ===")
        print(f"Errors: {summary['error_count']}")

        assert summary['error_count'] > 0
        assert result == False

    def test_validation_summary_structure(self, clean_env):
        """Test that validation summary has correct structure"""
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '1000',
            'MAX_POSITION_SIZE': '2000',
            'STOP_LOSS_PCT': '5',
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '2'
        })

        validator = ConfigValidator()
        validator.validate_all()
        summary = validator.get_summary()

        print(f"\n=== Validation Summary Structure ===")
        print(f"Summary: {summary}")

        # Check summary structure
        assert 'error_count' in summary
        assert 'warning_count' in summary
        assert 'info_count' in summary
        assert 'errors' in summary
        assert 'warnings' in summary

        assert isinstance(summary['error_count'], int)
        assert isinstance(summary['warning_count'], int)
        assert isinstance(summary['info_count'], int)
        assert isinstance(summary['errors'], list)
        assert isinstance(summary['warnings'], list)

    def test_reasonable_defaults(self, clean_env):
        """Test system behavior with reasonable default values"""
        os.environ.update({
            'TRADING_MODE': 'paper',
            'TOTAL_CAPITAL': '10000',
            'MAX_DAILY_LOSS': '500',  # 5% of capital
            'MAX_POSITION_SIZE': '1000',  # 10% of capital
            'STOP_LOSS_PCT': '3',  # 3% stop loss
            'MAX_OPEN_TRADES': '5',
            'MAX_LEVERAGE': '1',  # No leverage
            'EXCHANGE': 'binance',
            'TESTNET': 'True'
        })

        validator = ConfigValidator()
        result = validator.validate_all()

        summary = validator.get_summary()
        print(f"\n=== Reasonable Defaults ===")
        print(f"Errors: {summary['error_count']}")
        print(f"Warnings: {summary['warning_count']}")
        print(f"Valid: {result}")

        # Should have minimal warnings with reasonable defaults
        assert summary['error_count'] == 0
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
