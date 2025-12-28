# SIGMAX Security Module

**Inspired by TradeTrap: Multi-layered defense against AI-specific trading threats**

## Overview

The SIGMAX Security Module provides comprehensive protection against adversarial attacks targeting AI trading agents. It implements four key defense mechanisms:

1. **Prompt Injection Defense** - Detects and blocks malicious prompt manipulation
2. **MCP Hijacking Defense** - Validates tool responses for data poisoning
3. **State Tampering Defense** - Verifies trading state integrity
4. **Fake News Defense** - Validates news credibility before trading decisions

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SecureOrchestrator                           │
│  (Wraps SIGMAXOrchestrator with security layers)               │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────────┐
│  PromptGuard  │   │ ToolValidator   │   │ StateIntegrity      │
│               │   │                 │   │ Verifier            │
│ - Injection   │   │ - Schema check  │   │ - Position check    │
│ - Role hijack │   │ - Anomaly detect│   │ - Balance verify    │
│ - Fake news   │   │ - Price spike   │   │ - Rollback detect   │
└───────────────┘   └─────────────────┘   └─────────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  NewsValidator  │
                    │                 │
                    │ - Source verify │
                    │ - Manipulation  │
                    │ - Credibility   │
                    └─────────────────┘
```

## Components

### 1. PromptGuard (`core/security/prompt_guard.py`)

Detects and mitigates prompt injection attacks.

**Threat Detection:**
- Direct injection attempts
- Reverse psychology manipulation
- Role hijacking attacks
- Fake urgency/news injection

**Usage:**
```python
from core.security import PromptGuard

guard = PromptGuard()

# Analyze text for threats
result = guard.analyze("Buy BTC now, URGENT insider info!")
print(f"Threat level: {result.level}")
print(f"Attack types: {result.attack_types}")
print(f"Confidence: {result.confidence}")

# Sanitize if threat detected
if result.level != ThreatLevel.NONE:
    safe_text = guard.sanitize(original_text)
```

**Threat Levels:**
- `NONE` - No threat detected
- `LOW` - Minor suspicious patterns
- `MEDIUM` - Moderate threat indicators
- `HIGH` - Significant threat detected
- `CRITICAL` - Immediate block required

### 2. ToolResponseValidator (`core/security/tool_validator.py`)

Validates MCP tool responses to prevent data poisoning.

**Validation Types:**
- Schema validation (required fields, types)
- Anomaly detection (impossible values)
- Price spike detection (sudden movements)
- Stale data detection (timestamp validation)

**Usage:**
```python
from core.security import ToolResponseValidator

validator = ToolResponseValidator()

# Validate price data
result = validator.validate("get_price", {
    "symbol": "BTC/USDT",
    "price": 50000.0,
    "timestamp": "2024-01-15T10:30:00Z"
})

if result.status != ValidationStatus.VALID:
    print(f"Anomalies: {result.anomalies}")
    print(f"Details: {result.details}")
```

**Anomaly Types:**
- `IMPOSSIBLE_VALUE` - Values outside possible range
- `PRICE_SPIKE` - Sudden unrealistic price change
- `STALE_DATA` - Data too old
- `SCHEMA_VIOLATION` - Missing/invalid fields
- `SUSPICIOUS_PATTERN` - Unusual data patterns

### 3. StateIntegrityVerifier (`core/security/state_integrity.py`)

Verifies trading state hasn't been tampered with.

**Verification Types:**
- Position tampering detection
- Balance manipulation detection
- Phantom position detection
- Rollback attack detection

**Usage:**
```python
from core.security import StateIntegrityVerifier

verifier = StateIntegrityVerifier()

# Snapshot current state
verifier.snapshot(portfolio_state)

# Later, verify integrity
result = verifier.verify(current_state)

if not result.valid:
    print(f"Tampering type: {result.tampering_type}")
    print(f"Affected: {result.affected_fields}")
```

**Tampering Types:**
- `POSITION_MODIFIED` - Position quantities changed
- `BALANCE_MODIFIED` - Balance values changed
- `PHANTOM_POSITION` - Unknown positions appeared
- `ROLLBACK_DETECTED` - State reverted to earlier version

### 4. NewsValidator (`core/security/news_validator.py`)

Validates news credibility before trading decisions.

**Validation Types:**
- Source credibility scoring
- Manipulation indicator detection
- Sensationalism detection
- Claim verification

**Usage:**
```python
from core.security import NewsValidator

