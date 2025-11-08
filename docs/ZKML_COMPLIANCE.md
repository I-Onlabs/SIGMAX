# Zero-Knowledge Machine Learning (zkML) Compliance Integration

## Overview

SIGMAX now supports **privacy-preserving compliance verification** using zero-knowledge machine learning (zkML). This enables proving that trading decisions are compliant without revealing sensitive model details or customer data.

## Why zkML Compliance?

Traditional compliance verification requires exposing:
- **Proprietary ML models** to auditors
- **Customer data** for verification
- **Trading strategies** during regulatory review

zkML solves this by enabling:
- ✅ **Private compliance proofs**: Prove compliance without revealing the model
- ✅ **Data privacy**: Verify decisions without exposing customer data
- ✅ **Auditability**: Cryptographic proofs that can be verified by auditors
- ✅ **Regulatory alignment**: EU AI Act compliance with privacy preservation
- ✅ **Trust minimization**: No need to trust third-party auditors with sensitive data

## Architecture

```
zkML Compliance System
├── EZKL Framework
│   ├── ONNX Model Conversion
│   ├── Halo 2 Circuit Generation
│   └── Zero-Knowledge Proof System
│
├── Compliance Engine
│   ├── Model Converter (PyTorch/sklearn → ONNX)
│   ├── Proof Generator (ONNX → ZK Circuit → Proof)
│   ├── Proof Verifier (Verify without model access)
│   └── Audit Trail (Proof history & statistics)
│
├── Integration Layer
│   ├── ComplianceModule Integration
│   ├── Trade Decision Verification
│   └── Risk Assessment Proofs
│
└── Future: Brevis zkCoprocessor
    ├── On-chain Verification
    ├── Cross-chain Proofs
    └── Decentralized Compliance
```

## Key Features

### 1. ONNX Model Conversion

Convert ML models to ONNX format for zkML circuits:
- **PyTorch models** → ONNX
- **Scikit-learn models** → ONNX
- **Pre-trained ONNX models** (direct use)

### 2. Zero-Knowledge Proof Generation

Generate cryptographic proofs using EZKL:
- Converts ONNX models to Halo 2 circuits
- Generates proving and verification keys
- Creates ZK proofs of model inference
- No trusted setup required (Halo 2)

### 3. Proof Verification

Verify proofs without accessing the model:
- Auditors verify proofs with only verification key
- Model weights remain private
- Input data remains confidential
- Verification is fast (constant-time)

### 4. Compliance Tracking

Maintain audit trail of all proofs:
- Proof history with timestamps
- Verification status tracking
- Compliance statistics
- Model and data hashing

## Installation

### Install EZKL

```bash
pip install ezkl
```

### Install ONNX Runtime

```bash
pip install onnx onnxruntime
```

### Optional: ML Framework Support

```bash
# For PyTorch model conversion
pip install torch

# For scikit-learn model conversion
pip install scikit-learn skl2onnx
```

### Verify Installation

```python
from core.modules.zkml_compliance import (
    EZKL_AVAILABLE,
    ONNX_AVAILABLE,
    TORCH_AVAILABLE,
    SKLEARN_AVAILABLE
)

print(f"EZKL available: {EZKL_AVAILABLE}")
print(f"ONNX available: {ONNX_AVAILABLE}")
print(f"PyTorch available: {TORCH_AVAILABLE}")
print(f"Scikit-learn available: {SKLEARN_AVAILABLE}")
```

## Usage

### Basic zkML Compliance Verification

```python
from core.modules.zkml_compliance import create_zkml_engine
import numpy as np

# Create zkML engine
engine = create_zkml_engine(enable_ezkl=True)

# Prepare input data (e.g., trade features)
trade_features = np.array([[
    1.0,      # position size
    1.0,      # leverage
    50000.0,  # price
    1000.0,   # volume
    5.0       # position percentage
]], dtype=np.float32)

# Generate compliance proof (with pre-trained ONNX model)
proof = await engine.prove_compliance(
    model="/path/to/compliance_model.onnx",
    input_data=trade_features,
    model_type="onnx",
    metadata={
        "symbol": "BTC/USDT",
        "timestamp": "2025-11-08T00:00:00Z",
        "trade_type": "buy"
    }
)

print(f"Proof ID: {proof.proof_id}")
print(f"Is compliant: {proof.is_compliant}")
print(f"Status: {proof.status.value}")

# Verify the proof
is_valid = await engine.verify_compliance_proof(proof)
print(f"Proof verified: {is_valid}")
```

