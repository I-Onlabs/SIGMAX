"""
SIGMAX Security Module - Adversarial Defense Layer
Inspired by TradeTrap's security testing patterns

Features:
- Prompt injection detection and mitigation
- Tool response validation (MCP hijacking defense)
- State integrity verification
- News source authenticity validation
"""

from .prompt_guard import (
    PromptGuard,
    SecurePromptWrapper,
    ThreatDetection,
    ThreatLevel,
    AttackType,
    SecurityPolicy
)

from .tool_validator import (
    ToolResponseValidator,
    SecureToolWrapper,
    ValidationResult,
    ValidationStatus,
    AnomalyType,
    ToolSchema
)

from .state_integrity import (
    StateIntegrityVerifier,
    IntegrityCheck,
    IntegrityStatus,
    TamperType,
    StateSnapshot
)

from .news_validator import (
    NewsValidator,
    NewsValidation,
    CredibilityLevel,
    ManipulationIndicator,
    SourceProfile
)

__all__ = [
    # Prompt Guard
    "PromptGuard",
    "SecurePromptWrapper",
    "ThreatDetection",
    "ThreatLevel",
    "AttackType",
    "SecurityPolicy",
    # Tool Validator
    "ToolResponseValidator",
    "SecureToolWrapper",
    "ValidationResult",
    "ValidationStatus",
    "AnomalyType",
    "ToolSchema",
    # State Integrity
    "StateIntegrityVerifier",
    "IntegrityCheck",
    "IntegrityStatus",
    "TamperType",
    "StateSnapshot",
    # News Validator
    "NewsValidator",
    "NewsValidation",
    "CredibilityLevel",
    "ManipulationIndicator",
    "SourceProfile"
]
