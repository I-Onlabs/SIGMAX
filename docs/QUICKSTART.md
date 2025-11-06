# SIGMAX Quick Start Guide

Get SIGMAX running in 5 minutes!

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone <repo-url>
cd SIGMAX
```

### 2. Start Infrastructure

```bash
# Start databases and monitoring
docker-compose -f infra/compose/docker-compose.yml up -d

# Wait for services to be ready (30 seconds)
sleep 30
```

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Initialize Databases

```bash
python tools/init_database.py --profile=a
```

### 5. Configure (Optional for Paper Trading)

```bash
cp .env.example .env
# Edit .env if you want to test with real exchanges
# For paper trading, default config works!
```

### 6. Run the Trading System

```bash
# Start all services
python tools/runner.py --profile=a
```

You should see:

```
INFO starting_sigmax_services profile=a services=['ingest', 'book', 'features', 'volatility', 'decision', 'risk', 'router', 'exec']
INFO service_started service=ingest name=Market Data Ingestion pid=12345
INFO service_started service=book name=Order Book Shard pid=12346
...
INFO all_services_started count=8
```

## Verify It's Working

### Check Service Health

```bash
# Check if services are running
ps aux | grep python

# Check logs
tail -f logs/sigmax.log
```

### View Metrics

Open http://localhost:9090 (Prometheus)

Check metrics:
- `sigmax_latency_microseconds`
- `sigmax_messages_received_total`
- `sigmax_orders_submitted_total`

### View Dashboards

Open http://localhost:3000 (Grafana)

Login: admin/admin

## What's Running?

| Service | Description | Port |
|---------|-------------|------|
| ingest_cex | Market data ingestion | 9091 |
| book_shard | Order book maintenance | 9092 |
| features | Feature extraction | 9093 |
| decision | Trading decisions | 9094 |
| risk | Pre-trade risk | 9095 |
| router | Order routing | 9096 |
| exec_cex | Order execution | 9097 |
| Prometheus | Metrics | 9090 |
| Grafana | Dashboards | 3000 |
| Postgres | Database | 5432 |
| ClickHouse | Analytics | 9000 |

## First Trading Strategy

The system is running with a default mean-reversion strategy:

- **L1 Rules**: Trade on orderbook imbalance > 30%
- **L1 Rules**: Follow momentum on price change > 0.5%
- **L0 Safety**: Spread must be 1-500 bps
- **Risk**: Max $500 per order, $5000 position limit

## Testing Paper Trading

The system is in **paper trading mode** by default (simulated fills).

Watch the logs for:

```
INFO order_intent_generated symbol_id=1 side=buy qty=0.01 price=50000.0 confidence=0.7
INFO order_approved client_id=abc-123
INFO order_routed client_id=abc-123 venue=binance
INFO order_executed client_id=abc-123 exchange_order_id=SIM-abc-123
```

## Enable Live Trading

**⚠️ WARNING: Live trading involves real financial risk!**

1. Get exchange API keys
2. Edit `.env`:
   ```bash
   BINANCE_API_KEY=your_real_key
   BINANCE_API_SECRET=your_real_secret
   ```

3. Edit `profiles/profile_a.yaml`:
   ```yaml
   exchanges:
     binance:
       testnet: false  # Switch to production
   ```

4. Uncomment execution code in `apps/exec_cex/execution_engine.py`:
   ```python
   # Line ~115: Uncomment this
   result = await exchange.create_order(
       symbol=symbol,
       type=order.order_type.name.lower(),
       side=order.side.name.lower(),
       amount=order.qty,
       price=order.price
   )
   ```

5. Restart the system

## Next Steps

- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Architecture](../README.md#architecture) - Understand the system
- [Configuration](../profiles/profile_a.yaml) - Customize settings
- [Strategies](STRATEGIES.md) - Develop your own strategies

## Troubleshooting

### Services Exit Immediately

Check logs:
```bash
tail -f logs/sigmax.log
```

Common issues:
- Database not ready (wait 30s after `docker-compose up`)
- Port conflicts (change ports in configs)
- Missing dependencies (`pip install -r requirements.txt`)

### No Market Data

The ingestion service connects to exchange websockets. If using paper mode without API keys, it won't receive real data.

For testing without exchange connection, see the replay service (coming soon).

### High CPU Usage

Normal! The system is processing market data and making trading decisions continuously.

To reduce CPU:
- Reduce number of symbols in `profiles/profile_a.yaml`
- Increase window sizes in feature extraction
- Disable optional signal modules

## Stopping the System

```bash
# Stop trading services
pkill -f "python.*apps"

# Stop infrastructure
docker-compose -f infra/compose/docker-compose.yml down
```

## Clean Slate

```bash
# Remove all data and start fresh
docker-compose -f infra/compose/docker-compose.yml down -v
docker volume prune -f
rm -rf logs/*
```

Then repeat installation steps.

## Getting Help

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guidance
- Check logs in `./logs/`
- Open an issue on GitHub

Happy Trading! 🚀

**Disclaimer**: This is for educational purposes. Trading involves risk. Not financial advice.
