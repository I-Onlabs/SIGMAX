# SIGMAX SDK Development Guide

## Setup Development Environment

### Prerequisites

- Python 3.11 or higher
- pip and setuptools
- virtualenv (recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/I-Onlabs/SIGMAX.git
   cd SIGMAX/sdk/python
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   make dev
   # or manually:
   pip install -e ".[dev]"
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_client.py -v

# Run with coverage report
pytest --cov=sigmax_sdk --cov-report=html

# Run specific test
pytest tests/test_client.py::test_get_status_success -v
```

### Code Quality

```bash
# Format code
make format

# Run linter
make lint

# Type checking
make type-check

# Run all checks
make check
```

### Building Package

```bash
# Build distribution packages
make build

# This creates:
# - dist/sigmax_sdk-1.0.0-py3-none-any.whl
# - dist/sigmax_sdk-1.0.0.tar.gz
```

## Project Structure

```
sdk/python/
├── sigmax_sdk/           # Main package
│   ├── __init__.py       # Package exports
│   ├── client.py         # API client
│   ├── models.py         # Pydantic models
│   ├── exceptions.py     # Exception hierarchy
│   ├── types.py          # Type definitions
│   └── py.typed          # Type hints marker
├── tests/                # Unit tests
│   ├── __init__.py
│   └── test_client.py
├── examples/             # Usage examples
│   ├── basic_usage.py
│   ├── streaming.py
│   ├── async_operations.py
│   └── error_handling.py
├── pyproject.toml        # Package configuration
├── setup.py              # Setup script
├── README.md             # User documentation
├── DEVELOPMENT.md        # This file
├── Makefile              # Development commands
└── .gitignore
```

## Code Standards

### Type Hints

All public functions must have complete type hints:

```python
async def propose_trade(
    self,
    symbol: str,
    risk_profile: RiskProfile = RiskProfile.CONSERVATIVE,
    mode: TradeMode = TradeMode.PAPER,
    size: Optional[float] = None,
) -> TradeProposal:
    """Docstring here."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def function(param1: str, param2: int) -> bool:
    """
    Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When value is invalid
        SigmaxAPIError: On API errors

    Example:
        ```python
        result = function("test", 42)
        ```
    """
    ...
```

### Error Handling

- Use specific exception types from `exceptions.py`
- Always catch and re-raise with context
- Provide meaningful error messages

```python
try:
    response = await client.get(url)
except httpx.TimeoutException as e:
    raise SigmaxTimeoutError(f"Request timeout: {e}") from e
except httpx.ConnectError as e:
    raise SigmaxConnectionError(f"Connection failed: {e}") from e
```

### Async Patterns

- All I/O operations must be async
- Use `async with` for resource management
- Prefer `asyncio.gather()` for concurrent operations

```python
async with SigmaxClient() as client:
    # Concurrent operations
    results = await asyncio.gather(
        client.analyze("BTC/USDT"),
        client.analyze("ETH/USDT"),
        return_exceptions=True,
    )
```

## Testing Guidelines

### Unit Tests

- Test all public methods
- Mock HTTP responses with `pytest-httpx`
- Test error conditions
- Aim for >90% coverage

```python
@pytest.mark.asyncio
async def test_get_status_success(
    client: SigmaxClient,
    httpx_mock: HTTPXMock,
) -> None:
    """Test successful status retrieval."""
    httpx_mock.add_response(
        url="http://test-api/api/status",
        json={"status": "online", ...},
    )

    status = await client.get_status()
    assert status.status == "online"
```

### Integration Tests

For integration tests (not included in SDK):

```python
@pytest.mark.integration
async def test_real_api():
    """Test against real API."""
    async with SigmaxClient() as client:
        status = await client.get_status()
        assert status.api_health is True
```

## Release Process

### Version Bumping

1. Update version in `pyproject.toml`
2. Update version in `sigmax_sdk/__init__.py`
3. Update CHANGELOG.md
4. Commit changes

### Building Release

```bash
# Clean old builds
make clean

# Run all checks
make check

# Build distribution
make build

# Check build artifacts
ls -lh dist/
```

### Publishing to PyPI

```bash
# Install twine (if not already)
pip install twine

# Upload to TestPyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ sigmax-sdk

# If all looks good, upload to PyPI
make publish
# or manually:
python -m twine upload dist/*
```

### Post-Release

1. Create GitHub release with tag
2. Update documentation
3. Announce release

## Troubleshooting

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .

# Check installation
pip list | grep sigmax
```

### Type Checking Failures

```bash
# Install type stubs
pip install types-httpx

# Run with verbose output
mypy sigmax_sdk --show-error-codes
```

### Test Failures

```bash
# Run with more verbosity
pytest -vv --tb=long

# Run specific test with debugging
pytest tests/test_client.py::test_name -v -s
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and checks (`make check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Pull Request Guidelines

- Include tests for new features
- Update documentation
- Follow code standards
- Add entry to CHANGELOG.md
- Ensure all CI checks pass

## Resources

- [SIGMAX Main Repository](https://github.com/I-Onlabs/SIGMAX)
- [Python Packaging Guide](https://packaging.python.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [httpx Documentation](https://www.python-httpx.org/)
- [pytest Documentation](https://docs.pytest.org/)

## Support

- GitHub Issues: https://github.com/I-Onlabs/SIGMAX/issues
- Discussions: https://github.com/I-Onlabs/SIGMAX/discussions
