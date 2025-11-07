"""
Pre-Trade Risk Engine

Performs pre-trade risk checks on all OrderIntent messages:
- Position limits
- Notional limits
- Price band checks
- Rate limiting
- Venue-specific quotas

All checks are pure functions for deterministic replay.
"""
