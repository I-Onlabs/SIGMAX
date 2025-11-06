# Contributing to SIGMAX

Thank you for your interest in contributing to SIGMAX! This document provides guidelines and instructions for contributors.

## 🎯 Ways to Contribute

1. **Bug Reports**: Report issues or unexpected behavior
2. **Feature Requests**: Suggest new features or improvements
3. **Code Contributions**: Submit bug fixes or new features
4. **Documentation**: Improve docs, examples, or tutorials
5. **Testing**: Add unit tests, integration tests, or benchmarks
6. **Strategy Examples**: Share trading strategy implementations

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- 4GB RAM minimum (8GB+ recommended)

### Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/SIGMAX.git
cd SIGMAX

# 2. Create a virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 4. Start infrastructure
docker-compose -f docker-compose.dev.yml up -d

# 5. Initialize databases
python tools/init_database.py --profile=a

# 6. Run tests
pytest tests/

# 7. Start services
python tools/runner.py --profile=a
```

### Development Dependencies

```txt
# requirements-dev.txt
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
black==23.7.0
flake8==6.0.0
mypy==1.4.1
isort==5.12.0
pre-commit==3.3.3
```

## 📝 Code Standards

### Python Style Guide

We follow **PEP 8** with these specifics:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`
- **Formatting**: Auto-formatted with `black`

### Code Formatting

```bash
# Format code with black
black .

# Sort imports
isort .

# Check style
flake8 .

# Type checking
mypy pkg/ apps/
```

### Pre-commit Hooks

Install pre-commit hooks to automatically format code:

```bash
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## 🏗️ Architecture Overview

### Project Structure

```
SIGMAX/
├── apps/              # Microservices
│   ├── ingest_cex/    # Market data ingestion
│   ├── book_shard/    # Order book management
│   ├── features/      # Feature extraction
│   ├── signals/       # Signal modules
│   ├── decision/      # Decision engine (L0-L5)
│   ├── risk/          # Risk management
│   ├── router/        # Order routing
│   └── exec_cex/      # Execution gateway
├── pkg/               # Shared libraries
│   ├── common/        # Utilities (logging, config, timing)
│   └── schemas/       # Data models
├── db/                # Database migrations
├── infra/             # Infrastructure configs
├── tests/             # Test suite
├── tools/             # Utility scripts
└── examples/          # Strategy examples
```

### Data Flow

```
Market Data → Ingestion → Order Books → Features → Signals
                                             ↓
                                       Decision Layer
                                          (L0-L5)
                                             ↓
                                       Risk Engine
                                             ↓
                                       Smart Router
                                             ↓
                                    Execution Gateway
```

### Key Concepts

1. **Event-Driven Architecture**: Services communicate via ZeroMQ pub/sub
2. **Single-Writer Order Books**: Lockless design for low latency
3. **Hybrid Decision Layer**: L0 (constraints) → L1 (rules) → L2 (ML) → L5 (arbiter)
4. **Pre-Trade Risk**: Pure function checks before order submission
5. **Nanosecond Timing**: Clock abstraction with simulation support

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=pkg --cov=apps --cov-report=html

# Specific test
pytest tests/unit/test_schemas.py::test_top_of_book_calculations
```

### Writing Tests

**Unit Test Example**:

```python
# tests/unit/test_my_feature.py
import pytest
from pkg.schemas import OrderIntent, Side, OrderType

def test_order_intent_creation():
    """Test OrderIntent creation with required fields"""
    order = OrderIntent.create(
        symbol_id=1,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        qty=0.1,
        price=50000.0
    )

    assert order.symbol_id == 1
    assert order.side == Side.BUY
    assert order.client_id is not None  # Auto-generated UUID
```

**Integration Test Example**:

```python
# tests/integration/test_pipeline.py
import pytest
from apps.book_shard.book_manager import BookManager
from pkg.schemas import MdUpdate

@pytest.mark.asyncio
async def test_book_pipeline():
    """Test order book processing pipeline"""
    book_manager = BookManager()

    # Send market data update
    update = MdUpdate(
        symbol_id=1,
        timestamp_ns=1000000000,
        bid_px=50000.0,
        bid_sz=1.5,
        ask_px=50010.0,
        ask_sz=2.0,
        sequence=1
    )

    tob = await book_manager.process_update(update)

    assert tob is not None
    assert tob.bid_price == 50000.0
```

### Test Coverage

Aim for:
- **Unit tests**: >80% coverage
- **Integration tests**: Cover critical paths
- **Edge cases**: Error handling, boundary conditions

## 🐛 Bug Reports

### Before Submitting

1. **Search existing issues**: Check if already reported
2. **Reproduce consistently**: Ensure bug is reproducible
3. **Test latest version**: Verify bug exists in `main` branch

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Start SIGMAX with `python tools/runner.py`
2. Send market data update with...
3. Observe error in...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Ubuntu 22.04
- Python: 3.11.4
- SIGMAX version: main branch (commit 1234abc)
- Profile: A

## Logs
```
Relevant log output
```

## Additional Context
Screenshots, stack traces, etc.
```

## ✨ Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How would you implement this?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Mockups, examples from other systems, etc.
```

## 🔧 Pull Requests

### Before Submitting

