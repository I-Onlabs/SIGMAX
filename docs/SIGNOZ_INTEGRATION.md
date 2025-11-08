# SigNoz Observability Integration

## Overview

SIGMAX integrates with **SigNoz**, an open-source observability platform, using OpenTelemetry for production-grade monitoring. This enables complete visibility into trading operations with distributed tracing, custom metrics, and structured logging.

## Why SigNoz?

Traditional monitoring solutions are expensive and proprietary. SigNoz provides:

- ✅ **Open Source**: Full control over your observability data
- ✅ **OpenTelemetry Native**: Industry-standard instrumentation
- ✅ **All-in-One**: Logs, traces, and metrics in one platform
- ✅ **Cost-Effective**: No per-seat or data volume pricing
- ✅ **Self-Hosted**: Keep sensitive trading data private
- ✅ **Alternative to DataDog/NewRelic**: Enterprise features without the cost

## Architecture

```
SIGMAX Trading System
├── OpenTelemetry SDK
│   ├── Traces (Distributed Tracing)
│   ├── Metrics (Trading Performance)
│   └── Logs (Structured Logging)
│
├── OTLP Exporters
│   ├── HTTP Exporter (Primary)
│   └── Console Exporter (Development)
│
├── SigNoz Backend
│   ├── ClickHouse (Metrics & Traces)
│   ├── Query Service (API)
│   └── Frontend (Dashboard)
│
└── Monitoring Dashboards
    ├── Trade Execution Metrics
    ├── Position Management
    ├── PnL Tracking
    └── Error Rates
```

## Features

### 1. Distributed Tracing

Track request flows across components:
- Trade execution pipelines
- Agent decision-making processes
- Risk assessment workflows
- Multi-exchange arbitrage operations

### 2. Custom Metrics

Trading-specific metrics:
- **Trade Counter**: Total trades by symbol, side, success
- **Latency Histogram**: Execution latency distribution
- **Position Gauge**: Current open positions
- **PnL Histogram**: Profit/loss distribution
- **Error Counter**: Errors by type and component

### 3. Structured Logging

Correlated logs with traces:
- Automatic trace ID injection
- Span ID correlation
- Structured log attributes
- Log-to-trace linking in UI

### 4. Auto-Instrumentation

Automatic instrumentation for:
- aiohttp HTTP clients
- Python logging
- AsyncIO operations

## Installation

### 1. Install OpenTelemetry

```bash
pip install opentelemetry-distro \
    opentelemetry-exporter-otlp-proto-http \
    opentelemetry-instrumentation \
    opentelemetry-instrumentation-aiohttp-client \
    opentelemetry-instrumentation-logging
```

### 2. Install SigNoz

#### Option A: Docker Compose (Recommended)

```bash
git clone https://github.com/SigNoz/signoz.git
cd signoz/deploy
./install.sh
```

#### Option B: Kubernetes

```bash
helm repo add signoz https://charts.signoz.io
helm install signoz signoz/signoz
```

#### Option C: SigNoz Cloud

Sign up at https://signoz.io/teams/

### 3. Verify SigNoz

Access SigNoz UI:
- Local: http://localhost:3301
- Cloud: https://[your-org].signoz.io

## Configuration

### Environment Variables

Create `.env` file or set environment variables:

```bash
# Observability
OBSERVABILITY_ENABLED=true
OTEL_SERVICE_NAME=sigmax
SIGMAX_VERSION=1.0.0
ENVIRONMENT=production

# SigNoz Endpoint
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# Feature Toggles
OTEL_TRACES_ENABLED=true
OTEL_METRICS_ENABLED=true
OTEL_LOGS_ENABLED=true
OTEL_CONSOLE_ENABLED=false  # Enable for debugging

# Export Interval
OTEL_METRIC_EXPORT_INTERVAL=30000  # 30 seconds
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `OBSERVABILITY_ENABLED` | `true` | Enable/disable observability |
| `OTEL_SERVICE_NAME` | `sigmax` | Service name in SigNoz |
| `SIGMAX_VERSION` | `1.0.0` | Service version |
| `ENVIRONMENT` | `development` | Environment (dev/staging/prod) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | SigNoz collector endpoint |
| `OTEL_TRACES_ENABLED` | `true` | Enable distributed tracing |
| `OTEL_METRICS_ENABLED` | `true` | Enable metrics collection |
| `OTEL_LOGS_ENABLED` | `true` | Enable log instrumentation |
| `OTEL_CONSOLE_ENABLED` | `false` | Enable console output (debug) |

## Usage

### Automatic Instrumentation

SIGMAX automatically instruments itself on startup. No code changes needed!

```bash
python core/main.py --mode paper --profile conservative
```

The observability system:
1. Initializes OpenTelemetry SDK
2. Configures SigNoz exporters
3. Instruments common libraries
4. Starts exporting telemetry

### Manual Tracing

#### Async Functions

```python
from core.modules.observability import trace_async

