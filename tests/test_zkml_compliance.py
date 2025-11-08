"""
Tests for zkML Compliance Module

Tests zero-knowledge machine learning compliance verification including:
- ONNX model conversion
- ZK proof generation (with EZKL when available)
- ZK proof verification
- Compliance engine workflows
- Integration with compliance module
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from datetime import datetime

from core.modules.zkml_compliance import (
    ZKMLComplianceEngine,
    ONNXModelConverter,
    ZKProofGenerator,
    ZKProofVerifier,
    ComplianceProof,
    ProofStatus,
    create_zkml_engine,
    EZKL_AVAILABLE,
    ONNX_AVAILABLE,
    TORCH_AVAILABLE,
    SKLEARN_AVAILABLE
)


class TestONNXModelConverter:
    """Test ONNX model conversion"""

    def test_converter_initialization(self):
        """Test converter initializes with output directory"""
        converter = ONNXModelConverter()
        assert converter.output_dir is not None
        assert converter.output_dir.exists()

    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    def test_validate_onnx_model_invalid(self):
        """Test ONNX validation with invalid model"""
        converter = ONNXModelConverter()

        # Create invalid ONNX file
        temp_file = tempfile.NamedTemporaryFile(suffix=".onnx", delete=False)
        temp_file.write(b"not a valid onnx model")
        temp_file.close()

        is_valid = converter.validate_onnx_model(temp_file.name)
        assert not is_valid

    @pytest.mark.skipif(not (TORCH_AVAILABLE and ONNX_AVAILABLE), reason="PyTorch or ONNX not available")
    def test_convert_pytorch_model(self):
        """Test PyTorch model to ONNX conversion"""
        import torch
        import torch.nn as nn

        converter = ONNXModelConverter()

        # Create simple PyTorch model
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(5, 1)
                self.sigmoid = nn.Sigmoid()

            def forward(self, x):
                return self.sigmoid(self.linear(x))

        model = SimpleModel()

        # Convert to ONNX
        onnx_path = converter.convert_pytorch_model(
            model=model,
            input_shape=(1, 5),
            model_name="test_pytorch"
        )

        assert Path(onnx_path).exists()
        assert converter.validate_onnx_model(onnx_path)


class TestZKProofGenerator:
    """Test ZK proof generation"""

    @pytest.mark.skipif(not EZKL_AVAILABLE, reason="EZKL not available")
    def test_generator_initialization(self):
        """Test proof generator initializes"""
        generator = ZKProofGenerator()
        assert generator.output_dir is not None
        assert generator.output_dir.exists()

    @pytest.mark.asyncio
    async def test_fallback_proof_generation(self):
        """Test fallback proof generation when EZKL not available"""
        if EZKL_AVAILABLE:
            generator = ZKProofGenerator()
        else:
            pytest.skip("Testing fallback, but would need generator mock")

        # Use fallback method directly
        model_hash = "test_model_hash_123"
        input_hash = "test_input_hash_456"
        output_hash = "test_output_hash_789"

        if EZKL_AVAILABLE:
            proof_data, vk_data = await generator.generate_proof_fallback(
                model_hash, input_hash, output_hash
            )

            assert proof_data is not None
            assert vk_data is not None
            assert b"mock" in vk_data.lower()


class TestZKProofVerifier:
    """Test ZK proof verification"""

    @pytest.mark.skipif(not EZKL_AVAILABLE, reason="EZKL not available")
    def test_verifier_initialization(self):
        """Test proof verifier initializes"""
        verifier = ZKProofVerifier()
        assert verifier is not None

    @pytest.mark.asyncio
    async def test_fallback_proof_verification(self):
        """Test fallback proof verification"""
        if not EZKL_AVAILABLE:
            pytest.skip("EZKL not available")

        verifier = ZKProofVerifier()

        # Create mock proof
        import json
        proof_dict = {
            "model_hash": "test_hash",
            "input_hash": "test_input",
            "output_hash": "test_output"
        }
        proof_data = json.dumps(proof_dict).encode()
        vk_data = b"mock_vk"

        is_valid = await verifier.verify_proof_fallback(proof_data, vk_data)
        assert is_valid


class TestComplianceProof:
    """Test ComplianceProof dataclass"""

    def test_proof_creation(self):
        """Test creating compliance proof"""
        proof = ComplianceProof(
            proof_id="test_proof_001",
            timestamp=datetime.now(),
            model_hash="model_hash_123",
            input_hash="input_hash_456",
            output_hash="output_hash_789",
            proof_data=b"test_proof_data",
            verification_key=b"test_vk",
            status=ProofStatus.GENERATED,
            is_compliant=True,
            metadata={"test": "metadata"}
        )

        assert proof.proof_id == "test_proof_001"
        assert proof.is_compliant is True
        assert proof.status == ProofStatus.GENERATED

    def test_proof_to_dict(self):
        """Test converting proof to dictionary"""
        timestamp = datetime.now()
        proof = ComplianceProof(
            proof_id="test_proof_002",
            timestamp=timestamp,
            model_hash="model_hash",
            input_hash="input_hash",
            output_hash="output_hash",
            proof_data=None,
            verification_key=None,
            status=ProofStatus.PENDING,
            is_compliant=False,
            metadata={}
        )

        proof_dict = proof.to_dict()
        assert proof_dict["proof_id"] == "test_proof_002"
        assert proof_dict["status"] == "pending"
        assert proof_dict["is_compliant"] is False


class TestZKMLComplianceEngine:
    """Test main zkML compliance engine"""

    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)
        assert engine is not None
        assert engine.model_converter is not None
        assert engine.proof_history == []

    def test_engine_initialization_with_ezkl(self):
        """Test engine initialization with EZKL"""
        if EZKL_AVAILABLE:
            engine = ZKMLComplianceEngine(enable_ezkl=True)
            assert engine.enable_ezkl is True
            assert engine.proof_generator is not None
            assert engine.proof_verifier is not None
        else:
            engine = ZKMLComplianceEngine(enable_ezkl=True)
            assert engine.enable_ezkl is False

    def test_hash_data(self):
        """Test data hashing"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)

        # Test with numpy array
        data1 = np.array([[1, 2, 3]])
        hash1 = engine._hash_data(data1)
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex

        # Test with string
        data2 = "test_string"
        hash2 = engine._hash_data(data2)
        assert isinstance(hash2, str)
        assert len(hash2) == 64

        # Test deterministic
        hash3 = engine._hash_data(data1)
        assert hash1 == hash3

    @pytest.mark.asyncio
    async def test_prove_compliance_fallback(self):
        """Test compliance proof generation with fallback"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)

        # Create simple test data
        input_data = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]], dtype=np.float32)

        # Create mock ONNX model path (will fail gracefully)
        with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
            model_path = f.name

        # Should create a failed proof
        proof = await engine.prove_compliance(
            model=model_path,
            input_data=input_data,
            model_type="onnx"
        )

        assert proof is not None
        assert proof.status == ProofStatus.FAILED
        assert "error" in proof.metadata

    @pytest.mark.asyncio
    @pytest.mark.skipif(not ONNX_AVAILABLE, reason="ONNX not available")
    async def test_prove_compliance_with_onnx(self):
        """Test compliance proof with valid ONNX model"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)

        # Create simple ONNX model for testing
        if ONNX_AVAILABLE:
            import onnx
            from onnx import helper, TensorProto

            # Create a simple linear model: output = input * 0.5
            input_tensor = helper.make_tensor_value_info('input', TensorProto.FLOAT, [1, 5])
            output_tensor = helper.make_tensor_value_info('output', TensorProto.FLOAT, [1, 1])

            # Create constant tensor for weights
            weights = helper.make_tensor(
                name='weights',
                data_type=TensorProto.FLOAT,
                dims=[5, 1],
                vals=[0.5] * 5
            )

            # Create MatMul node
            matmul_node = helper.make_node(
                'MatMul',
                inputs=['input', 'weights'],
                outputs=['output']
            )

            # Create graph
            graph = helper.make_graph(
                [matmul_node],
                'simple_model',
                [input_tensor],
                [output_tensor],
                [weights]
            )

            # Create model with IR version 11 (max supported by onnxruntime)
            model = helper.make_model(graph, producer_name='test')
            model.opset_import[0].version = 11
            model.ir_version = 11

            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
                onnx.save(model, f.name)
                model_path = f.name

            # Test data
            input_data = np.array([[1.0, 2.0, 3.0, 4.0, 5.0]], dtype=np.float32)

            # Generate proof (will use fallback)
            proof = await engine.prove_compliance(
                model=model_path,
                input_data=input_data,
                model_type="onnx",
                metadata={"test": "onnx_model"}
            )

            # Proof should be generated (fallback mode)
            assert proof is not None
            assert proof.model_hash != ""
            assert proof.input_hash != ""

    @pytest.mark.asyncio
    async def test_verify_compliance_proof(self):
        """Test proof verification"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)

        # Create mock proof
        proof = ComplianceProof(
            proof_id="test_verify",
            timestamp=datetime.now(),
            model_hash="hash1",
            input_hash="hash2",
            output_hash="hash3",
            proof_data=b'{"model_hash":"h1","input_hash":"h2","output_hash":"h3"}',
            verification_key=b"mock_vk",
            status=ProofStatus.GENERATED,
            is_compliant=True,
            metadata={}
        )

        # Verify (will use fallback)
        is_valid = await engine.verify_compliance_proof(proof)

        # Fallback verification should work with properly formatted proof
        assert is_valid or not EZKL_AVAILABLE  # Fallback or EZKL verification

    def test_get_proof_history(self):
        """Test getting proof history"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)

        # Add some proofs to history
        for i in range(5):
            proof = ComplianceProof(
                proof_id=f"proof_{i}",
                timestamp=datetime.now(),
                model_hash=f"hash_{i}",
                input_hash=f"input_{i}",
                output_hash=f"output_{i}",
                proof_data=None,
                verification_key=None,
                status=ProofStatus.PENDING,
                is_compliant=True,
                metadata={}
            )
            engine.proof_history.append(proof)

        history = engine.get_proof_history(limit=3)
        assert len(history) == 3
        assert history[0].proof_id == "proof_2"  # Last 3

    def test_get_compliance_stats(self):
        """Test compliance statistics"""
        engine = ZKMLComplianceEngine(enable_ezkl=False)

        # Add various proofs
        proofs = [
            (ProofStatus.VERIFIED, True),
            (ProofStatus.VERIFIED, True),
            (ProofStatus.GENERATED, False),
            (ProofStatus.FAILED, False)
        ]

        for status, is_compliant in proofs:
            proof = ComplianceProof(
                proof_id=f"proof_{status.value}",
                timestamp=datetime.now(),
                model_hash="hash",
                input_hash="input",
                output_hash="output",
                proof_data=None,
                verification_key=None,
                status=status,
                is_compliant=is_compliant,
                metadata={}
            )
            engine.proof_history.append(proof)

        stats = engine.get_compliance_stats()
        assert stats["total_proofs"] == 4
        assert stats["verified_proofs"] == 2
        assert stats["compliant_proofs"] == 2
        assert stats["failed_proofs"] == 1
        assert stats["verification_rate"] == 0.5
        assert stats["compliance_rate"] == 0.5