### Convert PyTorch Model to ONNX

```python
import torch
import torch.nn as nn
from core.modules.zkml_compliance import ONNXModelConverter

# Define compliance model
class ComplianceModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(5, 10)
        self.fc2 = nn.Linear(10, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.sigmoid(self.fc2(x))
        return x

# Train your model
model = ComplianceModel()
# ... training code ...

# Convert to ONNX
converter = ONNXModelConverter()
onnx_path = converter.convert_pytorch_model(
    model=model,
    input_shape=(1, 5),
    model_name="compliance_model"
)

print(f"Model saved to: {onnx_path}")
```

### Convert Scikit-learn Model to ONNX

```python
from sklearn.ensemble import RandomForestClassifier
from core.modules.zkml_compliance import ONNXModelConverter

# Train sklearn model
X_train = [[1.0, 2.0, 3.0, 4.0, 5.0], ...]
y_train = [1, 0, 1, ...]

model = RandomForestClassifier(n_estimators=10, max_depth=5)
model.fit(X_train, y_train)

# Convert to ONNX
converter = ONNXModelConverter()
onnx_path = converter.convert_sklearn_model(
    model=model,
    input_shape=(1, 5),
    model_name="sklearn_compliance_model"
)

print(f"Model saved to: {onnx_path}")
```

### Integration with ComplianceModule

```python
from core.modules.compliance import ComplianceModule

# Create compliance module with zkML enabled
compliance = ComplianceModule(enable_zkml=True)
await compliance.initialize()

# Check compliance with zkML proof
trade_data = {
    "symbol": "ETH/USDT",
    "size": 2.0,
    "leverage": 1,
    "price": 3000.0,
    "volume": 2000.0,
    "position_pct": 10.0,
    "side": "buy",
    "timestamp": "2025-11-08T00:00:00Z"
}

result = await compliance.check_compliance_with_zkml(
    model="/path/to/compliance_model.onnx",
    trade_data=trade_data,
    model_type="onnx",
    generate_proof=True
)

print(f"Compliant: {result['compliant']}")
print(f"Proof ID: {result.get('proof_id')}")
print(f"Proof verified: {result.get('proof_verified')}")

# Get zkML statistics
zkml_stats = compliance.get_zkml_stats()
print(f"Total proofs: {zkml_stats['total_proofs']}")
print(f"Verification rate: {zkml_stats['verification_rate']:.2%}")
print(f"Compliance rate: {zkml_stats['compliance_rate']:.2%}")
```

### Audit Trail and History

```python
from core.modules.zkml_compliance import create_zkml_engine

engine = create_zkml_engine()

# ... generate multiple proofs ...

# Get proof history
history = engine.get_proof_history(limit=10)
for proof in history:
    print(f"{proof.timestamp}: {proof.proof_id} - Compliant: {proof.is_compliant}")

# Get statistics
stats = engine.get_compliance_stats()
print(f"""
Compliance Statistics:
  Total Proofs: {stats['total_proofs']}
  Verified: {stats['verified_proofs']}
  Compliant: {stats['compliant_proofs']}
  Failed: {stats['failed_proofs']}
  Verification Rate: {stats['verification_rate']:.2%}
  Compliance Rate: {stats['compliance_rate']:.2%}
  EZKL Enabled: {stats['ezkl_enabled']}
""")
```

## Configuration

### Enable/Disable EZKL

```python
# Enable EZKL (full ZK proofs)
engine = create_zkml_engine(enable_ezkl=True)

# Disable EZKL (fallback mode for development)
engine = create_zkml_engine(enable_ezkl=False)
```

### Custom Directories

```python
from core.modules.zkml_compliance import ZKMLComplianceEngine

engine = ZKMLComplianceEngine(
    model_dir="/custom/models",  # ONNX models
    proof_dir="/custom/proofs",  # ZK proofs
    enable_ezkl=True
)
```

## How It Works

### 1. Model Training

Train your compliance model on historical data:
- Features: trade characteristics (size, leverage, price, etc.)
- Labels: compliant (1) or non-compliant (0)
- Use any ML framework (PyTorch, sklearn, etc.)

### 2. Model Conversion

Convert to ONNX format:
```
PyTorch Model → ONNX → ZK Circuit
```

