# Rust Execution Layer

## Overview

SIGMAX includes an ultra-low-latency Rust execution layer for achieving sub-100ns order execution. This layer provides:

- **Zero-copy data structures**
- **Lock-free operations**
- **Atomic statistics tracking**
- **Python bindings via PyO3**
- **Fallback to optimized Python implementation**

## Architecture

```
Python Layer (SIGMAX)
       ↓
core.modules.rust_execution (Python API)
       ↓
   [Attempts Import]
       ↓
   ┌─────────────┐
   │  Compiled   │────→ Ultra-low latency (<100ns)
   │  Rust Module│      Lock-free, zero-copy
   └─────────────┘
       OR
   ┌─────────────┐
   │  Optimized  │────→ High performance (~1-10μs)
   │  Python     │      Thread-safe, minimal allocation
   └─────────────┘
```

## Performance Targets

| Metric | Rust (Compiled) | Python (Fallback) |
|--------|----------------|-------------------|
| Avg Latency | <100ns | ~1-10μs |
| Min Latency | <50ns | ~500ns |
| Throughput | >1M orders/sec | ~50K orders/sec |
| Memory | Minimal | Low |

## Installation

### Option 1: Pre-compiled Binary (Recommended)

```bash
# Download pre-compiled Rust module
# (When available from releases)
cp sigmax_rust_execution.so /path/to/SIGMAX/

# Test
python -c "from core.modules.rust_execution import RUST_MODULE_AVAILABLE; print(f'Rust: {RUST_MODULE_AVAILABLE}')"
```

### Option 2: Compile from Source

