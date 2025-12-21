# Changelog

All notable changes to the SIGMAX Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-21

### Added

- Initial release of SIGMAX Python SDK
- Async-first client implementation with `httpx`
- Server-Sent Events (SSE) streaming support
- Complete type safety with Pydantic models
- Comprehensive error handling with custom exception hierarchy
- Context manager support for automatic resource cleanup
- Full API coverage:
  - System status monitoring
  - Market analysis (sync and streaming)
  - Trade proposal management
  - Proposal approval and execution
- Pydantic models for all data structures:
  - `SystemStatus` - System health and metrics
  - `TradeProposal` - Trade proposal details
  - `AnalysisResult` - Market analysis results
  - `RiskProfile` - Risk level enumeration
  - `TradeMode` - Trading mode enumeration
  - `ProposalStatus` - Proposal status tracking
- Exception types:
  - `SigmaxError` - Base exception
  - `SigmaxAPIError` - API-level errors
  - `SigmaxAuthenticationError` - 401/403 errors
  - `SigmaxRateLimitError` - 429 rate limit
  - `SigmaxValidationError` - 400/422 validation
  - `SigmaxConnectionError` - Network errors
  - `SigmaxTimeoutError` - Timeout errors
- Comprehensive documentation:
  - README with quick start guide
  - API reference documentation
  - Development guide
  - Example scripts:
    - Basic usage
    - Streaming analysis
    - Async operations
    - Error handling
- Production-ready packaging:
  - PyPI-ready `pyproject.toml`
  - Type hints marker (`py.typed`)
  - Development dependencies
  - Testing with pytest and pytest-httpx
  - Code quality tools (black, ruff, mypy)
  - Makefile for common tasks

### Features

- **Async-First Design**: All operations are async for optimal performance
- **Type Safety**: Complete type hints with strict mypy compliance
- **Streaming Support**: Real-time updates via SSE
- **Error Recovery**: Automatic retry logic with exponential backoff
- **Resource Management**: Proper cleanup with context managers
- **Concurrent Operations**: Built-in support for parallel requests
- **Validation**: Pydantic-based request/response validation
- **Extensible**: Easy to extend with new endpoints

### Developer Experience

- Intuitive Pythonic API
- Comprehensive examples
- Full test coverage
- Development tooling (Makefile, pre-commit hooks)
- Strict type checking
- Formatted with black
- Linted with ruff

### Requirements

- Python >= 3.11
- httpx >= 0.27.0
- httpx-sse >= 0.4.0
- pydantic >= 2.0.0

---

## [Unreleased]

### Planned

- WebSocket support for real-time updates
- Historical data retrieval
- Performance metrics and monitoring
- Batch operations optimization
- Rate limit handling improvements
- Response caching
- CLI tool for quick testing

---

[1.0.0]: https://github.com/I-Onlabs/SIGMAX/releases/tag/sdk-v1.0.0