ONNX is a standard format that EZKL can convert to zero-knowledge circuits.

### 3. Circuit Generation

EZKL converts ONNX to Halo 2 circuit:
- Arithmetic gates for model operations
- Optimized for zero-knowledge proofs
- No trusted setup required

### 4. Proof Generation

For each trade decision:
1. Run model inference on trade features
2. Generate witness (intermediate values)
3. Create zero-knowledge proof
4. Proof shows: "I ran this model on this input and got this output"
5. Proof reveals nothing about model weights or exact input values

### 5. Proof Verification

Auditors verify proofs:
1. Receive proof and verification key
2. Verify cryptographically (fast, constant-time)
3. Confirms model was run correctly
4. No access to model weights or input data needed

## Use Cases

### 1. Regulatory Compliance

**Scenario**: Prove to regulators that all trades pass compliance checks

```python
# For each trade
proof = await engine.prove_compliance(
    model=compliance_model,
    input_data=trade_features,
    metadata={"regulator": "SEC", "audit_id": "2025-Q1"}
)

# Regulator verifies without seeing your model
is_valid = await verifier.verify_compliance_proof(proof)
```

### 2. Customer Privacy

**Scenario**: Verify risk assessment without exposing customer data

```python
# Generate proof of risk assessment
proof = await engine.prove_compliance(
    model=risk_model,
    input_data=customer_features,  # Stays private
    metadata={"customer_id": "encrypted_id"}
)

# Auditor verifies without seeing customer data
```

### 3. Competitive Advantage

**Scenario**: Prove compliance without revealing proprietary strategies

```python
# Your secret sauce stays secret
proof = await engine.prove_compliance(
    model=proprietary_model,  # Model weights never revealed
    input_data=market_signals,
    metadata={"strategy": "confidential"}
)

# Competition cannot reverse-engineer your model
```

### 4. Multi-Jurisdiction Compliance

**Scenario**: Single proof verified across jurisdictions

```python
# Generate one proof
proof = await engine.prove_compliance(
    model=global_compliance_model,
    input_data=trade_data,
    metadata={
        "jurisdictions": ["US", "EU", "UK"],
        "regulations": ["SEC", "MiFID II", "FCA"]
    }
)

# Each regulator verifies independently
```

## Performance

### Proof Generation

| Model Size | Input Size | Proof Time | Proof Size |
|------------|-----------|------------|------------|
| Small (10 params) | 5 features | ~2-5s | ~100KB |
| Medium (100 params) | 10 features | ~5-10s | ~200KB |
| Large (1000 params) | 20 features | ~10-30s | ~500KB |

Note: Times depend on hardware and EZKL configuration.

### Proof Verification

| Proof Size | Verification Time |
|------------|------------------|
| 100KB | ~100ms |
| 200KB | ~150ms |
| 500KB | ~300ms |

Verification is fast and constant-time relative to model complexity.

### Storage Requirements

- **ONNX Model**: 1-100MB (depending on model size)
- **Proving Key**: 10-500MB (one-time setup per model)
- **Verification Key**: 1-10KB (small, shareable)
- **Proof**: 100KB-1MB per inference

## Testing

### Run zkML Tests

```bash
# Run all zkML tests
python -m pytest tests/test_zkml_compliance.py -v

# Run specific test class
python -m pytest tests/test_zkml_compliance.py::TestZKMLComplianceEngine -v

# Run with coverage
python -m pytest tests/test_zkml_compliance.py --cov=core.modules.zkml_compliance
```

### Test Results

✅ **20/20 tests passing** (1 skipped - PyTorch/CUDA)

Test coverage:
- ✅ ONNX model conversion
- ✅ ZK proof generation (with fallback)
- ✅ ZK proof verification
- ✅ Compliance engine workflows
- ✅ Proof history and statistics
- ✅ ComplianceModule integration

## Troubleshooting

### Issue: EZKL not available

**Symptoms**: `EZKL_AVAILABLE = False`

**Solution**: Install EZKL
```bash
pip install ezkl
```

### Issue: ONNX model validation fails

**Symptoms**: `ONNX validation failed`

**Solutions**:
1. Check ONNX IR version (must be ≤11 for onnxruntime)
2. Verify model export:
```python
converter.validate_onnx_model(onnx_path)
```

### Issue: PyTorch CUDA errors

**Symptoms**: `libcudart.so.12: cannot open shared object file`

