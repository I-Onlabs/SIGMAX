# Security Policy

## Supported Versions

We actively support the following versions of SIGMAX with security updates:

| Version | Supported          | Status      |
| ------- | ------------------ | ----------- |
| 1.0.x   | :white_check_mark: | Current     |
| < 1.0   | :x:                | End of Life |

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues.**

### Responsible Disclosure

We take security seriously and appreciate your efforts to responsibly disclose your findings. Please follow these steps:

1. **Email us directly**: Send details to [security@sigmax.dev](mailto:security@sigmax.dev)
2. **Do not disclose publicly** until we've had a chance to address the issue
3. **Provide detailed information** (see template below)
4. **Allow reasonable time** for us to respond (we aim for 48 hours)

### What to Include in Your Report

Please include as much of the following information as possible:

```
Subject: [SECURITY] Brief description of vulnerability

## Vulnerability Details
- Type of issue (e.g., SQL injection, XSS, authentication bypass)
- Affected component(s) and version(s)
- Step-by-step reproduction instructions
- Proof of concept or exploit code (if available)
- Potential impact assessment

## Your Environment
- SIGMAX version
- Operating system
- Python version
- Deployment method (Docker, manual, etc.)

## Additional Context
- Any mitigating factors
- Suggested fix (optional)
- Whether you discovered this through automated scanning or manual testing
```

### Response Timeline

| Timeline | Action |
|----------|--------|
| < 48 hours | Initial response acknowledging receipt |
| < 7 days | Preliminary assessment and severity classification |
| < 30 days | Fix developed and tested |
| < 45 days | Patch released and security advisory published |

We will keep you informed throughout the process and credit you in the security advisory (unless you prefer to remain anonymous).

## Security Best Practices

### For Users

When deploying SIGMAX, please follow these security best practices:

#### 1. **Secrets Management**

**Never commit secrets to git:**
```bash
# ❌ BAD
OPENAI_API_KEY=sk-abc123xyz  # in .env committed to git

# ✅ GOOD
# Use environment variables or HashiCorp Vault
export OPENAI_API_KEY=sk-abc123xyz  # in shell only
```

**Use strong, unique passwords:**
```bash
# Generate strong passwords
openssl rand -base64 32

# Required environment variables for production:
POSTGRES_PASSWORD=<strong-password-here>
GRAFANA_ADMIN_PASSWORD=<strong-password-here>
REDIS_PASSWORD=<strong-password-here>
```

**Enable HashiCorp Vault for production:**
```bash
# In .env
USE_VAULT=true
VAULT_ADDR=https://vault.your-domain.com
VAULT_TOKEN=<vault-token>
```

#### 2. **Network Security**

**Use HTTPS/TLS in production:**
```bash
# Configure reverse proxy (nginx example)
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    # ...
}
```

**Configure firewall:**
```bash
# Only expose necessary ports
sudo ufw allow 443/tcp  # HTTPS
sudo ufw deny 8000/tcp  # Block direct API access
sudo ufw deny 5432/tcp  # Block PostgreSQL
sudo ufw deny 6379/tcp  # Block Redis
```

**Set ALLOWED_HOSTS:**
```bash
# In .env for production
ENVIRONMENT=production
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com
```

#### 3. **API Security**

**Set a strong API key:**
```bash
# Generate secure API key
SIGMAX_API_KEY=$(openssl rand -hex 32)

# In client requests:
curl -H "Authorization: Bearer your-api-key" https://api.yourdomain.com/api/v1/status
```

**Monitor rate limits:**
```bash
# Default: 100 requests/minute
# Adjust in .env if needed
RATE_LIMIT_PER_MINUTE=100
```

#### 4. **Docker Security**

**Run as non-root user** (already configured):
```dockerfile
# Our Dockerfile uses non-root user
USER sigmax
```

**Scan images for vulnerabilities:**
```bash
# Scan Docker images
docker scan sigmax-api:latest

# Or use Trivy
trivy image sigmax-api:latest
```

**Keep images updated:**
```bash
# Rebuild regularly
docker-compose build --pull
```

#### 5. **Database Security**

**Restrict database access:**
```yaml
# docker-compose.yml
postgres:
  environment:
    POSTGRES_HOST_AUTH_METHOD: scram-sha-256  # Use strong auth
  # Don't expose ports externally in production
  # ports:
  #   - "5432:5432"  # Comment out
```

**Enable SSL for database connections:**
```bash
# PostgreSQL with SSL
POSTGRES_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

**Regular backups:**
```bash
# Automated daily backups
0 2 * * * docker exec sigmax-postgres pg_dump -U sigmax sigmax > /backups/sigmax_$(date +\%Y\%m\%d).sql
```

#### 6. **Monitoring & Alerts**

**Enable security monitoring:**
```bash
# In .env
SENTRY_DSN=https://your-sentry-dsn
OBSERVABILITY_ENABLED=true
```

**Set up alerts for suspicious activity:**
- Multiple failed authentication attempts
- Rate limit violations
- Unusual trading patterns
- API errors

#### 7. **Trading Security**

**Start with paper trading:**
```bash
# Always test in paper mode first
TRADING_MODE=paper
```

**Use testnet for crypto exchanges:**
```bash
TESTNET=true
EXCHANGE_TESTNET=true
```

**Set conservative risk limits:**
```bash
MAX_POSITION_SIZE=0.05  # 5% max per position
MAX_DAILY_LOSS=0.02     # 2% max daily loss
STOP_LOSS_PCT=1.5       # 1.5% stop loss
```

**Enable two-factor authentication on exchanges:**
- Always use 2FA/MFA on exchange accounts
- Use hardware security keys when possible
- Never share API keys

### For Developers

#### Secure Coding Practices

1. **Input Validation**
```python
# ✅ GOOD - Validate all inputs
from pydantic import BaseModel, validator

