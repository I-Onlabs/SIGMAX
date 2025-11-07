# SIGMAX Trading Policies
# Deploy to OPA server for policy-as-code compliance enforcement

package trading

# Default policies
policies := {
    "max_position_size": 15,
    "max_leverage": 1,
    "max_daily_loss": 10,
    "allowed_assets": [
        "BTC/USDT",
        "ETH/USDT",
        "SOL/USDT",
        "BNB/USDT",
        "AVAX/USDT",
        "MATIC/USDT",
        "DOT/USDT",
        "LINK/USDT"
    ],
    "blacklisted_assets": [],
    "risk_limits": {
        "conservative": {
            "max_position_pct": 10,
            "max_correlation": 0.7,
            "min_liquidity_score": 60
        },
        "balanced": {
            "max_position_pct": 15,
            "max_correlation": 0.8,
            "min_liquidity_score": 50
        },
        "aggressive": {
            "max_position_pct": 25,
            "max_correlation": 0.9,
            "min_liquidity_score": 40
        }
    }
}

# Main allow rule - trade is allowed if no violations
allow := {
    "allow": count(violations) == 0,
    "reason": reason,
    "violations": violations
}

# Collect all violations
violations[msg] {
    input.trade.size > policies.max_position_size
    msg := sprintf("Position size %.2f exceeds limit %.2f", [input.trade.size, policies.max_position_size])
}

violations[msg] {
    input.trade.leverage > policies.max_leverage
    msg := sprintf("Leverage %.1f exceeds limit %.1f", [input.trade.leverage, policies.max_leverage])
}

violations[msg] {
    policies.blacklisted_assets[_] == input.trade.symbol
    msg := sprintf("Asset %s is blacklisted", [input.trade.symbol])
}

violations[msg] {
    count(policies.allowed_assets) > 0
    not asset_in_whitelist
    msg := sprintf("Asset %s not in whitelist", [input.trade.symbol])
}

violations[msg] {
    limits := policies.risk_limits[input.risk_profile]
    input.trade.position_pct > limits.max_position_pct
    msg := sprintf("Position %.1f%% exceeds %s limit %.1f%%", [
        input.trade.position_pct,
        input.risk_profile,
        limits.max_position_pct
    ])
}

# Helper rules
asset_in_whitelist {
    policies.allowed_assets[_] == input.trade.symbol
}

reason := "All compliance checks passed" {
    count(violations) == 0
}

reason := sprintf("%d violation(s) found", [count(violations)]) {
    count(violations) > 0
}

# Risk profile validation
valid_risk_profiles := ["conservative", "balanced", "aggressive"]

default risk_profile_valid := false

risk_profile_valid {
    valid_risk_profiles[_] == input.risk_profile
}

# Advanced rules can be added here:
# - Time-based trading restrictions
# - Correlation limits
# - Liquidity requirements
# - Market condition filters
# - Circuit breakers
