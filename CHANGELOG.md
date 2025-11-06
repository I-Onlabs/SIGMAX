# Changelog

All notable changes to SIGMAX will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pre-commit hooks configuration
- GitHub issue and PR templates
- pyproject.toml for modern Python packaging
- Development dependencies in requirements-dev.txt

## [0.1.0] - 2025-01-XX

### Added

**Core Trading Pipeline:**
- Market data ingestion service with CCXT WebSocket integration
- Single-writer L2 order book management
- Micro-window feature extraction engine (200-500ms)
- Pluggable signal modules (volatility, news, listings)
- Hybrid decision layer with L0-L5 architecture
  - L0: Safety constraints (spread, volatility limits)
  - L1: Reflex rules (mean reversion, momentum)
  - L2: ML placeholder (LightGBM/ONNX ready)
  - L5: Arbiter with confidence-based sizing
- Pre-trade risk engine with pure function checks
- Smart order router with rate limiting
- CEX execution gateway with paper trading mode

**Infrastructure:**
- Docker Compose orchestration for all services
- Postgres database for transactional data (OLTP)
- ClickHouse database for analytics (OLAP)
- Redis for caching and pub/sub
- Prometheus metrics collection
- Grafana dashboards
  - Trading metrics (orders, P&L, latency, signals)
  - System health (services, resources, errors)
- Service orchestration runner
- Database initialization scripts

**Testing & CI/CD:**
- Unit test framework with 100+ tests
- Integration test framework
- GitHub Actions CI/CD pipeline
- Automated testing on push/PR
- Code coverage reporting

**Documentation:**
- Comprehensive README with architecture overview
- Quick Start Guide (5-minute setup)
- Deployment Guide (VPS, Kubernetes, systemd)
- Contributing Guide with code standards and templates
- Strategy examples documentation

**Monitoring & Observability:**
- Nanosecond-precision timing with Clock abstraction
- Latency tracking for all pipeline stages
- Prometheus metrics for all services
- Grafana dashboards with SLO alerts
- Performance benchmarking tool
- System health checker
- Historical trade analysis tool

**Example Strategies:**
- Mean reversion (orderbook imbalance)
- Momentum (trend following with confirmation)
- Market making (dual-sided quoting with inventory management)
- Arbitrage (cross-exchange price detection)

**Developer Tools:**
- Enhanced Makefile with 30+ targets
- Performance benchmark script
- System health monitoring script
- Trade analysis script
- Grafana dashboard import script
- Pre-commit hooks for code quality

### Technical Highlights

- **Event-driven architecture**: ZeroMQ pub/sub for IPC
- **Low latency**: p50 < 10ms, p99 < 20ms tick-to-trade (Profile A)
- **Deterministic replay**: Clock abstraction for simulation
- **Pure function risk**: No side effects in risk checks
- **Zero legal risk**: All dependencies use permissive licenses (MIT, Apache 2.0, BSD)

### Security

- All services bound to 127.0.0.1 (localhost only)
- No hardcoded credentials
- SOPS-encrypted secrets support
- Comprehensive input validation
- Rate limiting on all endpoints

## [0.0.1] - 2025-01-XX (Initial Architecture)

### Added
- Project structure and initial architecture design
- Core schemas and data models
- Common utilities (logging, config, timing)
- Basic service templates

---

## Release Notes Format

### Types of Changes
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

### Version History
- **0.1.0**: First production-ready release with complete trading pipeline
- **0.0.1**: Initial architecture and project setup

---

## Upgrade Guide

### From 0.0.1 to 0.1.0
This is the first production release. No migration needed.

---

## Roadmap

See [README.md](README.md#-future-enhancements) for planned features.
