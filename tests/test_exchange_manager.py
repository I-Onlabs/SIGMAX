"""
Tests for Exchange Credential Manager
"""

import pytest
import os
import json
import tempfile
from datetime import datetime
from cryptography.fernet import Fernet
from core.utils.exchange_manager import (
    ExchangeCredentialManager,
    ExchangeType,
    NetworkType
)


class TestExchangeCredentialManager:
    """Test suite for exchange credential management"""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def manager(self, temp_storage):
        """Create credential manager with temp storage"""
        return ExchangeCredentialManager(storage_path=temp_storage)

    def test_manager_initialization(self, manager):
        """Test credential manager initializes"""
        assert manager is not None
        assert manager.encryption_key is not None
        assert len(manager.credentials) == 0

    def test_add_credential(self, manager):
        """Test adding exchange credentials"""
        credential = manager.add_credential(
            exchange="binance",
            name="Binance Main",
            api_key="test_api_key_123",
            api_secret="test_secret_456",
            testnet=False,
            enabled=True
        )

        assert credential is not None
        assert credential.exchange == "binance"
        assert credential.name == "Binance Main"
        assert credential.enabled is True
        assert credential.testnet is False
        assert credential.network == NetworkType.MAINNET.value

        # Verify encryption
        assert credential.api_key != "test_api_key_123"  # Should be encrypted
        assert credential.api_secret != "test_secret_456"

    def test_add_credential_with_passphrase(self, manager):
        """Test adding credentials with passphrase"""
        credential = manager.add_credential(
            exchange="coinbase",
            name="Coinbase Pro",
            api_key="coinbase_key",
            api_secret="coinbase_secret",
            passphrase="test_passphrase",
            testnet=True
        )

        assert credential.passphrase is not None
        assert credential.passphrase != "test_passphrase"  # Should be encrypted
        assert credential.testnet is True

    def test_add_invalid_exchange(self, manager):
        """Test adding invalid exchange raises error"""
        with pytest.raises(ValueError, match="Unsupported exchange"):
            manager.add_credential(
                exchange="invalid_exchange",
                name="Invalid",
                api_key="key",
                api_secret="secret"
            )

    def test_get_credential(self, manager):
        """Test retrieving credential by ID"""
        added = manager.add_credential(
            exchange="kraken",
            name="Kraken Main",
            api_key="kraken_key",
            api_secret="kraken_secret"
        )

        retrieved = manager.get_credential(added.id)

        assert retrieved is not None
        assert retrieved.id == added.id
        assert retrieved.name == "Kraken Main"

    def test_get_nonexistent_credential(self, manager):
        """Test getting non-existent credential returns None"""
        result = manager.get_credential("nonexistent_id")
        assert result is None

    def test_update_credential(self, manager):
        """Test updating exchange credentials"""
        credential = manager.add_credential(
            exchange="bybit",
            name="Bybit Test",
            api_key="old_key",
            api_secret="old_secret",
            enabled=False
        )

        # Update
        updated = manager.update_credential(
            credential.id,
            name="Bybit Production",
            enabled=True
        )

        assert updated is not None
        assert updated.name == "Bybit Production"
        assert updated.enabled is True

    def test_update_credentials_keys(self, manager):
        """Test updating API keys"""
        credential = manager.add_credential(
            exchange="binance",
            name="Test",
            api_key="old_key",
            api_secret="old_secret"
        )

        old_key = credential.api_key

        # Update keys
        updated = manager.update_credential(
            credential.id,
            api_key="new_key_123",
            api_secret="new_secret_456"
        )

        assert updated.api_key != old_key  # Should be different encrypted value
        # Verify encryption
        decrypted_key = manager._decrypt(updated.api_key)
        assert decrypted_key == "new_key_123"

    def test_delete_credential(self, manager):
        """Test deleting credential"""
        credential = manager.add_credential(
            exchange="alpaca",
            name="Alpaca",
            api_key="key",
            api_secret="secret"
        )

        # Delete
        success = manager.delete_credential(credential.id)
        assert success is True

        # Verify deleted
        assert manager.get_credential(credential.id) is None

    def test_delete_nonexistent_credential(self, manager):
        """Test deleting non-existent credential returns False"""
        success = manager.delete_credential("nonexistent_id")
        assert success is False

    def test_get_all_credentials_masked(self, manager):
        """Test getting all credentials with masked keys"""
        manager.add_credential(
            exchange="binance",
            name="Binance",
            api_key="binance_key_12345678",
            api_secret="binance_secret"
        )
        manager.add_credential(
            exchange="coinbase",
            name="Coinbase",
            api_key="coinbase_key_87654321",
            api_secret="coinbase_secret"
        )

        credentials = manager.get_all_credentials(decrypted=False)

        assert len(credentials) == 2
        assert credentials[0]["api_secret"] == "***********"
        assert "..." in credentials[0]["api_key"]  # Should be masked
        assert "..." in credentials[1]["api_key"]

    def test_get_all_credentials_decrypted(self, manager):
        """Test getting all credentials decrypted"""
        manager.add_credential(
            exchange="binance",
            name="Binance",
            api_key="actual_key_123",
            api_secret="actual_secret_456"
        )

        credentials = manager.get_all_credentials(decrypted=True)

        assert len(credentials) == 1
        assert credentials[0]["api_key"] == "actual_key_123"
        assert credentials[0]["api_secret"] == "actual_secret_456"

    def test_get_enabled_credentials(self, manager):
        """Test getting only enabled credentials"""
        manager.add_credential(
            exchange="binance",
            name="Binance",
            api_key="key1",
            api_secret="secret1",
            enabled=True
        )
        manager.add_credential(
            exchange="coinbase",
            name="Coinbase",
            api_key="key2",
            api_secret="secret2",
            enabled=False
        )
        manager.add_credential(
            exchange="kraken",
            name="Kraken",
            api_key="key3",
            api_secret="secret3",
            enabled=True
        )

        enabled = manager.get_enabled_credentials()

        assert len(enabled) == 2
        assert all(c.enabled for c in enabled)

    def test_persistence(self, temp_storage):
        """Test credentials are persisted to disk"""
        # Set consistent encryption key for both instances
        import os
        os.environ["EXCHANGE_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

        manager1 = ExchangeCredentialManager(storage_path=temp_storage)

        manager1.add_credential(
            exchange="binance",
            name="Test Exchange",
            api_key="test_key",
            api_secret="test_secret"
        )

        # Create new manager instance (should load from disk with same key)
        manager2 = ExchangeCredentialManager(storage_path=temp_storage)

        assert len(manager2.credentials) == 1
        credentials = manager2.get_all_credentials(decrypted=True)
        assert credentials[0]["name"] == "Test Exchange"
        assert credentials[0]["api_key"] == "test_key"

        # Cleanup
        del os.environ["EXCHANGE_ENCRYPTION_KEY"]

    def test_encryption_decryption(self, manager):
        """Test encryption and decryption work correctly"""
        original = "sensitive_api_key_12345"

        encrypted = manager._encrypt(original)
        assert encrypted != original

        decrypted = manager._decrypt(encrypted)
        assert decrypted == original

    def test_key_masking(self, manager):
        """Test API key masking"""
        key = "abcdefghijklmnopqrstuvwxyz123456"

        masked = manager._mask_key(key, visible_chars=4)

        assert masked.startswith("abcd")
        assert masked.endswith("3456")
        assert "..." in masked
        assert len(masked) < len(key)

    def test_short_key_masking(self, manager):
        """Test masking short keys"""
        key = "abc"
        masked = manager._mask_key(key)
        assert masked == "****"

    def test_testnet_configuration(self, manager):
        """Test testnet configuration is saved correctly"""
        testnet_cred = manager.add_credential(
            exchange="binance",
            name="Binance Testnet",
            api_key="key",
            api_secret="secret",
            testnet=True
        )

        mainnet_cred = manager.add_credential(
            exchange="binance",
            name="Binance Mainnet",
            api_key="key",
            api_secret="secret",
            testnet=False
        )

        assert testnet_cred.testnet is True
        assert testnet_cred.network == NetworkType.TESTNET.value

        assert mainnet_cred.testnet is False
        assert mainnet_cred.network == NetworkType.MAINNET.value

    def test_connection_status_tracking(self, manager):
        """Test connection status is tracked"""
        credential = manager.add_credential(
            exchange="binance",
            name="Test",
            api_key="key",
            api_secret="secret"
        )

        assert credential.connection_status == "unknown"
        assert credential.last_connected is None

        # Update connection status
        credential.connection_status = "connected"
        credential.last_connected = datetime.now().isoformat()

        manager._save_credentials()

        # Reload and verify
        retrieved = manager.get_credential(credential.id)
        assert retrieved.connection_status == "connected"
        assert retrieved.last_connected is not None

    def test_multiple_same_exchange(self, manager):
        """Test can add multiple credentials for same exchange"""
        manager.add_credential(
            exchange="binance",
            name="Binance Account 1",
            api_key="key1",
            api_secret="secret1"
        )
        manager.add_credential(
            exchange="binance",
            name="Binance Account 2",
            api_key="key2",
            api_secret="secret2"
        )

        credentials = manager.get_all_credentials(decrypted=True)
        assert len(credentials) == 2

        binance_creds = [c for c in credentials if c["exchange"] == "binance"]
        assert len(binance_creds) == 2
        assert {c["name"] for c in binance_creds} == {"Binance Account 1", "Binance Account 2"}