**Requirements:**
- Rust 1.70+ (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- Python 3.10+
- PyO3 0.22+

**Build:**
```bash
cd rust_execution
cargo build --release

# Copy to Python path
cp target/release/libsigmax_rust_execution.so ../sigmax_rust_execution.so

# Test
python -c "import sigmax_rust_execution; print('✓ Rust module loaded')"
```

### Option 3: Use Python Fallback

The system automatically uses the Python implementation if the Rust module isn't available:

```python
from core.modules.rust_execution import RUST_MODULE_AVAILABLE

if RUST_MODULE_AVAILABLE:
    print("✓ Using compiled Rust (ultra-low latency)")
else:
    print("✓ Using Python fallback (high performance)")
```

## Usage

### Basic Execution

```python
from core.modules.rust_execution import RustExecutionEngine

# Create engine
engine = RustExecutionEngine(queue_capacity=10000)

# Execute order
execution = engine.execute_order(
    symbol_id=1,        # Integer symbol ID (faster than string)
    side=0,            # 0 = buy, 1 = sell
    order_type=0,      # 0 = limit, 1 = market
    price=50000.0,
    quantity=1.0
)

print(f"Order {execution.order_id}: {execution.executed_quantity}@{execution.executed_price}")
print(f"Latency: {execution.latency_ns}ns")
print(f"Slippage: {execution.slippage}")
```

### Batch Execution

```python
from core.modules.rust_execution import execute_batch

# Prepare batch
orders = [
    (1, 0, 0, 50000.0, 1.0),  # symbol_id, side, type, price, qty
    (2, 1, 0, 3000.0, 2.0),
    (3, 0, 1, 100.0, 5.0),
]

# Execute batch
executions = execute_batch(engine, orders)

for exec in executions:
    print(f"Order {exec.order_id}: {exec.latency_ns}ns")
```

### Performance Monitoring

```python
# Get statistics
stats = engine.get_stats()

print(f"Total executions: {stats['total_executions']}")
print(f"Average latency: {stats['avg_latency_ns']}ns")
print(f"Min latency: {stats['min_latency_ns']}ns")
print(f"Max latency: {stats['max_latency_ns']}ns")

# Reset statistics
engine.reset_stats()
```

### Benchmarking

```python
from core.modules.rust_execution import benchmark_latency

# Run benchmark
results = benchmark_latency(iterations=10000)

print(f"Iterations: {results['iterations']}")
print(f"Average: {results['avg_ns']}ns")
print(f"P50: {results['p50_ns']}ns")
print(f"P95: {results['p95_ns']}ns")
print(f"P99: {results['p99_ns']}ns")
print(f"Min: {results['min_ns']}ns")
print(f"Max: {results['max_ns']}ns")
```

## Integration with SIGMAX

### With HFT Engine

```python
from core.modules.hft_execution import create_hft_engine
from core.modules.rust_execution import RustExecutionEngine

# Create Rust engine
rust_engine = RustExecutionEngine()

# Use with HFT engine
hft_engine = create_hft_engine(
    exchange_connector=exchange,
    execution_backend=rust_engine  # Use Rust for execution
)
```

### With CrewAI Orchestrator

```python
from core.agents.crewai_orchestrator import SIGMAXCrewAIOrchestrator
from core.modules.rust_execution import RustExecutionEngine

# Create Rust engine
rust_engine = RustExecutionEngine()

# Use with orchestrator
orchestrator = SIGMAXCrewAIOrchestrator(
    data_module=data_module,
    execution_module=rust_engine,  # Ultra-low latency execution
    # ... other modules
)
```

## Rust Module Details

### Data Structures

**RustExecution:**
```rust
pub struct RustExecution {
    pub order_id: u64,
    pub executed_price: f64,
    pub executed_quantity: f64,
    pub latency_ns: u64,
    pub slippage: f64,
}
```

**RustExecutionEngine:**
- Lock-free atomic operations
- Zero-copy order processing
- Inline critical paths
- Optimized for cache locality

### Key Optimizations

1. **Atomic Operations**: Lock-free counters using `AtomicU64`
2. **Inline Functions**: Critical paths marked `#[inline(always)]`
3. **Zero Allocation**: Stack-allocated orders in hot path
4. **Minimal Branching**: Optimized control flow
5. **Release Build**: LTO enabled, full optimization

### Build Optimizations

```toml
[profile.release]
lto = true              # Link-time optimization
codegen-units = 1       # Single codegen unit for best optimization
opt-level = 3          # Maximum optimization
strip = true           # Strip debug symbols
```

## Testing

### Run Tests

```bash
# Test Rust execution module
pytest tests/test_rust_execution.py -v

# Specific tests
pytest tests/test_rust_execution.py::TestRustExecutionEngine -v
```

### Test Results

- ✅ **5/5 tests passing**
- ✅ Engine initialization
- ✅ Order execution
- ✅ Statistics tracking
- ✅ Batch execution  
- ✅ Benchmarking

### Benchmark Results

Python Implementation:
- Average: ~1-10μs
- Throughput: ~50,000-100,000 orders/second

Compiled Rust (Expected):
- Average: <100ns  
- Throughput: >1,000,000 orders/second

## Development

### Adding New Features

1. **Update Rust code** (`rust_execution/src/lib.rs`)
2. **Rebuild**: `cargo build --release`
3. **Update Python fallback** (`core/modules/rust_execution.py`)
4. **Add tests** (`tests/test_rust_execution.py`)
5. **Test both implementations**

### Debugging

```bash
# Build with debug symbols
cargo build

# Run with backtrace
RUST_BACKTRACE=1 python your_script.py

# Check which implementation is used
python -c "from core.modules.rust_execution import RUST_MODULE_AVAILABLE; print(RUST_MODULE_AVAILABLE)"
```

## Troubleshooting

### Issue: Rust module not loading

**Symptoms**: `RUST_MODULE_AVAILABLE = False`

**Solutions**:
1. Check if compiled: `ls rust_execution/target/release/libsigmax_rust_execution.so`
2. Rebuild: `cd rust_execution && cargo build --release`
3. Copy to correct location
4. Check Python can import: `python -c "import sigmax_rust_execution"`

### Issue: Compilation fails

**Solutions**:
1. Update Rust: `rustup update`
2. Check PyO3 version: `cargo tree | grep pyo3`
3. Clean and rebuild: `cargo clean && cargo build --release`

### Issue: Performance not as expected

**Solutions**:
1. Verify release build: Check `Cargo.toml` profile
2. Check if Rust module loaded: Print `RUST_MODULE_AVAILABLE`
3. Run benchmark: `benchmark_latency(iterations=10000)`
4. Profile Python fallback if Rust not available

## Future Enhancements

Planned improvements:
1. **SIMD optimizations** for batch operations
2. **Custom allocator** for order pools
3. **Lock-free order book** integration
4. **Direct exchange API** bindings
5. **Async/await support** via tokio

## References

- [PyO3 Documentation](https://pyo3.rs/)
- [Rust Performance Book](https://nnethercote.github.io/perf-book/)
- [SIGMAX HFT Integration](./HFT_INTEGRATION.md)

## License

- Rust code: MIT License
- SIGMAX: See main repository LICENSE
