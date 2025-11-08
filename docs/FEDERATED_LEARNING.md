# Federated Learning Integration - Flower

## Overview

SIGMAX integrates with **Flower (flwr)**, a friendly federated learning framework, to enable privacy-preserving distributed model training across multiple trading instances without sharing raw data.

## Why Federated Learning?

Traditional centralized learning requires:
- ❌ Sharing sensitive trading data
- ❌ Centralizing data from multiple markets
- ❌ Exposing proprietary strategies

Federated Learning enables:
- ✅ **Privacy-Preserving**: Train models without sharing data
- ✅ **Distributed**: Learn from multiple SIGMAX instances
- ✅ **Collaborative**: Aggregate knowledge across markets
- ✅ **Secure**: Model updates only, no raw data transfer

## Architecture

```
Federated Learning System
├── Server (Aggregator)
│   ├── FedAvg Strategy
│   ├── Model Aggregation
│   └── Coordination
│
├── Client 1 (SIGMAX Instance A)
│   ├── Local Model
│   ├── Local Training Data
│   └── Model Updates
│
├── Client 2 (SIGMAX Instance B)
│   ├── Local Model
│   ├── Local Training Data
│   └── Model Updates
│
└── Client N (SIGMAX Instance N)
    ├── Local Model
    ├── Local Training Data
    └── Model Updates
```

## Installation

```bash
pip install flwr
```

Flower is installed with SIGMAX dependencies and supports Python 3.9+.

## Use Cases

### 1. Multi-Market Learning
Train models across different cryptocurrency exchanges without sharing data:
- **Instance A**: Learns from Binance data
- **Instance B**: Learns from Coinbase data
- **Global Model**: Benefits from both markets

### 2. Multi-Strategy Collaboration
Different trading strategies learn collaboratively:
- Each instance maintains its own strategy
- Models improve from collective experience
- No strategy details are shared

### 3. Privacy-Preserving Optimization
- Train risk models across multiple portfolios
- Learn from multiple time zones
- Maintain data sovereignty

## Configuration

```python
from core.modules.federated_learning import FederatedConfig

config = FederatedConfig(
    # Server configuration
    server_address="0.0.0.0:8080",
    num_rounds=10,
    min_fit_clients=2,
    min_available_clients=2,

    # Client configuration
    client_id="sigmax_instance_1",

    # Training configuration
    local_epochs=5,
    batch_size=32,
    learning_rate=0.001,

    # Strategy configuration
    fraction_fit=1.0,  # Use all clients for training
    fraction_evaluate=1.0  # Use all clients for evaluation
)
```

## Usage

### Start Server

```python
from core.modules.federated_learning import create_fl_manager, FederatedConfig
import torch.nn as nn

# Create model
class TradingModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(50, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.fc3(x)

# Configure
config = FederatedConfig(
    server_address="0.0.0.0:8080",
    num_rounds=20,
    min_fit_clients=3
)

# Create manager
manager = create_fl_manager(config)

# Start server
model = TradingModel()
await manager.start_server(initial_model=model)
```

### Start Client

```python
from core.modules.federated_learning import create_fl_manager, FederatedConfig
from torch.utils.data import DataLoader

# Load local data
train_dataset = load_local_trading_data()
val_dataset = load_validation_data()

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32)

# Configure client
config = FederatedConfig(
    server_address="server_ip:8080",
    client_id="sigmax_binance_1",
    local_epochs=5
)

# Create manager and client
manager = create_fl_manager(config)
model = TradingModel()

client = manager.start_client(
    model=model,
    train_loader=train_loader,
    val_loader=val_loader
)

# Client automatically participates in federated rounds
```

## Federated Training Process

### Round 1-N:

1. **Server** → **Clients**: Send global model
2. **Clients**: Train on local data (5 epochs)
3. **Clients** → **Server**: Send model updates
4. **Server**: Aggregate updates (FedAvg)
5. **Server**: Update global model
6. Repeat

### After N Rounds:

- Global model benefits from all clients
- No raw data was shared
- Each client retains privacy

## FedAvg Strategy

Federated Averaging aggregates client models:

```
Global Model = Σ (n_k / n_total) × Client_Model_k
```

