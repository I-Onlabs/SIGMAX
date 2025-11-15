"""
Secrets Manager - HashiCorp Vault Integration with Environment Variable Fallback

This module provides centralized secrets management for SIGMAX with support for:
- HashiCorp Vault (production)
- Environment variables (development/fallback)
- Secure credential retrieval
- Automatic fallback on Vault failures

Usage:
    from core.utils.secrets_manager import secrets_manager

    api_key = secrets_manager.get_secret("OPENAI_API_KEY")
    db_url = secrets_manager.get_database_url()
"""

import os
from typing import Optional, Dict, Any
from loguru import logger

# Optional Vault dependency
try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logger.warning("hvac not installed. Vault support disabled. Install with: pip install hvac")


class SecretsManager:
    """
    Centralized secrets management with HashiCorp Vault integration

    Features:
    - Automatic Vault connection with authentication
    - Graceful fallback to environment variables
    - Database URL construction with credentials
    - API key management for multiple services
    - Secure error handling (no credential logging)

    Configuration (via environment variables):
    - USE_VAULT: Enable Vault integration (default: false)
    - VAULT_ADDR: Vault server URL (default: http://localhost:8200)
    - VAULT_TOKEN: Vault authentication token (required if USE_VAULT=true)
    - VAULT_NAMESPACE: Vault namespace (optional)
    - VAULT_PATH_PREFIX: Secret path prefix (default: secret/data/sigmax)
    """

    def __init__(self):
        self.use_vault = os.getenv("USE_VAULT", "false").lower() == "true"
        self.client: Optional[Any] = None
        self.vault_available = VAULT_AVAILABLE
        self.vault_path_prefix = os.getenv("VAULT_PATH_PREFIX", "secret/data/sigmax")

        if self.use_vault:
            if not self.vault_available:
                logger.error("USE_VAULT=true but hvac not installed. Falling back to env vars.")
                logger.error("Install with: pip install hvac")
                self.use_vault = False
            else:
                self._initialize_vault()

    def _initialize_vault(self):
        """Initialize Vault client with authentication"""
        vault_url = os.getenv("VAULT_ADDR", "http://localhost:8200")
        vault_token = os.getenv("VAULT_TOKEN")
        vault_namespace = os.getenv("VAULT_NAMESPACE")

        if not vault_token:
            logger.warning("VAULT_TOKEN not set. Falling back to environment variables.")
            self.use_vault = False
            return

        try:
            # Initialize Vault client
            self.client = hvac.Client(
                url=vault_url,
                token=vault_token,
                namespace=vault_namespace
            )

            # Verify authentication
            if not self.client.is_authenticated():
                raise Exception("Vault authentication failed - invalid token")

            logger.info(f"✓ Connected to Vault at {vault_url}")
            if vault_namespace:
                logger.info(f"  Using namespace: {vault_namespace}")

        except Exception as e:
            logger.error(f"❌ Vault initialization failed: {e}")
            logger.warning("Falling back to environment variables")
            self.use_vault = False
            self.client = None

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from Vault or environment variable

        Args:
            key: Secret key name
            default: Default value if secret not found

        Returns:
            Secret value or default

        Example:
            api_key = secrets_manager.get_secret("OPENAI_API_KEY")
        """
        # Try Vault first if enabled
        if self.use_vault and self.client:
            try:
                secret_path = f"{self.vault_path_prefix}/{key}"
                response = self.client.secrets.kv.v2.read_secret_version(path=secret_path)
                value = response['data']['data']['value']
                logger.debug(f"Retrieved {key} from Vault")
                return value
            except Exception as e:
                logger.warning(f"Failed to read {key} from Vault: {e}. Trying env var.")

        # Fallback to environment variable
        value = os.getenv(key, default)
        if value:
            logger.debug(f"Retrieved {key} from environment variable")
        else:
            logger.warning(f"Secret {key} not found in Vault or environment")

        return value

    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a specific service

        Args:
            service: Service name (e.g., "OPENAI", "ANTHROPIC", "EXCHANGE")

        Returns:
            API key or None

        Example:
            openai_key = secrets_manager.get_api_key("OPENAI")
        """
        key_name = f"{service.upper()}_API_KEY"
        return self.get_secret(key_name)

    def get_api_secret(self, service: str) -> Optional[str]:
        """
        Get API secret for a specific service

        Args:
            service: Service name (e.g., "EXCHANGE")

        Returns:
            API secret or None

        Example:
            exchange_secret = secrets_manager.get_api_secret("EXCHANGE")
        """
        secret_name = f"{service.upper()}_API_SECRET"
        return self.get_secret(secret_name)

    def get_database_url(self, db_type: str = "POSTGRES") -> str:
        """
        Construct database URL with credentials

        Args:
            db_type: Database type ("POSTGRES", "REDIS", "CLICKHOUSE")

        Returns:
            Database connection URL

        Example:
            postgres_url = secrets_manager.get_database_url("POSTGRES")
        """
        db_type = db_type.upper()

        # Check for full URL first
        url_key = f"{db_type}_URL"
        full_url = self.get_secret(url_key)
        if full_url:
            return full_url

        # Construct from components
        if db_type == "POSTGRES":
            user = self.get_secret("POSTGRES_USER", "sigmax")
            password = self.get_secret("POSTGRES_PASSWORD", "")
            host = self.get_secret("POSTGRES_HOST", "localhost")
            port = self.get_secret("POSTGRES_PORT", "5432")
            db = self.get_secret("POSTGRES_DB", "sigmax")

            if password:
                return f"postgresql://{user}:{password}@{host}:{port}/{db}"
            else:
                logger.warning("POSTGRES_PASSWORD not set - using passwordless connection")
                return f"postgresql://{user}@{host}:{port}/{db}"

        elif db_type == "REDIS":
            password = self.get_secret("REDIS_PASSWORD", "")
            host = self.get_secret("REDIS_HOST", "localhost")
            port = self.get_secret("REDIS_PORT", "6379")
            db = self.get_secret("REDIS_DB", "0")

            if password:
                return f"redis://:{password}@{host}:{port}/{db}"
            else:
                return f"redis://{host}:{port}/{db}"

        elif db_type == "CLICKHOUSE":
            user = self.get_secret("CLICKHOUSE_USER", "default")
            password = self.get_secret("CLICKHOUSE_PASSWORD", "")
            host = self.get_secret("CLICKHOUSE_HOST", "localhost")
            port = self.get_secret("CLICKHOUSE_PORT", "8123")
            db = self.get_secret("CLICKHOUSE_DB", "default")

            if password:
                return f"clickhouse://{user}:{password}@{host}:{port}/{db}"
            else:
                return f"clickhouse://{user}@{host}:{port}/{db}"

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def get_telegram_config(self) -> Dict[str, Optional[str]]:
        """
        Get Telegram bot configuration

        Returns:
            Dictionary with bot_token and chat_id
        """
        return {
            "bot_token": self.get_secret("TELEGRAM_BOT_TOKEN"),
            "chat_id": self.get_secret("TELEGRAM_CHAT_ID")
        }

    def get_exchange_credentials(self, exchange: str) -> Dict[str, Optional[str]]:
        """
        Get exchange API credentials

        Args:
            exchange: Exchange name (e.g., "BINANCE", "COINBASE")

        Returns:
            Dictionary with api_key and api_secret
        """
        exchange = exchange.upper()
        return {
            "api_key": self.get_secret(f"{exchange}_API_KEY"),
            "api_secret": self.get_secret(f"{exchange}_API_SECRET")
        }

    def set_secret(self, key: str, value: str) -> bool:
        """
        Store secret in Vault (Vault only, not env vars)

        Args:
            key: Secret key name
            value: Secret value

        Returns:
            True if successful, False otherwise
        """
        if not self.use_vault or not self.client:
            logger.error("Cannot set secret: Vault not enabled or not available")
            return False

        try:
            secret_path = f"{self.vault_path_prefix}/{key}"
            self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={"value": value}
            )
            logger.info(f"✓ Secret {key} stored in Vault")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store {key} in Vault: {e}")
            return False

    def list_secrets(self) -> list:
        """
        List all secrets in Vault (Vault only)

        Returns:
            List of secret keys
        """
        if not self.use_vault or not self.client:
            logger.error("Cannot list secrets: Vault not enabled or not available")
            return []

        try:
            response = self.client.secrets.kv.v2.list_secrets(path=self.vault_path_prefix)
            return response['data']['keys']
        except Exception as e:
            logger.error(f"❌ Failed to list secrets: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Check secrets manager health

        Returns:
            Health status dictionary
        """
        health = {
            "vault_enabled": self.use_vault,
            "vault_available": self.vault_available,
            "vault_connected": False,
            "vault_authenticated": False,
            "fallback_mode": "environment_variables"
        }

        if self.use_vault and self.client:
            try:
                health["vault_connected"] = True
                health["vault_authenticated"] = self.client.is_authenticated()
                health["fallback_mode"] = "vault_primary"
            except Exception as e:
                logger.warning(f"Vault health check failed: {e}")

        return health


# Global singleton instance
secrets_manager = SecretsManager()


# Convenience functions
def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get secret"""
    return secrets_manager.get_secret(key, default)


def get_api_key(service: str) -> Optional[str]:
    """Convenience function to get API key"""
    return secrets_manager.get_api_key(service)


def get_database_url(db_type: str = "POSTGRES") -> str:
    """Convenience function to get database URL"""
    return secrets_manager.get_database_url(db_type)


if __name__ == "__main__":
    # Self-test
    import sys

    print("🔒 SIGMAX Secrets Manager Self-Test\n")

    # Health check
    health = secrets_manager.health_check()
    print("Health Status:")
    for key, value in health.items():
        print(f"  {key}: {value}")

    print("\nTesting secret retrieval:")

    # Test environment variable retrieval
    test_val = secrets_manager.get_secret("PATH", "not_found")
    print(f"  PATH (should exist): {'✓' if test_val != 'not_found' else '✗'}")

    # Test missing secret
    test_val = secrets_manager.get_secret("NONEXISTENT_SECRET_12345", "default_value")
    print(f"  Missing secret (should return default): {'✓' if test_val == 'default_value' else '✗'}")

    # Test database URL construction
    try:
        db_url = secrets_manager.get_database_url("POSTGRES")
        print(f"  Database URL construction: ✓")
        print(f"    URL: {db_url}")
    except Exception as e:
        print(f"  Database URL construction: ✗ ({e})")

    print("\n✅ Self-test complete!")
