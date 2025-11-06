# SIGMAX Examples

This directory contains example scripts demonstrating how to use SIGMAX.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

Demonstrates core API functionality:
- Health checks
- System status
- Symbol analysis
- Agent debates
- Portfolio management
- Trade execution

**Usage:**
```bash
# Install dependencies
pip install httpx

# Set API key (optional)
export SIGMAX_API_KEY="your-api-key"

# Run example
python examples/basic_usage.py
```

### 2. WebSocket Client (`websocket_example.py`)

Real-time updates via WebSocket:
- Connection handling
- Status updates
- Trade notifications
- Alert messages

**Usage:**
```bash
# Install dependencies
pip install websockets

# Run example
python examples/websocket_example.py
```

## Requirements

```bash
pip install httpx websockets
```

## Configuration

Set these environment variables:

```bash
# API Configuration
export SIGMAX_API_URL="http://localhost:8000"
export SIGMAX_API_KEY="your-api-key-here"

# WebSocket Configuration
export SIGMAX_WS_URL="ws://localhost:8000/ws"
```

## More Examples Coming Soon

- Backtesting strategies
- Custom agent implementations
- Portfolio optimization
- Risk management
- Integration with external services

## Support

For more information, see:
- [API Reference](../docs/API_REFERENCE.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Troubleshooting](../docs/TROUBLESHOOTING.md)
