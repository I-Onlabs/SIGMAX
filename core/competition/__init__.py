"""
SIGMAX Competition Module
Multi-model trading competition and benchmarking
"""

from .multi_model_arena import (
    CompetitionArena,
    ModelConfig,
    ModelProvider,
    StrategyType,
    LLMCompetitor,
    TradeDecision,
    ModelPerformance,
    PRESET_CONFIGS,
    create_default_arena
)

__all__ = [
    "CompetitionArena",
    "ModelConfig",
    "ModelProvider",
    "StrategyType",
    "LLMCompetitor",
    "TradeDecision",
    "ModelPerformance",
    "PRESET_CONFIGS",
    "create_default_arena"
]