1. **Create an issue first**: Discuss major changes before implementation
2. **Fork the repository**: Work in your own fork
3. **Create a feature branch**: `git checkout -b feature/my-feature`
4. **Follow code standards**: Run formatters and linters
5. **Add tests**: Cover new functionality
6. **Update documentation**: Update relevant docs
7. **Test thoroughly**: Run full test suite

### PR Checklist

- [ ] Code follows style guide
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with `main`
- [ ] Changelog updated (if applicable)

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #123

## Changes Made
- Added feature X
- Fixed bug Y
- Updated documentation for Z

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing performed

## Screenshots (if applicable)
Before/after screenshots

## Checklist
- [ ] Code follows style guide
- [ ] Tests pass
- [ ] Documentation updated
```

### Commit Messages

Follow **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, no code change
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```
feat(decision): Add L3 ML prediction layer

Implement LightGBM model integration for L3 decision layer.
Includes feature preprocessing and model inference.

Closes #42
```

```
fix(risk): Correct position limit check

Position limit was checking absolute value incorrectly,
allowing positions to exceed limits in rare cases.

Fixes #87
```

## 📚 Documentation

### Documentation Standards

- **Docstrings**: All public functions/classes must have docstrings
- **Type hints**: Use type hints for all function parameters and returns
- **Examples**: Include usage examples in docstrings
- **README updates**: Update README.md for user-facing changes

### Docstring Example

```python
def calculate_microprice(bid_price: float, bid_size: float,
                         ask_price: float, ask_size: float) -> float:
    """
    Calculate volume-weighted microprice.

    The microprice is the weighted average of bid and ask prices,
    weighted by their respective sizes. This provides a better
    estimate of fair value than the simple midpoint.

    Args:
        bid_price: Best bid price
        bid_size: Size at best bid
        ask_price: Best ask price
        ask_size: Size at best ask

    Returns:
        Microprice as float

    Raises:
        ValueError: If sizes are zero or negative

    Example:
        >>> calculate_microprice(50000.0, 1.5, 50010.0, 2.0)
        50005.71
    """
    total_size = bid_size + ask_size
    if total_size <= 0:
        raise ValueError("Total size must be positive")

    return (bid_price * ask_size + ask_price * bid_size) / total_size
```

## 🎨 Adding New Services

### Service Template

```python
# apps/my_service/main.py
import asyncio
from pkg.common import get_logger, Config, MetricsCollector
from pkg.ipc import ZMQPublisher, ZMQSubscriber

class MyService:
    """
    Service description.

    Subscribes to: Stream X
    Publishes to: Stream Y
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.metrics = MetricsCollector(service_name="my_service")

        # Initialize IPC
        self.subscriber = ZMQSubscriber(stream_id=10)
        self.publisher = ZMQPublisher(stream_id=20)

    async def start(self):
        """Start service"""
        self.logger.info("my_service_starting")

        await self.subscriber.start()
        await self.publisher.start()

        # Message processing loop
        async for msg in self.subscriber:
            await self.process_message(msg)

    async def process_message(self, msg):
        """Process incoming message"""
        try:
            # Business logic here
            pass
        except Exception as e:
            self.logger.error("processing_error", error=str(e))
            self.metrics.increment_counter("errors_total")

async def main():
    config = Config.load("profiles/profile_a.yaml")
    service = MyService(config)
    await service.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧩 Adding New Strategies

See `examples/strategies/` for reference implementations.

### Strategy Template

```python
# examples/strategies/my_strategy.py
from pkg.schemas import FeatureFrame, OrderIntent, Side, OrderType
from pkg.common import get_logger

class MyStrategy:
    """
    Strategy description.

    Logic:
    - When condition X → BUY
    - When condition Y → SELL
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)

        # Strategy parameters
        self.threshold = config.get("threshold", 0.5)

    def generate_signal(self, features: FeatureFrame) -> OrderIntent:
        """Generate trading signal"""
        # Your logic here
        if features.some_condition > self.threshold:
            return OrderIntent.create(
                symbol_id=features.symbol_id,
                side=Side.BUY,
                order_type=OrderType.LIMIT,
                qty=0.1,
                price=features.mid_price
            )
        return None

    def on_fill(self, symbol_id: int, side: Side, qty: float):
        """Update position on fill"""
        # Position tracking here
        pass
```

## 🔒 Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email: security@example.com (replace with actual)
2. Provide detailed description
3. Include steps to reproduce
4. Suggest fix if possible

### Security Checklist

- [ ] No hardcoded credentials
- [ ] Input validation on external data
- [ ] Rate limiting on API endpoints
- [ ] Secrets stored in SOPS or OS keyring
- [ ] All services bound to 127.0.0.1 (not 0.0.0.0)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

**CRITICAL**: All contributions must use permissive licenses only:
- ✅ MIT, Apache 2.0, BSD-like
- ❌ GPL, AGPL, copyleft licenses

Always verify dependencies before adding them.

## 🙏 Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- GitHub contributors page

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: For private inquiries

## 🎓 Resources

- [Architecture Documentation](README.md#architecture)
- [Quick Start Guide](docs/QUICKSTART.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Strategy Examples](examples/README.md)

---

Thank you for contributing to SIGMAX! 🚀