@trace_async("execute_trade")
async def execute_trade(symbol, side, quantity):
    """Execute trade with automatic tracing"""
    # ... execution logic ...
    return result
```

#### Sync Functions

```python
from core.modules.observability import trace_sync

@trace_sync("calculate_risk")
def calculate_risk(portfolio):
    """Calculate risk with automatic tracing"""
    # ... risk calculation ...
    return risk_score
```

#### Context Manager

```python
from core.modules.observability import get_observability

observability = get_observability()

with observability.trace_operation("complex_operation", {"symbol": "BTC/USDT"}):
    # ... operation code ...
    pass
```

### Recording Metrics

#### Trade Metrics

```python
from core.modules.observability import get_observability

observability = get_observability()

observability.record_trade(
    symbol="BTC/USDT",
    side="buy",
    quantity=1.0,
    price=50000.0,
    latency_ms=100.5,
    success=True
)
```

#### Position Changes

```python
# Open position
observability.record_position_change("BTC/USDT", +1)

# Close position
observability.record_position_change("BTC/USDT", -1)
```

#### Profit/Loss

```python
observability.record_pnl("BTC/USDT", 1000.0)   # Profit
observability.record_pnl("ETH/USDT", -500.0)   # Loss
```

#### Errors

```python
observability.record_error("ConnectionError", "execution_module")
```

### Custom Attributes

Add custom attributes to spans:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("exchange", "binance")
    span.set_attribute("order_type", "limit")
    span.set_attribute("leverage", 2.0)
    # ... operation ...
```

## SigNoz Dashboard

### Accessing Dashboards

1. **Service Map**: Visualize service dependencies
2. **Traces**: Search and analyze traces
3. **Metrics**: View trading metrics
4. **Logs**: Search correlated logs
5. **Alerts**: Configure alerts

### Key Metrics to Monitor

#### Trade Execution
- `sigmax.trades.total`: Total trades
- `sigmax.trade.latency`: Execution latency (p50, p95, p99)
- Filter by: `symbol`, `side`, `success`

#### Positions
- `sigmax.positions.count`: Open positions
- Filter by: `symbol`

#### PnL
- `sigmax.pnl`: Profit/loss distribution
- Filter by: `symbol`

#### Errors
- `sigmax.errors.total`: Error count
- Filter by: `error_type`, `component`

### Example Queries

#### Average Trade Latency by Symbol

```
avg(sigmax.trade.latency) by symbol
```

#### Trade Success Rate

```
sum(sigmax.trades.total{success="true"}) / sum(sigmax.trades.total) * 100
```

#### Error Rate

```
rate(sigmax.errors.total[5m])
```

## Example Workflow

### 1. Start SIGMAX with Observability

```bash
export OBSERVABILITY_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
python core/main.py --mode paper
```

### 2. Execute Trades

SIGMAX automatically traces and records metrics for:
- Agent decisions
- Risk assessments
- Trade executions
- Position updates

### 3. View in SigNoz

Navigate to http://localhost:3301

**Traces**:
1. Go to "Traces" tab
2. Filter by service: `sigmax`
3. Search for operation: `execute_trade`
4. Click on trace to see full span timeline

**Metrics**:
1. Go to "Dashboards"
2. Create new dashboard
3. Add panel: `sigmax.trades.total`
4. Group by: `symbol`
5. Time range: Last 1 hour

**Logs**:
1. Go to "Logs" tab
2. Filter by service: `sigmax`
3. Click log entry to see linked trace

### 4. Create Alerts

```yaml
# Example alert: High latency
name: "High Trade Latency"
condition: "sigmax.trade.latency.p95 > 1000"  # >1 second
threshold: 1000ms
severity: warning
notification: slack/email
```

## Production Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  sigmax:
    build: .
    environment:
      - OBSERVABILITY_ENABLED=true
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://signoz-otel-collector:4318
      - OTEL_SERVICE_NAME=sigmax
      - ENVIRONMENT=production
    depends_on:
      - signoz-otel-collector

  signoz-otel-collector:
    image: signoz/signoz-otel-collector:latest
    ports:
      - "4318:4318"  # OTLP HTTP
      - "4317:4317"  # OTLP gRPC
