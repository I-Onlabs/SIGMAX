"""
Exchange API Management - Secure storage and management of exchange credentials
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from cryptography.fernet import Fernet
from loguru import logger


class ExchangeType(Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    HYPERLIQUID = "hyperliquid"
    ALPACA = "alpaca"
    OKX = "okx"


class NetworkType(Enum):
    """Network types"""
    TESTNET = "testnet"
    MAINNET = "mainnet"


@dataclass
class ExchangeCredential:
    """Exchange credential model"""
    id: str
    exchange: str
    name: str  # User-friendly name (e.g., "Binance Main")
    api_key: str  # Encrypted
    api_secret: str  # Encrypted
    passphrase: Optional[str] = None  # For exchanges that require it (encrypted)
    network: str = NetworkType.MAINNET.value
    enabled: bool = False
    testnet: bool = False
    created_at: str = None
    updated_at: str = None
    last_connected: Optional[str] = None
    connection_status: str = "unknown"  # unknown, connected, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class ExchangeCredentialManager:
    """
    Manages exchange API credentials with encryption

    Features:
    - Secure encryption of API keys using Fernet (AES-128)
    - Multiple exchange support
    - Testnet/mainnet configuration
    - Connection status tracking
    - Enable/disable functionality
    """

    def __init__(self, storage_path: str = "./data/exchanges.json"):
        """
        Initialize credential manager

        Args:
            storage_path: Path to store encrypted credentials
        """
        self.storage_path = storage_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.credentials: Dict[str, ExchangeCredential] = {}

        # Ensure storage directory exists
        os.makedirs(os.path.dirname(storage_path) or ".", exist_ok=True)

        # Load existing credentials
        self._load_credentials()

        logger.info(f"✓ Exchange credential manager initialized ({len(self.credentials)} exchanges)")

    def _get_or_create_encryption_key(self) -> bytes:
        """
        Get or create encryption key for API credentials

        Key is stored in .env file or generated if not exists
        """
        key_env = os.getenv("EXCHANGE_ENCRYPTION_KEY")

        if key_env:
            return key_env.encode()

        # Generate new key
        key = Fernet.generate_key()

        # Save to .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, "a") as f:
                f.write(f"\n\n# Exchange API Encryption Key (auto-generated)\n")
                f.write(f"EXCHANGE_ENCRYPTION_KEY={key.decode()}\n")
            logger.info("Generated new encryption key and saved to .env")
        else:
            logger.warning(
                "No .env file found. Encryption key is temporary. "
                "Create .env and add EXCHANGE_ENCRYPTION_KEY to persist."
            )

        return key

    def _encrypt(self, value: str) -> str:
        """Encrypt a value"""
        if not value:
            return ""
        return self.cipher.encrypt(value.encode()).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        if not encrypted_value:
            return ""
        try:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""

    def add_credential(
        self,
        exchange: str,
        name: str,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        testnet: bool = False,
        enabled: bool = True
    ) -> ExchangeCredential:
        """
        Add new exchange credential

        Args:
            exchange: Exchange type (binance, coinbase, etc.)
            name: User-friendly name
            api_key: API key (will be encrypted)
            api_secret: API secret (will be encrypted)
            passphrase: Optional passphrase (will be encrypted)
            testnet: Use testnet
            enabled: Enable this exchange

        Returns:
            Created credential
        """
        import uuid

        # Validate exchange
        try:
            ExchangeType(exchange.lower())
        except ValueError:
            raise ValueError(f"Unsupported exchange: {exchange}")

        # Create credential
        credential = ExchangeCredential(
            id=str(uuid.uuid4()),
            exchange=exchange.lower(),
            name=name,
            api_key=self._encrypt(api_key),
            api_secret=self._encrypt(api_secret),
            passphrase=self._encrypt(passphrase) if passphrase else None,
            network=NetworkType.TESTNET.value if testnet else NetworkType.MAINNET.value,
            enabled=enabled,
            testnet=testnet,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        # Store
        self.credentials[credential.id] = credential
        self._save_credentials()

        logger.info(f"Added exchange credential: {name} ({exchange})")
        return credential

    def update_credential(
        self,
        credential_id: str,
        **updates
    ) -> Optional[ExchangeCredential]:
        """
        Update exchange credential

        Args:
            credential_id: Credential ID
            **updates: Fields to update

        Returns:
            Updated credential or None
        """
        if credential_id not in self.credentials:
            logger.warning(f"Credential not found: {credential_id}")
            return None

        credential = self.credentials[credential_id]

        # Update fields
        if "name" in updates:
            credential.name = updates["name"]
        if "api_key" in updates:
            credential.api_key = self._encrypt(updates["api_key"])
        if "api_secret" in updates:
            credential.api_secret = self._encrypt(updates["api_secret"])
        if "passphrase" in updates:
            credential.passphrase = self._encrypt(updates["passphrase"]) if updates["passphrase"] else None
        if "testnet" in updates:
            credential.testnet = updates["testnet"]
            credential.network = NetworkType.TESTNET.value if updates["testnet"] else NetworkType.MAINNET.value
        if "enabled" in updates:
            credential.enabled = updates["enabled"]

        credential.updated_at = datetime.now().isoformat()

        self._save_credentials()
        logger.info(f"Updated credential: {credential.name}")

        return credential

    def delete_credential(self, credential_id: str) -> bool:
        """
        Delete exchange credential

        Args:
            credential_id: Credential ID

        Returns:
            True if deleted, False if not found
        """
        if credential_id not in self.credentials:
            return False

        credential = self.credentials.pop(credential_id)
        self._save_credentials()

        logger.info(f"Deleted credential: {credential.name}")
        return True

    def get_credential(self, credential_id: str) -> Optional[ExchangeCredential]:
        """Get credential by ID"""
        return self.credentials.get(credential_id)

    def get_all_credentials(self, decrypted: bool = False) -> List[Dict[str, Any]]:
        """
        Get all credentials

        Args:
            decrypted: Return decrypted credentials (use with caution)

        Returns:
            List of credential dictionaries
        """
        credentials = []

        for cred in self.credentials.values():
            cred_dict = cred.to_dict()

            if decrypted:
                cred_dict["api_key"] = self._decrypt(cred.api_key)
                cred_dict["api_secret"] = self._decrypt(cred.api_secret)
                if cred.passphrase:
                    cred_dict["passphrase"] = self._decrypt(cred.passphrase)
            else:
                # Mask credentials for display
                cred_dict["api_key"] = self._mask_key(self._decrypt(cred.api_key))
                cred_dict["api_secret"] = "***********"
                cred_dict["passphrase"] = "***********" if cred.passphrase else None

            credentials.append(cred_dict)

        return credentials

    def get_enabled_credentials(self) -> List[ExchangeCredential]:
        """Get all enabled credentials"""
        return [cred for cred in self.credentials.values() if cred.enabled]

    def _mask_key(self, key: str, visible_chars: int = 4) -> str:
        """Mask API key for display"""
        if not key or len(key) <= visible_chars:
            return "****"
        return f"{key[:visible_chars]}...{key[-visible_chars:]}"

    def _load_credentials(self):
        """Load credentials from storage"""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            for cred_data in data:
                cred = ExchangeCredential(**cred_data)
                self.credentials[cred.id] = cred

            logger.info(f"Loaded {len(self.credentials)} exchange credentials")

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")

    def _save_credentials(self):
        """Save credentials to storage"""
        try:
            data = [cred.to_dict() for cred in self.credentials.values()]

            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.credentials)} credentials")

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def test_connection(self, credential_id: str) -> Dict[str, Any]:
        """
        Test exchange connection

        Args:
            credential_id: Credential ID to test

        Returns:
            Connection test result
        """
        credential = self.get_credential(credential_id)
        if not credential:
            return {
                "success": False,
                "error": "Credential not found"
            }

        try:
            import ccxt

            # Get decrypted credentials
            api_key = self._decrypt(credential.api_key)
            api_secret = self._decrypt(credential.api_secret)

            # Initialize exchange
            exchange_class = getattr(ccxt, credential.exchange)
            exchange = exchange_class({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True
            })

            # Set testnet if enabled
            if credential.testnet:
                if hasattr(exchange, 'set_sandbox_mode'):
                    exchange.set_sandbox_mode(True)

            # Test connection by fetching balance
            balance = exchange.fetch_balance()

            # Update connection status
            credential.connection_status = "connected"
            credential.last_connected = datetime.now().isoformat()
            self._save_credentials()

            return {
                "success": True,
                "message": f"Connected to {credential.exchange.upper()}",
                "balance": balance.get("total", {}),
                "network": credential.network
            }

        except Exception as e:
            # Update connection status
            credential.connection_status = "failed"
            self._save_credentials()

            logger.error(f"Connection test failed for {credential.name}: {e}")

            return {
                "success": False,
                "error": str(e)
            }
