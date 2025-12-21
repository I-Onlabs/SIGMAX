"""
Tests for Federated Learning Module

Tests Flower integration for distributed model training.
"""

import pytest
import numpy as np

from core.modules.federated_learning import (
    FederatedConfig,
    TradingModelClient,
    FederatedLearningManager,
    create_fl_manager,
    create_fl_config,
    FLWR_AVAILABLE,
    TORCH_AVAILABLE
)


class TestFederatedConfig:
    """Test federated learning configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = FederatedConfig()

        assert config.server_address == "0.0.0.0:8080"
        assert config.num_rounds == 10
        assert config.min_fit_clients == 2
        assert config.min_available_clients == 2
        assert config.local_epochs == 5
        assert config.batch_size == 32
        assert config.learning_rate == 0.001

    def test_custom_config(self):
        """Test custom configuration"""
        config = FederatedConfig(
            server_address="localhost:9090",
            num_rounds=20,
            local_epochs=10,
            learning_rate=0.01
        )

        assert config.server_address == "localhost:9090"
        assert config.num_rounds == 20
        assert config.local_epochs == 10
        assert config.learning_rate == 0.01

    def test_config_to_dict(self):
        """Test configuration serialization"""
        config = FederatedConfig(client_id="client_1")
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["client_id"] == "client_1"
        assert "server_address" in config_dict
        assert "num_rounds" in config_dict


class TestTradingModelClient:
    """Test federated learning client"""

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_client_initialization(self):
        """Test client initialization"""
        import torch
        import torch.nn as nn

        # Create simple model
        model = nn.Sequential(
            nn.Linear(10, 5),
            nn.ReLU(),
            nn.Linear(5, 1)
        )

        # Create mock data loaders
        train_loader = [
            (torch.randn(16, 10), torch.randn(16, 1))
            for _ in range(5)
        ]
        val_loader = [
            (torch.randn(16, 10), torch.randn(16, 1))
            for _ in range(2)
        ]

        config = FederatedConfig(local_epochs=2)
        client = TradingModelClient(model, train_loader, val_loader, config)

        assert client.model is not None
        assert client.config == config

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_get_parameters(self):
        """Test getting model parameters"""
        import torch.nn as nn

        model = nn.Linear(10, 1)
        train_loader = []
        val_loader = []

        client = TradingModelClient(model, train_loader, val_loader, FederatedConfig())
        parameters = client.get_parameters(config={})

        assert isinstance(parameters, list)
        assert len(parameters) > 0
        assert all(isinstance(p, np.ndarray) for p in parameters)

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_set_parameters(self):
        """Test setting model parameters"""
        import torch.nn as nn

        model = nn.Linear(10, 1)
        train_loader = []
        val_loader = []

        client = TradingModelClient(model, train_loader, val_loader, FederatedConfig())

        # Get initial parameters
        initial_params = client.get_parameters(config={})

        # Modify parameters
        modified_params = [p * 2 for p in initial_params]

        # Set modified parameters
        client.set_parameters(modified_params)

        # Get parameters again
        new_params = client.get_parameters(config={})

        # Check that parameters were updated
        assert not np.allclose(initial_params[0], new_params[0])

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_fit(self):
        """Test model training"""
        import torch
        import torch.nn as nn

        model = nn.Linear(10, 1)

        # Create synthetic data
        train_loader = [
            (torch.randn(16, 10), torch.randn(16, 1))
            for _ in range(5)
        ]
        val_loader = []

        config = FederatedConfig(local_epochs=2)
        client = TradingModelClient(model, train_loader, val_loader, config)

        # Get initial parameters
        initial_params = client.get_parameters(config={})

        # Train
        updated_params, num_examples, metrics = client.fit(initial_params, config={})

        assert isinstance(updated_params, list)
        assert num_examples > 0
        assert "train_loss" in metrics
        assert isinstance(metrics["train_loss"], float)

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_evaluate(self):
        """Test model evaluation"""
        import torch
        import torch.nn as nn

        model = nn.Linear(10, 1)
        train_loader = []

        # Create validation data
        val_loader = [
            (torch.randn(16, 10), torch.randn(16, 1))
            for _ in range(3)
        ]

        client = TradingModelClient(model, train_loader, val_loader, FederatedConfig())

        # Get parameters
        parameters = client.get_parameters(config={})

        # Evaluate
        loss, num_examples, metrics = client.evaluate(parameters, config={})

        assert isinstance(loss, float)
        assert num_examples > 0
        assert "val_loss" in metrics


class TestFederatedLearningManager:
    """Test federated learning manager"""

    def test_manager_initialization(self):
        """Test manager initialization"""
        manager = FederatedLearningManager()

        assert manager.config is not None
        assert manager.server_running is False
        assert manager.client_running is False

    def test_manager_with_custom_config(self):
        """Test manager with custom configuration"""
        config = FederatedConfig(num_rounds=20)
        manager = FederatedLearningManager(config)

        assert manager.config.num_rounds == 20

    @pytest.mark.skipif(not FLWR_AVAILABLE, reason="Flower not available")
    def test_create_strategy(self):
        """Test strategy creation"""
        manager = FederatedLearningManager()
        strategy = manager.create_strategy()

        assert strategy is not None

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_start_client(self):
        """Test starting client"""
        import torch
        import torch.nn as nn

        manager = FederatedLearningManager()

        model = nn.Linear(10, 1)
        train_loader = [(torch.randn(16, 10), torch.randn(16, 1))]
        val_loader = [(torch.randn(16, 10), torch.randn(16, 1))]

        client = manager.start_client(model, train_loader, val_loader)

        assert client is not None
        assert isinstance(client, TradingModelClient)
        assert manager.client_running is True

    def test_stop(self):
        """Test stopping federated learning"""
        manager = FederatedLearningManager()
        manager.server_running = True
        manager.client_running = True

        manager.stop()

        assert manager.server_running is False
        assert manager.client_running is False


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_fl_manager(self):
        """Test creating FL manager"""
        manager = create_fl_manager()

        assert isinstance(manager, FederatedLearningManager)

    def test_create_fl_manager_with_config(self):
        """Test creating FL manager with config"""
        config = FederatedConfig(num_rounds=15)
        manager = create_fl_manager(config)

        assert manager.config.num_rounds == 15

    def test_create_fl_config(self):
        """Test creating FL config"""
        config = create_fl_config(
            server_address="localhost:8080",
            num_rounds=25
        )

        assert isinstance(config, FederatedConfig)
        assert config.server_address == "localhost:8080"
        assert config.num_rounds == 25


class TestIntegration:
    """Test integration scenarios"""

    @pytest.mark.skipif(
        not (FLWR_AVAILABLE and TORCH_AVAILABLE),
        reason="Flower or PyTorch not available"
    )
    def test_full_training_workflow(self):
        """Test complete federated learning workflow"""
        import torch
        import torch.nn as nn

        # Create model
        model = nn.Sequential(
            nn.Linear(10, 5),
            nn.ReLU(),
            nn.Linear(5, 1)
        )

        # Create synthetic data
        train_loader = [
            (torch.randn(16, 10), torch.randn(16, 1))
            for _ in range(5)
        ]
        val_loader = [
            (torch.randn(16, 10), torch.randn(16, 1))
            for _ in range(2)
        ]

        # Create manager and client
        config = FederatedConfig(local_epochs=2)
        manager = create_fl_manager(config)

        client = manager.start_client(model, train_loader, val_loader)

        assert client is not None

        # Get initial parameters
        initial_params = client.get_parameters(config={})

        # Simulate federated round: fit
        updated_params, num_examples, fit_metrics = client.fit(
            initial_params,
            config={}
        )

        assert num_examples > 0
        assert "train_loss" in fit_metrics

        # Simulate federated round: evaluate
        loss, num_val, eval_metrics = client.evaluate(
            updated_params,
            config={}
        )

        assert num_val > 0
        assert "val_loss" in eval_metrics

        # Cleanup
        manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