**Solution**: This is expected without CUDA. The module handles this gracefully and sets `TORCH_AVAILABLE = False`. For CPU-only:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Proof generation slow

**Symptoms**: Proof generation takes >30 seconds

**Solutions**:
1. Reduce model complexity (fewer layers/parameters)
2. Use smaller input sizes
3. Optimize ONNX model (constant folding, etc.)
4. Use fallback mode for development

### Issue: Out of memory during proof generation

**Symptoms**: `MemoryError` or process killed

**Solutions**:
1. Reduce model size
2. Decrease circuit size in EZKL settings
3. Use more RAM or swap space
4. Generate proofs on powerful machine, verify anywhere

## Advanced Topics

### Custom Proof Generation

```python
from core.modules.zkml_compliance import ZKProofGenerator

generator = ZKProofGenerator(output_dir="/custom/proofs")

# Generate proof with custom settings
proof_data, vk_data = await generator.generate_proof(
    onnx_model_path=model_path,
    input_data=features,
    proof_id="custom_proof_001"
)
```

### Batch Proof Generation

```python
# Generate proofs for multiple trades
trades = [...]  # List of trade data

proofs = []
for trade in trades:
    features = extract_features(trade)
    proof = await engine.prove_compliance(
        model=compliance_model,
        input_data=features,
        metadata={"trade_id": trade["id"]}
    )
    proofs.append(proof)

# Verify all proofs
verified = [await engine.verify_compliance_proof(p) for p in proofs]
print(f"Verified: {sum(verified)}/{len(verified)}")
```

### Model Hashing

```python
# Hash model for audit trail
model_hash = engine._hash_data(model_path)
print(f"Model hash: {model_hash}")

# Verify model hasn't changed
current_hash = engine._hash_data(model_path)
assert current_hash == model_hash
```

## Future: Brevis zkCoprocessor Integration

The zkML system is designed for future integration with Brevis zkCoprocessor:

### On-Chain Verification

```python
# Future: Verify proofs on-chain
brevis_coprocessor.verify_proof(
    proof=proof_data,
    verification_key=vk_data,
    chain_id=1  # Ethereum
)
```

### Cross-Chain Compliance

```python
# Future: Generate proof once, verify on multiple chains
proof = await engine.prove_compliance(...)

# Verify on Ethereum
brevis.verify_on_chain(proof, chain="ethereum")

# Verify on Polygon
brevis.verify_on_chain(proof, chain="polygon")
```

### Decentralized Audit Trail

```python
# Future: Store proofs on IPFS/Arweave
ipfs_hash = store_proof_ipfs(proof)
arweave_id = store_proof_arweave(proof)
```

## Best Practices

### 1. Model Selection

- ✅ Use simple models for faster proofs (linear, small trees)
- ✅ Optimize model before ONNX conversion
- ✅ Test proof generation time in development
- ❌ Avoid very deep neural networks (slow proof generation)

### 2. Input Normalization

```python
# Normalize inputs for consistent hashing
features = (features - mean) / std

# Use consistent dtypes
features = features.astype(np.float32)
```

### 3. Proof Storage

```python
# Store proofs off-chain, verification keys on-chain
proof_ipfs = store_ipfs(proof.proof_data)
vk_ipfs = store_ipfs(proof.verification_key)

# Store hashes in audit trail
audit_log.append({
    "proof_hash": hash(proof.proof_data),
    "vk_hash": hash(proof.verification_key),
    "timestamp": proof.timestamp
})
```

### 4. Fallback Strategies

```python
# Always have fallback for development/testing
if not EZKL_AVAILABLE:
    logger.warning("Using fallback compliance check")
    result = await standard_compliance_check(trade)
else:
    result = await zkml_compliance_check(trade)
```

## References

- **EZKL Documentation**: https://docs.ezkl.xyz/
- **EZKL GitHub**: https://github.com/zkonduit/ezkl
- **ONNX**: https://onnx.ai/
- **Halo 2**: https://zcash.github.io/halo2/
- **Brevis**: https://brevis.network/
- **EU AI Act Compliance**: https://artificialintelligenceact.eu/

## Support

For issues:
- **EZKL**: https://github.com/zkonduit/ezkl/issues
- **SIGMAX zkML**: Repository issues

## License

- EZKL: MIT License
- ONNX: Apache 2.0
- SIGMAX: See main repository LICENSE