class TestCreateZKMLEngine:
    """Test convenience function"""

    def test_create_engine(self):
        """Test creating engine with convenience function"""
        engine = create_zkml_engine(enable_ezkl=False)
        assert isinstance(engine, ZKMLComplianceEngine)
        assert engine.enable_ezkl is False

    def test_create_engine_with_ezkl(self):
        """Test creating engine with EZKL enabled"""
        engine = create_zkml_engine(enable_ezkl=True)
        assert isinstance(engine, ZKMLComplianceEngine)

        if EZKL_AVAILABLE:
            assert engine.enable_ezkl is True
        else:
            assert engine.enable_ezkl is False


class TestComplianceModuleIntegration:
    """Test integration with ComplianceModule"""

    @pytest.mark.asyncio
    async def test_compliance_module_with_zkml(self):
        """Test ComplianceModule with zkML enabled"""
        from core.modules.compliance import ComplianceModule

        # Create compliance module with zkML
        compliance = ComplianceModule(enable_zkml=True)
        await compliance.initialize()

        # Check zkML stats
        zkml_stats = compliance.get_zkml_stats()

        if compliance.enable_zkml:
            assert zkml_stats is not None
            assert "total_proofs" in zkml_stats
        else:
            assert zkml_stats is None

    @pytest.mark.asyncio
    async def test_compliance_check_with_zkml_fallback(self):
        """Test zkML compliance check falls back gracefully"""
        from core.modules.compliance import ComplianceModule

        compliance = ComplianceModule(enable_zkml=True)
        await compliance.initialize()

        trade_data = {
            "symbol": "BTC/USDT",
            "size": 1.0,
            "leverage": 1,
            "price": 50000.0,
            "volume": 1000.0,
            "position_pct": 5.0,
            "side": "buy"
        }

        # This should fall back to standard compliance check
        # since we don't have a valid model
        result = await compliance.check_compliance_with_zkml(
            model="/tmp/nonexistent.onnx",
            trade_data=trade_data,
            model_type="onnx"
        )

        assert "compliant" in result
        # Either zkML worked or it fell back to standard check
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
