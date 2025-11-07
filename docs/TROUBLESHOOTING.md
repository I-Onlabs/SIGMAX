# SIGMAX Troubleshooting Guide

## Table of Contents
1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [API & Connectivity Issues](#api--connectivity-issues)
4. [Trading & Execution Issues](#trading--execution-issues)
5. [Performance Issues](#performance-issues)
6. [Database Issues](#database-issues)
7. [Agent & LLM Issues](#agent--llm-issues)
8. [UI & WebSocket Issues](#ui--websocket-issues)
9. [Docker & Container Issues](#docker--container-issues)
10. [Common Error Messages](#common-error-messages)

---

## Quick Diagnostics

### Health Check Script

```bash
#!/bin/bash
# Quick system health check

echo "=== SIGMAX Health Check ==="
echo

# Check services
echo "1. Checking Services..."
docker-compose ps 2>/dev/null || systemctl status sigmax-* 2>/dev/null

# Check API
echo -e "\n2. Checking API..."
curl -s http://localhost:8000/health | jq . || echo "❌ API not responding"

# Check database
echo -e "\n3. Checking PostgreSQL..."
pg_isready -h localhost -p 5432 && echo "✓ PostgreSQL OK" || echo "❌ PostgreSQL down"

# Check Redis
echo -e "\n4. Checking Redis..."
redis-cli ping 2>/dev/null && echo "✓ Redis OK" || echo "❌ Redis down"

# Check disk space
echo -e "\n5. Checking Disk Space..."
df -h / | tail -1

# Check memory
echo -e "\n6. Checking Memory..."
free -h | grep Mem

# Check logs for errors
echo -e "\n7. Recent Errors..."
tail -50 logs/sigmax.log | grep -i error | tail -5

echo -e "\n=== Health Check Complete ==="
```

Save as `health-check.sh` and run:
```bash
chmod +x health-check.sh
./health-check.sh
```

---

## Installation Issues

### Issue: `pip install` fails with dependency conflicts

**Symptoms:**
```
ERROR: Cannot install package-a and package-b because they have conflicting dependencies
```

**Solutions:**

1. **Use clean virtual environment:**
```bash
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

2. **Install in order:**
```bash
pip install numpy pandas  # Install base dependencies first
pip install -r requirements.txt
```

3. **Use pip resolver:**
```bash
pip install --use-deprecated=legacy-resolver -r requirements.txt
```

### Issue: Node.js build fails

**Symptoms:**
```
npm ERR! code ELIFECYCLE
npm ERR! errno 1
```

**Solutions:**

1. **Clear npm cache:**
```bash
cd ui/web
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

2. **Use correct Node version:**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install Node 20
nvm install 20
nvm use 20
npm install
```

### Issue: Permission denied errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

**Solutions:**

1. **Fix ownership:**
```bash
sudo chown -R $USER:$USER .
chmod -R u+w .
```

2. **Create required directories:**
```bash
mkdir -p logs reports/backtests reports/sessions
chmod 755 logs reports
```

---

## API & Connectivity Issues

### Issue: API returns 401 Unauthorized

**Symptoms:**
```json
{
  "detail": "Invalid or missing API key"
}
```

**Solutions:**

1. **Check API key configuration:**
```bash
# Verify .env file
cat .env | grep SIGMAX_API_KEY

# Generate new key if needed
echo "SIGMAX_API_KEY=$(openssl rand -hex 32)" >> .env
```

2. **Test with API key:**
```bash
API_KEY="your-key-here"
curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/status
```

3. **Disable API key for testing:**
```bash
# In .env - comment out or remove
# SIGMAX_API_KEY=...

# Restart API
docker-compose restart api
```

### Issue: 429 Too Many Requests

**Symptoms:**
```json
{
  "detail": "Rate limit exceeded. Retry after 60 seconds"
}
```

**Solutions:**

1. **Wait and retry** - Rate limits are per-minute

2. **Adjust rate limits** in `ui/api/main.py`:
```python
self.limits = {
    "default": (120, 60),  # 120 requests per 60 seconds
    "analyze": (20, 60),   # 20 requests per 60 seconds
    "trade": (10, 60),     # 10 requests per 60 seconds
}
```

3. **Use exponential backoff:**
```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
```

### Issue: CORS errors in browser

**Symptoms:**
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solutions:**

1. **Update CORS_ORIGINS:**
```bash
# In .env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

2. **Restart API:**
```bash
docker-compose restart api
```

### Issue: Connection refused

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solutions:**

1. **Check if service is running:**
```bash
# Check API
curl http://localhost:8000/health

# Check port binding
ss -tlnp | grep 8000
```

2. **Check firewall:**
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

3. **Verify host binding:**
```bash
# In ui/api/main.py, ensure:
uvicorn.run(app, host="0.0.0.0", port=8000)  # Not 127.0.0.1
```

---

## Trading & Execution Issues

### Issue: Trades not executing

**Symptoms:**
- Analysis completes but no trades execute
- Status shows "0 trades today"

**Diagnostic Steps:**

1. **Check trading mode:**
```bash
# Verify in .env
cat .env | grep TRADING_MODE
# Should be: TRADING_MODE=paper or TRADING_MODE=live
```

2. **Check logs:**
```bash
tail -f logs/sigmax.log | grep -i "trade\|execution"
```

3. **Verify orchestrator is running:**
```bash
# Check process
ps aux | grep "python.*main.py"

# Check logs
tail -100 logs/sigmax.log | grep orchestrator
```

**Solutions:**

1. **Enable trading:**
```bash
curl -X POST http://localhost:8000/api/control/start
```

2. **Check risk limits:**
```bash
# In .env, ensure limits allow trades
TOTAL_CAPITAL=50.0
MAX_POSITION_SIZE=15.0
MAX_DAILY_LOSS=10.0
```

3. **Test with lower confidence threshold** in `core/agents/orchestrator.py`:
```python
# Line ~411
if sentiment > 0.2 and confidence > 0.5:  # Lower thresholds for testing
    action = "buy"
```

### Issue: "Risk check failed" errors

**Symptoms:**
```
Decision: hold (reason: Failed risk check)
```

**Solutions:**

1. **Review risk policy** in `.env`:
```bash
# Increase limits temporarily for testing
TOTAL_CAPITAL=100.0
MAX_POSITION_SIZE=30.0
MAX_DAILY_LOSS=20.0
```

2. **Check compliance module:**
```bash
# View logs
grep -i "risk\|compliance" logs/sigmax.log | tail -20
```

3. **Disable specific checks for testing** (NOT FOR PRODUCTION):
```python
# In core/modules/compliance.py
async def validate_trade(self, trade):
    return {"approved": True, "reason": "Testing"}  # Temporary bypass
```

### Issue: Exchange API errors

**Symptoms:**
```
ExchangeError: Invalid API key
ccxt.errors.AuthenticationError
```

**Solutions:**

1. **Verify API credentials:**
```bash
# Check .env
cat .env | grep EXCHANGE_

# Ensure no extra spaces
EXCHANGE_API_KEY=your_key_here
EXCHANGE_SECRET_KEY=your_secret_here
```

2. **Test connection:**
```python
import ccxt

exchange = ccxt.binance({
    'apiKey': 'your_key',
    'secret': 'your_secret',
    'enableRateLimit': True,
})

# Test
print(exchange.fetch_balance())
```

3. **Use testnet/sandbox:**
```bash
EXCHANGE_SANDBOX=true
```

---

## Performance Issues

### Issue: Slow API responses

**Symptoms:**
- Requests take >5 seconds
- UI feels sluggish
- Timeout errors

**Diagnostic Steps:**

1. **Check API metrics:**
```bash
curl http://localhost:8000/metrics | jq '.api'
```

2. **Check system resources:**
```bash
# CPU usage
top -b -n 1 | head -20

# Memory
free -h

# Disk I/O
iostat -x 1 3
```

3. **Check database performance:**
```sql
-- In psql
SELECT * FROM pg_stat_activity WHERE state = 'active';
SELECT * FROM pg_stat_user_tables;
```

**Solutions:**

1. **Add database indexes:**
```sql
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_status ON trades(status);
```

2. **Enable caching:**
```bash
# In .env
CACHE_ENABLED=true
CACHE_TTL=300
```

3. **Scale API instances:**
```bash
# In docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
```

4. **Optimize queries:**
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10
)
```

### Issue: High memory usage

**Symptoms:**
```
MemoryError: Unable to allocate memory
System freezing
```

**Solutions:**

1. **Limit data retention:**
```python
# In config
MAX_HISTORY_DAYS = 30
CLEANUP_OLD_DATA = True
```

2. **Reduce batch sizes:**
```python
BATCH_SIZE = 100  # Instead of 1000
CHUNK_SIZE = 50
```

3. **Enable garbage collection:**
```python
import gc
gc.collect()  # Force cleanup
```

4. **Increase swap (Linux):**
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: CPU at 100%

**Symptoms:**
- System unresponsive
- Processes taking forever

**Solutions:**

1. **Identify culprit:**
```bash
top -H -p $(pgrep -f sigmax)
```

2. **Reduce parallel processing:**
```python
# In config
MAX_WORKERS = 4  # Instead of cpu_count()
PARALLEL_REQUESTS = 2
```

3. **Disable intensive features:**
```bash
# In .env
QUANTUM_ENABLED=false  # Quantum optimization is CPU-intensive
FEATURE_ARBITRAGE=false
```

---

## Database Issues

### Issue: PostgreSQL connection failed

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

1. **Check PostgreSQL status:**
```bash
sudo systemctl status postgresql
# or
docker-compose ps postgres
```

2. **Verify connection parameters:**
```bash
# Test connection
psql -h localhost -U sigmax -d sigmax

# Check pg_hba.conf
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v "^#"
```

3. **Reset PostgreSQL:**
```bash
# Docker
docker-compose restart postgres

# System
sudo systemctl restart postgresql
```

4. **Check disk space:**
```bash
df -h /var/lib/postgresql
```

### Issue: Database locked

**Symptoms:**
```
database is locked
```

**Solutions:**

1. **Kill blocking queries:**
```sql
-- Find blocking queries
SELECT pid, query, state, wait_event_type
FROM pg_stat_activity
WHERE state = 'active';

-- Kill specific query
SELECT pg_terminate_backend(PID);
```

2. **Restart database:**
```bash
docker-compose restart postgres
```

### Issue: Redis connection timeout

**Symptoms:**
```
redis.exceptions.ConnectionError: Connection timeout
```

**Solutions:**

1. **Check Redis:**
```bash
redis-cli ping
# Should return: PONG
```

2. **Restart Redis:**
```bash
docker-compose restart redis
```

3. **Clear Redis data (if corrupted):**
```bash
redis-cli FLUSHALL
```

---

## Agent & LLM Issues

### Issue: LLM not responding

**Symptoms:**
```
LLM timeout
No response from model
```

**Solutions:**

1. **Check LLM configuration:**
```bash
# Verify API key
cat .env | grep -E "OPENAI|ANTHROPIC|OLLAMA"
```

2. **Test LLM connection:**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
print(llm.invoke("Hello, test"))
```

3. **Switch to local LLM:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama3

# Update .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

4. **Increase timeout:**
```python
# In core/llm/factory.py
llm = ChatOpenAI(
    request_timeout=120,  # 2 minutes
    max_retries=3
)
```

### Issue: Agent debate loop never ends

**Symptoms:**
- Analysis takes >5 minutes
- Logs show repeated agent calls

**Solutions:**

1. **Check max iterations:**
```python
# In orchestrator.py
initial_state = {
    ...
    "max_iterations": 1  # Limit to 1 iteration for faster results
}
```

2. **Add timeout:**
```python
# Wrap analysis with timeout
import asyncio

try:
    result = await asyncio.wait_for(
        orchestrator.analyze_symbol(symbol),
        timeout=60.0  # 60 seconds max
    )
except asyncio.TimeoutError:
    logger.error("Analysis timed out")
```

### Issue: Quantum optimization fails

**Symptoms:**
```
QuantumError: Circuit execution failed
```

**Solutions:**

1. **Disable quantum features:**
```bash
# In .env
QUANTUM_ENABLED=false
```

2. **Use classical fallback:**
```python
# In core/modules/quantum.py
try:
    result = self.quantum_optimize()
except Exception as e:
    logger.warning(f"Quantum failed, using classical: {e}")
    result = self.classical_optimize()
```

3. **Reduce qubit count:**
```python
# In quantum module
N_QUBITS = 2  # Instead of 4
```

---

## UI & WebSocket Issues

### Issue: UI not loading

**Symptoms:**
- Blank page
- "Failed to fetch" errors in console

**Solutions:**

1. **Check API connection:**
```javascript
// In browser console
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

2. **Verify environment variables:**
```bash
# In ui/web/.env
VITE_API_URL=http://localhost:8000
```

3. **Rebuild UI:**
```bash
cd ui/web
rm -rf node_modules dist
npm install
npm run build
```

4. **Check browser console:**
- Press F12
- Look for errors in Console tab
- Check Network tab for failed requests

### Issue: WebSocket disconnecting

**Symptoms:**
```
WebSocket connection closed
Constantly reconnecting
```

**Solutions:**

1. **Check WebSocket endpoint:**
```javascript
// Test WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
```

2. **Increase timeout:**
```python
# In ui/api/main.py websocket endpoint
await websocket.send_json({...})
await asyncio.sleep(5)  # Increase interval
```

3. **Check proxy configuration:**
```nginx
# Nginx WebSocket config
location /ws {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

---

## Docker & Container Issues

### Issue: Container keeps restarting

**Symptoms:**
```
docker-compose ps shows "Restarting"
```

**Solutions:**

1. **Check logs:**
```bash
docker-compose logs -f api
docker-compose logs -f postgres
```

2. **Check health:**
```bash
docker inspect sigmax_api_1 | jq '.[0].State.Health'
```

3. **Remove and recreate:**
```bash
docker-compose down
docker-compose up -d --force-recreate
```

### Issue: Out of disk space

**Symptoms:**
```
no space left on device
```

**Solutions:**

1. **Clean Docker:**
```bash
docker system prune -a --volumes
```

2. **Remove old images:**
```bash
docker image prune -a
```

3. **Check disk usage:**
```bash
du -sh /var/lib/docker
```

---

## Common Error Messages

### Error: "Configuration validation failed"

**Solution:**
```bash
# Run validator
python core/config/validator.py

# Fix reported issues in .env
```

### Error: "Failed to initialize SIGMAX"

**Solution:**
```bash
# Check all dependencies
./health-check.sh

# Review initialization logs
tail -100 logs/sigmax.log
```

### Error: "Module 'X' not found"

**Solution:**
```bash
pip install --upgrade -r core/requirements.txt
```

### Error: "Port already in use"

**Solution:**
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
kill -9 PID

# Or use different port
PORT=8001 python main.py
```

---

## Getting Help

### Before Asking for Help

1. ✅ Run health check script
2. ✅ Check logs for errors
3. ✅ Search existing GitHub issues
4. ✅ Try solutions in this guide
5. ✅ Collect relevant info (OS, Python version, error messages)

### Where to Get Help

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/yourusername/SIGMAX/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/yourusername/SIGMAX/discussions)
- 📖 **Documentation:** [docs/](./docs/)
- 💡 **Feature Requests:** [GitHub Issues](https://github.com/yourusername/SIGMAX/issues)

### Information to Include

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.5
- Docker: 24.0.5
- SIGMAX Version: 2.0.0

**What I'm trying to do:**
[Describe the task]

**What happened:**
[Error message or unexpected behavior]

**What I expected:**
[Expected result]

**Logs:**
```
[Paste relevant log excerpts]
```

**Steps to reproduce:**
1. Step one
2. Step two
3. ...
```

---

**Last Updated:** 2025-11-06
**Version:** 2.0.0
