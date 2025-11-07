"""
Hybrid Decision Layer (L0-L5)

Implements the "LLM under control" architecture:
- L0: Safety constraints (price/quantity bands, min quote life)
- L1: Reflex rules (inventory skew, spread/vol caps, cooldowns)
- L2: Micro-ML (LightGBM for price/size predictions)
- L3: Controller-ML (decides LLM invocation)
- L4: Agentic LLM (optional, advisory only)
- L5: Arbiter (mixes outputs, emits OrderIntent)
"""