```

### Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sigmax-config
data:
  OBSERVABILITY_ENABLED: "true"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://signoz-otel-collector.monitoring:4318"
  OTEL_SERVICE_NAME: "sigmax"
  ENVIRONMENT: "production"

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: sigmax
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: sigmax
        image: sigmax:latest
        envFrom:
        - configMapRef:
            name: sigmax-config
```

## Troubleshooting

### Issue: Traces not appearing

**Check**:
1. SigNoz collector is running: `curl http://localhost:4318/v1/traces`
2. Environment variables are set
3. `OTEL_TRACES_ENABLED=true`
4. Check logs: `grep "Observability initialized" logs/sigmax.log`

**Solution**:
```bash
# Enable console exporter for debugging
export OTEL_CONSOLE_ENABLED=true
python core/main.py --mode paper
```

### Issue: Metrics not updating

**Check**:
1. Export interval: `OTEL_METRIC_EXPORT_INTERVAL=30000` (30s)
2. Wait for export cycle to complete
3. Check SigNoz metrics storage

**Solution**:
```python
# Force metric flush (for testing)
from core.modules.observability import get_observability
observability = get_observability()
observability.shutdown()  # Flushes metrics
```

### Issue: High memory usage

**Cause**: Too many spans in memory

**Solution**:
```python
# Reduce batch size
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,      # Default: 2048
    max_export_batch_size=512  # Default: 512
)
```

### Issue: Network timeouts

**Cause**: SigNoz collector unreachable

**Solution**:
1. Check network: `telnet localhost 4318`
2. Increase timeout in config
3. Use gRPC instead of HTTP:
```bash
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Performance Impact

### Overhead

| Component | Overhead | Impact |
|-----------|----------|---------|
| Tracing | <1% CPU | Negligible |
| Metrics | <0.5% CPU | Negligible |
| Logging | <0.5% CPU | Negligible |
| **Total** | **<2% CPU** | **Minimal** |

### Recommendations

**Development**:
- Enable all: traces, metrics, logs
- Use console exporter for debugging
- Short export intervals (10s)

**Production**:
- Enable traces + metrics (logs optional)
- OTLP HTTP/gRPC exporter
- Standard export interval (30s)
- Sample high-volume traces (if needed)

## Best Practices

### 1. Meaningful Span Names

```python
# Good
@trace_async("execute_limit_order")

# Bad
@trace_async("do_stuff")
```

### 2. Add Context

```python
with tracer.start_as_current_span("trade") as span:
    span.set_attribute("symbol", "BTC/USDT")
    span.set_attribute("exchange", "binance")
    span.set_attribute("order_type", "limit")
```

### 3. Error Handling

```python
@trace_async("execute_trade")
async def execute_trade():
    try:
        # ... trading logic ...
    except Exception as e:
        observability.record_error(type(e).__name__, "execution")
        raise
```

### 4. Metric Labels

```python
# Keep cardinality low (don't use unique IDs)
observability.record_trade(
    symbol="BTC/USDT",      # Good (low cardinality)
    side="buy",             # Good
    # order_id="12345"     # Bad (high cardinality)
)
```

### 5. Sampling (High Volume)

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.1)
```

## Advanced Features

### Custom Metrics

```python
from core.modules.observability import get_observability

observability = get_observability()
meter = observability.meter

# Create custom counter
slippage_counter = meter.create_histogram(
    name="sigmax.slippage",
    description="Trade slippage",
    unit="bps"
)

# Record
slippage_counter.record(5.2, {"symbol": "BTC/USDT"})
```

### Trace Propagation

```python
from opentelemetry.propagate import inject

headers = {}
inject(headers)  # Inject trace context

# Pass headers to downstream service
await aiohttp_client.post(url, headers=headers)
```

### Baggage

```python
from opentelemetry.baggage import set_baggage

# Set baggage (propagates across services)
ctx = set_baggage("user_id", "12345")
ctx = set_baggage("risk_profile", "aggressive", context=ctx)
```

## References

- **SigNoz**: https://signoz.io/
- **OpenTelemetry**: https://opentelemetry.io/
- **Python Instrumentation**: https://opentelemetry.io/docs/languages/python/
- **SigNoz Docs**: https://signoz.io/docs/
- **GitHub - SigNoz**: https://github.com/SigNoz/signoz

## Support

For issues:
- **SigNoz**: https://github.com/SigNoz/signoz/issues
- **OpenTelemetry**: https://github.com/open-telemetry/opentelemetry-python/issues
- **SIGMAX**: Repository issues

## License

- SigNoz: MIT License
- OpenTelemetry: Apache 2.0
- SIGMAX: See main repository LICENSE