class TradeRequest(BaseModel):
    symbol: str
    quantity: float

    @validator('symbol')
    def validate_symbol(cls, v):
        if not re.match(r'^[A-Z]{3,6}/[A-Z]{3,6}$', v):
            raise ValueError('Invalid symbol format')
        return v
```

2. **SQL Injection Prevention**
```python
# ❌ BAD
cursor.execute(f"SELECT * FROM trades WHERE symbol = '{symbol}'")

# ✅ GOOD - Use parameterized queries
cursor.execute("SELECT * FROM trades WHERE symbol = %s", (symbol,))
```

3. **Authentication & Authorization**
```python
# ✅ GOOD - Always verify API keys
async def protected_endpoint(api_key: str = Depends(verify_api_key)):
    # Endpoint logic
    pass
```

4. **Secrets in Code**
```python
# ❌ BAD - Hardcoded secrets
api_key = "sk-abc123xyz"

# ✅ GOOD - Use secrets manager
from core.utils.secrets_manager import secrets_manager
api_key = secrets_manager.get_api_key("OPENAI")
```

5. **Error Handling**
```python
# ❌ BAD - Exposes internal details
except Exception as e:
    return {"error": str(e), "stack_trace": traceback.format_exc()}

# ✅ GOOD - Generic error messages
except Exception as e:
    logger.error(f"Internal error: {e}", exc_info=True)
    return {"error": "An internal error occurred"}
```

## Security Features

SIGMAX includes the following built-in security features:

### 1. **Rate Limiting**
- Prevents API abuse and DoS attacks
- Configurable per-endpoint limits
- Redis-backed for distributed systems

### 2. **API Key Authentication**
- Bearer token authentication
- Environment-based configuration
- Optional for development, required for production

### 3. **Secrets Management**
- HashiCorp Vault integration
- Secure credential storage
- Automatic fallback to environment variables

### 4. **CORS Protection**
- Configurable allowed origins
- Prevents unauthorized cross-origin requests

### 5. **Input Validation**
- Pydantic models for all API endpoints
- Type checking and validation
- Prevents injection attacks

### 6. **Audit Logging**
- All trading decisions logged
- Immutable audit trail
- ZK-SNARK proof framework

### 7. **Risk Management**
- Automatic pause triggers
- Position size limits
- Stop-loss enforcement
- Daily loss limits

### 8. **Two-Man Rule**
- Critical actions require confirmation
- Prevents accidental or malicious trades

## Known Security Considerations

### Trading Risks
- **Market Volatility**: Crypto markets are highly volatile
- **Exchange Risk**: Centralized exchanges can be hacked or go offline
- **Smart Contract Risk**: DeFi protocols may have bugs
- **MEV/Sandwich Attacks**: Frontrunning on DEXs
- **API Key Compromise**: Secure your exchange API keys

### Technical Limitations
- **Quantum Module**: Uses simulated quantum computing, not real quantum hardware
- **LLM Hallucinations**: AI agents may generate incorrect analysis
- **Data Quality**: Analysis quality depends on data source reliability
- **Network Latency**: WebSocket delays may affect real-time trading

## Compliance

SIGMAX is designed with the following compliance considerations:

- **EU AI Act**: Bias detection, transparency, human oversight
- **SEC Guidelines**: Trade logging, audit trails, disclosure
- **GDPR**: PII detection, data privacy controls
- **Financial Regulations**: Paper trading default, risk limits

## Security Audit Status

| Date | Auditor | Scope | Report |
|------|---------|-------|--------|
| TBD  | TBD     | Full codebase | Pending |

We plan to conduct a professional security audit before v2.0.0 release.

## Bug Bounty Program

**Status**: Coming soon

We plan to launch a bug bounty program for responsible security researchers. Details will be announced in Q2 2025.

**Potential rewards** (subject to severity):
- **Critical**: $500-$2,000
- **High**: $250-$500
- **Medium**: $100-$250
- **Low**: $50-$100

## Contact

- **Security Email**: security@sigmax.dev
- **General Email**: support@sigmax.dev
- **GitHub Issues**: https://github.com/I-Onlabs/SIGMAX/issues (for non-security issues only)
- **Discord**: https://discord.gg/sigmax

## Updates

This security policy was last updated on **2025-11-15**.

We review and update our security practices regularly. Check back for the latest information.

---

**Thank you for helping keep SIGMAX and its users safe!**
