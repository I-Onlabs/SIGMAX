# SIGMAX Safety & Risk Management

## Philosophy

**Safety is NOT optional. Every design decision prioritizes capital preservation over profit maximization.**

SIGMAX operates under a "zero-trust" model where every action is validated, logged, and can be audited.

## Risk Limits (Phase 0: Paper Trading)

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Total Capital** | $50 | Small enough to limit damage, large enough to test |
| **Max Position Size** | $10-15 | Diversification across 3-5 trades |
| **Stop Loss** | -1.5% | Tight stops for capital preservation |
| **Daily Loss Limit** | $10 | Prevents runaway losses |
| **Max Open Trades** | 3 | Focus over diversification |
| **Leverage** | 1x | No leverage until proven safe |
| **Allowed Assets** | BTC, ETH, SOL | Liquid majors only |

## Auto-Pause Triggers

SIGMAX automatically pauses trading when:

### 1. Loss-Based Triggers

- **3 consecutive losses**: Circuit breaker
- **Daily loss > $10**: Capital preservation
- **Position drawdown > 5%**: Risk of cascade

### 2. System Health Triggers

- **API error burst** (>5 errors/min): Exchange connectivity
- **Memory usage > 8GB**: System stability
- **Latency > 2s**: Execution quality
- **Missing heartbeat** (>30s): Core failure

### 3. Market Condition Triggers

- **Sentiment drop** (<-0.3): High fear
- **Volatility spike** (>2x ATR): Unstable markets
- **Liquidity drop** (<50% normal): Slippage risk
- **MEV detected**: Sandwich/frontrun attempt

### 4. Compliance Triggers

- **RAG mismatch** (>5%): Hallucination risk
- **Privacy breach**: PII leak detected
- **Collusion pattern**: Coordination signals
- **Blacklist hit**: Restricted asset

## Two-Man Rule

Critical actions require confirmation:

| Action | Requires |
|--------|----------|
| Increase leverage | Manual approval + 2FA |
| Remove risk cap | Justification + review |
| Override policy | Admin access + audit log |
| Emergency withdraw | Two independent approvals |
| Strategy change | Testing + validation |

## Policy Validation (OPA)

Every trade passes through Open Policy Agent checks:

```rego
package sigmax.trading

# Deny if position size exceeds limit
deny[msg] {
    input.size > 15
    msg := "Position size exceeds $15 limit"
}

# Deny if total exposure exceeds cap
deny[msg] {
    sum(input.open_positions) + input.size > 50
    msg := "Total exposure would exceed $50"
}

# Deny if asset blacklisted
deny[msg] {
    input.symbol == blacklist[_]
    msg := sprintf("Asset %v is blacklisted", [input.symbol])
}

# Deny if stop loss not set
deny[msg] {
    not input.stop_loss
    msg := "Stop loss must be set"
}
```

## Audit Trail (ZK-SNARKs)

Every decision is logged with:

1. **Decision inputs**: Market data, agent arguments, scores
2. **Decision output**: Action, confidence, reasoning
3. **Cryptographic proof**: ZK-SNARK for immutability
4. **Timestamp**: UTC with nanosecond precision
5. **Agent states**: Snapshots of agent memory

Logs are:
- **Immutable**: Cannot be altered without breaking proof
- **Verifiable**: Anyone can verify authenticity
- **Private**: Sensitive data stays encrypted
- **Auditable**: Regulators can inspect on demand

## Privacy Protections

### PII Detection

Regex patterns for:
- Email addresses
- Phone numbers
- SSNs
- Credit cards
- API keys
- Private keys
- Wallet addresses (selectively)

### Anti-Collusion

Detects:
- Coordination keywords ("pump together", "insider")
- Unusual message patterns
- Time-synchronized actions
- Shared secrets in plaintext

### Data Minimization

- No PII collected by default
- Logs anonymized after 90 days
- Right to erasure honored (GDPR)
- Encryption at rest and in transit

## Incident Response

### Levels

| Level | Trigger | Response |
|-------|---------|----------|
| **INFO** | Normal operation | Log only |
| **WARN** | Approaching limit | Alert user |
| **ERROR** | Limit breached | Auto-pause |
| **CRITICAL** | System failure | Emergency stop + alert |

### Emergency Stop Procedure

1. **Trigger**: Manual panic button or critical error
2. **Actions**:
   - Close all open positions (market orders)
   - Cancel pending orders
   - Pause all strategies
   - Notify user (Telegram + email)
   - Generate incident report
3. **Recovery**:
   - Review logs and incident report
   - Identify root cause
   - Apply fixes
   - Test in paper mode
   - Resume only after approval

## Compliance

### EU AI Act

- **Transparency**: Decision reasoning always visible
- **Human oversight**: Manual approval for critical actions
- **Bias detection**: Monitor for discriminatory patterns
- **Documentation**: Architecture and training data described

### SEC Regulations

- **Record keeping**: All trades logged for 7 years
- **Market manipulation**: No wash trading, spoofing, or frontrunning
- **Disclosure**: Risks clearly communicated
- **Accredited investors**: Live trading requires verification (future)

### KYC/AML

- **Identity verification**: Required for live trading >$1000
- **Source of funds**: Documentation for large deposits
- **Suspicious activity**: Automatic flagging and reporting
- **Sanctions screening**: OFAC list checked

## Testing & Validation

### Pre-Deployment Checklist

- [ ] All unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Backtest shows positive Sharpe >1.0
- [ ] Max drawdown < 10%
- [ ] Paper trading for 14 days minimum
- [ ] Safety gates tested (simulated failures)
- [ ] Manual review of agent debates
- [ ] Disaster recovery plan validated

### Continuous Monitoring

- **Real-time dashboards**: Grafana with alerts
- **Daily reports**: Telegram snapshot (PnL, risk, trades)
- **Weekly tearsheets**: PDF with full analysis
- **Monthly reviews**: Strategy performance audit

## Phased Rollout

### Phase 0: Paper Trading (Days 1-14)

- **Capital**: Virtual $50
- **Assets**: BTC/USDT only
- **Goal**: Prove safety mechanisms work
- **Success**: 100% of safety gates triggered correctly

### Phase 1: Live $50 (Days 15-30)

- **Capital**: Real $50 (sub-account)
- **Assets**: BTC, ETH
- **Leverage**: 1x only
- **Goal**: Real-world validation
- **Success**: No losses beyond risk caps

### Phase 2: Expand (Days 31-60)

- **Capital**: Up to $200
- **Assets**: Add SOL, MATIC, ARB
- **Leverage**: Up to 2x (with approval)
- **Features**: Narrative trading, arbitrage
- **Goal**: Scale proven strategies

### Phase 3: Community (Q2 2025)

- **Multi-user**: Isolated accounts
- **Strategy marketplace**: Share and earn
- **Advanced features**: HFT, cross-chain
- **Goal**: Decentralized hedge fund

## Red Lines (Never Cross)

1. **Never** trade with money you can't afford to lose
2. **Never** disable safety rails in production
3. **Never** use leverage without proven edge
4. **Never** trust external data without verification
5. **Never** skip backtest validation
6. **Never** ignore auto-pause triggers
7. **Never** commit secrets to git
8. **Never** expose API keys in logs
9. **Never** trade blacklisted assets
10. **Never** manipulate markets

## Contact in Emergency

- **Email**: security@sigmax.dev (future)
- **Telegram**: @SIGMAXBot
- **GitHub Issues**: https://github.com/yourusername/SIGMAX/issues
- **Discord**: #incidents channel (future)

---

**Remember**: It's better to miss a trade than to lose capital. When in doubt, PAUSE.