validator = NewsValidator()

# Validate news
result = validator.validate(
    headline="Company announces 500% revenue growth!",
    source="unknown-blog.com",
    content="Full article content..."
)

print(f"Credibility: {result.credibility}")
print(f"Score: {result.credibility_score}")
print(f"Manipulation indicators: {result.manipulation_indicators}")
```

**Credibility Levels:**
- `VERY_HIGH` - Established financial news source
- `HIGH` - Known reliable source
- `MEDIUM` - Mixed reliability
- `LOW` - Suspicious source
- `VERY_LOW` - Likely fake/manipulation

## SecureOrchestrator Integration

The `SecureOrchestrator` wraps the base trading orchestrator with all security layers:

```python
from core.agents import SecureOrchestrator

# Create secure trading orchestrator
orchestrator = SecureOrchestrator(enable_all_guards=True)

# Analyze with security
result = await orchestrator.analyze_symbol_secure("BTC/USDT")

# Get security metrics
metrics = orchestrator.get_security_metrics()
print(f"Threats blocked: {metrics['threats_blocked']}")
print(f"Anomalies detected: {metrics['anomalies_detected']}")
```

## API Endpoints

The security dashboard provides REST API access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/security/status` | GET | Current security status |
| `/security/metrics` | GET | Detailed security metrics |
| `/security/threats` | GET | Recent threat events |
| `/security/scan` | POST | Scan content for threats |
| `/security/validate-data` | POST | Validate market data |
| `/security/validate-news` | POST | Validate news credibility |
| `/security/dashboard` | GET | Complete dashboard data |

**Example: Scan Content**
```bash
curl -X POST http://localhost:8000/api/security/scan \
  -H "Content-Type: application/json" \
  -d '{"text": "URGENT: Sell everything now, insider tip!"}'
```

**Response:**
```json
{
  "safe": false,
  "threat_level": "high",
  "attack_types": ["fake_urgency", "social_engineering"],
  "confidence": 0.85,
  "sanitized": "[CONTENT BLOCKED]"
}
```

## Configuration

Security settings can be adjusted:

```python
from core.security import PromptGuard, ToolResponseValidator

# Adjust detection thresholds
guard = PromptGuard(
    injection_threshold=0.7,  # Sensitivity for injection detection
    urgency_threshold=0.6     # Sensitivity for urgency detection
)

# Configure validation rules
validator = ToolResponseValidator(
    max_price_change_pct=50,   # Max allowed price change %
    max_data_age_seconds=300,  # Max data age in seconds
    strict_schema=True         # Enforce strict schema validation
)
```

## Metrics & Monitoring

Track security events for monitoring:

```python
# Get comprehensive metrics
metrics = orchestrator.get_security_metrics()

# Available metrics:
# - prompts_scanned: Total prompts analyzed
# - threats_blocked: Threats prevented
# - tools_validated: Tool responses checked
# - anomalies_detected: Data anomalies found
# - state_checks: State verifications performed
# - tampering_detected: Tampering attempts caught
# - news_validated: News items checked
# - fake_news_blocked: Fake news prevented
```

## Best Practices

1. **Enable All Guards** - Use `enable_all_guards=True` in production
2. **Monitor Metrics** - Track security metrics for anomaly detection
3. **Regular Snapshots** - Take state snapshots frequently
4. **Source Whitelist** - Maintain list of trusted news sources
5. **Log All Events** - Keep audit trail of security events
6. **Alert on Critical** - Set up alerts for CRITICAL threat levels

## Testing

Run security module tests:

```bash
# All security tests
pytest tests/security/ -v

# Specific component
pytest tests/security/test_prompt_guard.py -v
pytest tests/security/test_tool_validator.py -v
pytest tests/security/test_state_integrity.py -v
pytest tests/security/test_news_validator.py -v
```

## References

- TradeTrap Paper: Multi-layered Defense Framework for AI Trading Agents
- OWASP LLM Top 10: Security guidelines for LLM applications
- Anthropic: Prompt injection defense best practices