Where:
- `n_k` = number of training examples on client k
- `n_total` = total training examples across all clients

## Example: Multi-Instance Training

### Instance 1 (Binance)

```python
# Train on Binance data
config = FederatedConfig(
    server_address="central_server:8080",
    client_id="binance_1",
    local_epochs=5
)

manager = create_fl_manager(config)
client = manager.start_client(
    model=trading_model,
    train_loader=binance_data_loader,
    val_loader=binance_val_loader
)
```

### Instance 2 (Coinbase)

```python
# Train on Coinbase data
config = FederatedConfig(
    server_address="central_server:8080",
    client_id="coinbase_1",
    local_epochs=5
)

manager = create_fl_manager(config)
client = manager.start_client(
    model=trading_model,
    train_loader=coinbase_data_loader,
    val_loader=coinbase_val_loader
)
```

### Server

```python
# Aggregate from both instances
config = FederatedConfig(
    server_address="0.0.0.0:8080",
    num_rounds=20,
    min_fit_clients=2  # Wait for both instances
)

manager = create_fl_manager(config)
await manager.start_server(initial_model=trading_model)
```

## Metrics & Monitoring

Track federated learning progress:

```python
# During training
client.fit(parameters, config={})
# Returns: (updated_params, num_examples, {"train_loss": 0.045})

# During evaluation
client.evaluate(parameters, config={})
# Returns: (loss, num_examples, {"val_loss": 0.052})
```

## Security Considerations

### What is Shared:
- ✅ Model architecture
- ✅ Model parameter updates
- ✅ Aggregated metrics

### What is NOT Shared:
- ❌ Raw trading data
- ❌ Order history
- ❌ Customer information
- ❌ Proprietary signals

### Additional Security:
- Use secure communication (TLS)
- Implement differential privacy
- Add secure aggregation
- Validate model updates

## Production Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  fl-server:
    build: .
    command: python -m scripts.fl_server
    ports:
      - "8080:8080"
    environment:
      - FL_NUM_ROUNDS=20
      - FL_MIN_CLIENTS=3

  fl-client-1:
    build: .
    command: python -m scripts.fl_client
    environment:
      - FL_SERVER=fl-server:8080
      - FL_CLIENT_ID=client_1
      - DATA_SOURCE=binance

  fl-client-2:
    build: .
    command: python -m scripts.fl_client
    environment:
      - FL_SERVER=fl-server:8080
      - FL_CLIENT_ID=client_2
      - DATA_SOURCE=coinbase
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fl-server
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: server
        image: sigmax:latest
        args: ["python", "-m", "scripts.fl_server"]
        ports:
        - containerPort: 8080

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: fl-client
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: client
        image: sigmax:latest
        args: ["python", "-m", "scripts.fl_client"]
        env:
        - name: FL_SERVER
          value: "fl-server:8080"
```

## Best Practices

### 1. Data Quality
- Ensure consistent data preprocessing
- Normalize features identically
- Handle missing values uniformly

### 2. Model Convergence
- Use sufficient local epochs (3-10)
- Monitor training metrics
- Adjust learning rate per client

### 3. Client Participation
- Balance client contributions
- Handle stragglers (slow clients)
- Set reasonable timeouts

### 4. Privacy Protection
- Implement differential privacy
- Use secure aggregation
- Audit model updates

## Troubleshooting

### Issue: Clients can't connect

**Solution:**
```bash
# Check server is running
telnet server_ip 8080

# Check firewall rules
sudo ufw allow 8080/tcp
```

### Issue: Model not converging

**Solutions:**
- Increase local epochs
- Adjust learning rate
- Check data quality across clients
- Ensure sufficient training data

### Issue: Memory errors

**Solutions:**
- Reduce batch size
- Use gradient accumulation
- Enable mixed precision training

## Performance

- **Communication**: ~100KB-1MB per round (model dependent)
- **Training Time**: Depends on local epochs and data size
- **Convergence**: Typically 10-50 rounds for good results

## References

- **Flower Documentation**: https://flower.ai/docs/
- **Flower GitHub**: https://github.com/adap/flower
- **FedAvg Paper**: McMahan et al., 2017
- **Federated Learning**: Google Research

## License

- Flower: Apache 2.0
- SIGMAX: See main repository LICENSE
