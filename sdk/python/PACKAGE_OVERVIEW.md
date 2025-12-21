# SIGMAX Python SDK - Package Overview

## Quick Facts

- **Package Name**: `sigmax-sdk`
- **Version**: 1.0.0
- **Python**: 3.11+
- **License**: MIT
- **Type Safety**: Full type hints with strict mypy compliance
- **Async**: Async-first design with httpx
- **Status**: Production-ready

## Installation

```bash
# From PyPI (when published)
pip install sigmax-sdk

# From source
cd /Users/mac/Projects/SIGMAX/sdk/python
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
import asyncio
from sigmax_sdk import SigmaxClient, RiskProfile

async def main():
    async with SigmaxClient(api_url="http://localhost:8000") as client:
        # Get system status
        status = await client.get_status()
        print(f"System: {status.status}")

        # Analyze market
        result = await client.analyze("BTC/USDT", RiskProfile.MODERATE)
        print(f"Analysis: {result}")

asyncio.run(main())
```

## Package Structure

```
sdk/python/
├── sigmax_sdk/              # Main package
│   ├── __init__.py          # Public API exports
│   ├── client.py            # SigmaxClient implementation
│   ├── models.py            # Pydantic models
│   ├── exceptions.py        # Exception hierarchy
│   ├── types.py             # Type definitions
│   └── py.typed             # Type hints marker
├── tests/                   # Unit tests
│   ├── __init__.py
│   └── test_client.py       # Client tests with mocks
├── examples/                # Usage examples
│   ├── basic_usage.py       # Getting started
│   ├── streaming.py         # SSE streaming
│   ├── async_operations.py  # Advanced async patterns
│   ├── error_handling.py    # Error handling patterns
│   └── README.md            # Example documentation
├── pyproject.toml           # Package configuration
├── setup.py                 # Setup script
├── README.md                # User documentation
├── DEVELOPMENT.md           # Developer guide
├── CHANGELOG.md             # Version history
├── LICENSE                  # MIT License
├── Makefile                 # Development commands
├── MANIFEST.in              # Package manifest
├── .gitignore               # Git ignore rules
└── verify_package.py        # Verification script
```

## Core Components

### 1. SigmaxClient

Async HTTP client for SIGMAX API with full type safety.

**Features:**
- Context manager support
- Automatic connection pooling
- Retry logic with exponential backoff
- Comprehensive error handling
- SSE streaming support

**Methods:**
- `analyze()` - Synchronous market analysis
- `analyze_stream()` - Streaming market analysis
- `get_status()` - System status
- `propose_trade()` - Create trade proposal
- `list_proposals()` - List all proposals
- `get_proposal()` - Get proposal details
- `approve_proposal()` - Approve proposal
- `execute_proposal()` - Execute proposal

### 2. Pydantic Models

Type-safe data structures with validation.

**Models:**
- `SystemStatus` - System health and metrics
- `TradeProposal` - Trade proposal details
- `AnalysisResult` - Market analysis results
- `MarketData` - Market data snapshot
- `ChatMessage` - Chat message structure

**Enums:**
- `RiskProfile` - CONSERVATIVE, MODERATE, AGGRESSIVE
- `TradeMode` - PAPER, LIVE
- `ProposalStatus` - PENDING, APPROVED, REJECTED, EXECUTED, CANCELLED

### 3. Exception Hierarchy

```
SigmaxError (base)
├── SigmaxAPIError
│   ├── SigmaxAuthenticationError (401/403)
│   ├── SigmaxRateLimitError (429)
│   └── SigmaxValidationError (400/422)
├── SigmaxConnectionError
└── SigmaxTimeoutError
```

### 4. Type Definitions

- `StreamEvent` - SSE event structure
- `RiskProfileType` - Risk profile literal type
- `TradeModeType` - Trade mode literal type
- `ProposalStatusType` - Proposal status literal type
- `EventType` - Event type literal type

## Key Features

### Async-First Design

All operations are async for optimal performance:

```python
async with SigmaxClient() as client:
    # Single operation
    status = await client.get_status()

    # Concurrent operations
    results = await asyncio.gather(
        client.analyze("BTC/USDT"),
        client.analyze("ETH/USDT"),
    )
```

### Server-Sent Events Streaming

Real-time updates via SSE:

```python
async for event in client.analyze_stream("BTC/USDT"):
    print(f"Status: {event['status']}")
    print(f"Message: {event['message']}")
    if event.get('final'):
        break
```

### Type Safety

Complete type hints with Pydantic validation:

```python
from sigmax_sdk import TradeProposal, RiskProfile

proposal: TradeProposal = await client.propose_trade(
    symbol="BTC/USDT",
    risk_profile=RiskProfile.MODERATE,  # Type-checked enum
    size=0.1,  # Validated as Decimal
)
```

### Error Recovery

Comprehensive error handling with specific exceptions:

```python
from sigmax_sdk import (
    SigmaxAuthenticationError,
    SigmaxRateLimitError,
    SigmaxTimeoutError,
)

try:
    result = await client.analyze("BTC/USDT")
except SigmaxAuthenticationError:
    print("Invalid API key")
except SigmaxRateLimitError as e:
    await asyncio.sleep(e.retry_after or 5)
except SigmaxTimeoutError:
    print("Request timed out")
```

### Resource Management

Automatic cleanup with context managers:

```python
async with SigmaxClient() as client:
    # Client automatically closed on exit
    result = await client.get_status()
```

## Development Workflow

### Install Development Dependencies

```bash
make dev
# or
pip install -e ".[dev]"
```

### Run Tests

```bash
make test
# or
pytest tests/ -v --cov=sigmax_sdk
```

### Code Quality

```bash
# Format code
make format

# Lint
make lint

# Type check
make type-check

# All checks
make check
```

### Build Package

```bash
make build
# Creates dist/sigmax_sdk-1.0.0-py3-none-any.whl
```

### Publish to PyPI

```bash
make publish
# Requires twine and PyPI credentials
```

## Testing

### Unit Tests

Full test coverage with `pytest-httpx` for mocking:

```python
@pytest.mark.asyncio
async def test_get_status_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_response(
        url="http://test-api/api/status",
        json={"status": "online", ...},
    )
    status = await client.get_status()
    assert status.status == "online"
```

### Running Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_client.py::test_get_status_success

# With coverage
pytest --cov=sigmax_sdk --cov-report=html
```

## Examples

### Basic Usage

```bash
python examples/basic_usage.py
```

Demonstrates:
- Client initialization
- System status checks
- Market analysis
- Proposal listing

### Streaming Analysis

```bash
python examples/streaming.py
```

Demonstrates:
- SSE streaming
- Real-time updates
- Event filtering
- Concurrent streams

### Async Operations

```bash
python examples/async_operations.py
```

Demonstrates:
- Batch operations
- Retry patterns
- Complete workflows
- System monitoring

### Error Handling

```bash
python examples/error_handling.py
```

Demonstrates:
- Exception types
- Retry strategies
- Graceful degradation
- Error recovery

## API Coverage

| Endpoint | Method | SDK Method |
|----------|--------|------------|
| `/api/status` | GET | `get_status()` |
| `/api/chat/stream` | POST | `analyze()` |
| `/api/chat/stream` | POST (SSE) | `analyze_stream()` |
| `/api/chat/proposals` | POST | `propose_trade()` |
| `/api/chat/proposals` | GET | `list_proposals()` |
| `/api/chat/proposals/{id}` | GET | `get_proposal()` |
| `/api/chat/proposals/{id}/approve` | POST | `approve_proposal()` |
| `/api/chat/proposals/{id}/execute` | POST | `execute_proposal()` |

## Dependencies

### Runtime

- `httpx >= 0.27.0` - Async HTTP client
- `httpx-sse >= 0.4.0` - SSE support
- `pydantic >= 2.0.0` - Data validation

### Development

- `pytest >= 7.4.0` - Testing framework
- `pytest-asyncio >= 0.21.0` - Async test support
- `pytest-cov >= 4.1.0` - Coverage reporting
- `pytest-httpx >= 0.28.0` - HTTP mocking
- `black >= 23.7.0` - Code formatting
- `ruff >= 0.1.0` - Linting
- `mypy >= 1.4.1` - Type checking
- `pre-commit >= 3.3.3` - Git hooks

## Performance

### Async Benefits

- Concurrent requests with `asyncio.gather()`
- Non-blocking I/O operations
- Efficient connection pooling
- Streaming for large responses

### Benchmarks

```python
# Sequential (slow)
for symbol in symbols:
    await client.analyze(symbol)  # 5s each = 25s total

# Concurrent (fast)
await asyncio.gather(*[
    client.analyze(symbol) for symbol in symbols
])  # ~5s total
```

## Type Checking

Full mypy strict mode compliance:

```bash
mypy sigmax_sdk --strict
# Success: no issues found
```

Type stubs included via `py.typed` marker.

## Publishing

### Pre-publish Checklist

- [ ] All tests pass
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Version bumped
- [ ] CHANGELOG updated
- [ ] Examples tested

### Build and Publish

```bash
# Clean old builds
make clean

# Build distribution
make build

# Upload to PyPI
make publish
```

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

- **GitHub Issues**: https://github.com/I-Onlabs/SIGMAX/issues
- **Discussions**: https://github.com/I-Onlabs/SIGMAX/discussions
- **Documentation**: https://github.com/I-Onlabs/SIGMAX/tree/main/sdk/python

## Related Projects

- [SIGMAX Core](https://github.com/I-Onlabs/SIGMAX) - Main trading system
- [SIGMAX CLI](https://github.com/I-Onlabs/SIGMAX/tree/main/core/cli) - Command-line interface

---

**Built with modern Python best practices for production-ready AI trading.**
