"""
Market Data Ingestion Service for CEX

Connects to centralized exchanges via CCXT and streams market data.
Handles:
- WebSocket subscriptions for real-time ticks
- Gap detection and recovery
- Normalization to internal schema
- Publishing to IPC (ZeroMQ/Aeron)
"""
