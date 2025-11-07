# Grafana Dashboards for SIGMAX

Pre-built Grafana dashboards for monitoring SIGMAX trading bot.

## Available Dashboards

### 1. Trading Metrics (`trading-metrics.json`)

**Purpose**: Monitor trading performance and order flow

**Panels**:
- **Orders Per Second**: Order submission rate by status
- **Fill Rate**: Percentage of orders filled
- **Realized P&L**: Cumulative profit/loss by symbol
- **Current Positions**: Live position tracking
- **Risk Rejections**: Risk check failures by reason
- **Tick-to-Trade Latency**: End-to-end latency (p50, p99)
- **Trade Volume**: USD volume by symbol
- **Signal Counts**: Signal generation rate by strategy
- **Decision Layer Breakdown**: Action distribution across L0-L5
- **Market Data Feed Health**: Tick ingestion rate
- **Risk Gate Latency**: Pre-trade risk check latency
- **Pipeline Stage Latencies**: Heatmap of all stages

**Alerts**:
- High tick-to-trade latency (>20ms p99)
- Risk gate latency exceeding SLO (>100µs p99)

**Refresh**: 5 seconds

---

### 2. System Health (`system-health.json`)

**Purpose**: Monitor infrastructure and system resources

**Panels**:
- **Service Status**: Up/down status for all services
- **CPU Usage**: CPU utilization by instance
- **Memory Usage**: Memory consumption
- **Network I/O**: Network traffic (RX/TX)
- **Disk I/O**: Disk read/write rates
- **Postgres Connections**: Active database connections
- **ClickHouse Query Rate**: OLAP query throughput
- **Redis Memory Usage**: Cache memory utilization
- **ZeroMQ Message Rate**: IPC message throughput
- **Error Rate by Service**: Error frequency by service and type
- **GC Pause Time**: Python garbage collection metrics
- **Open File Descriptors**: System resource usage
- **Log Events by Level**: Recent log messages

**Alerts**:
- High error rate (>1 error/sec sustained)
- Resource exhaustion warnings

**Refresh**: 10 seconds

---

## Installation

### Method 1: Manual Import

1. **Open Grafana**: Navigate to http://localhost:3000
2. **Login**: Default credentials (admin/admin)
3. **Import Dashboard**:
   - Click "+" → "Import"
   - Copy contents of dashboard JSON file
   - Paste into "Import via panel json"
   - Click "Load"
4. **Configure Data Source**:
   - Select "Prometheus" as data source
   - Click "Import"

### Method 2: Automated Import

```bash
# Import all dashboards
./tools/import_dashboards.sh

# Or manually using curl
curl -X POST \
  -H "Content-Type: application/json" \
  -d @infra/prometheus/grafana-dashboards/trading-metrics.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

### Method 3: Provisioning (Recommended)

Add to `docker-compose.yml`:

```yaml
grafana:
  image: grafana/grafana:latest
  volumes:
    - ./infra/prometheus/grafana-dashboards:/etc/grafana/provisioning/dashboards
    - ./infra/prometheus/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
  environment:
    - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/etc/grafana/provisioning/dashboards/trading-metrics.json
```

---

## Data Source Configuration

### Prometheus

Create `/etc/grafana/provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

### Loki (Logs)

If using Loki for log aggregation:

```yaml
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
```

---

## Customization

### Adding Custom Panels

1. Open dashboard in Grafana
2. Click "Add panel" → "Add new panel"
3. Configure query using PromQL
4. Save dashboard
5. Export JSON: "Dashboard settings" → "JSON Model"
6. Save to repository

### Common PromQL Queries

**Order fill rate**:
```promql
rate(sigmax_fills_total[5m]) / rate(sigmax_orders_total{status="sent"}[5m])
```

**P99 latency**:
```promql
histogram_quantile(0.99, rate(sigmax_latency_us_bucket[1m]))
```

**Error rate by service**:
```promql
sum by(service) (rate(sigmax_errors_total[5m]))
```

**Position value (USD)**:
```promql
sigmax_position_qty * sigmax_mark_price
```

**Sharpe ratio (daily)**:
```promql
(avg_over_time(sigmax_pnl_realized[1d]) - avg_over_time(sigmax_pnl_realized[1d] offset 1d)) /
stddev_over_time(sigmax_pnl_realized[1d])
```

---

## Alert Configuration

### Alertmanager Integration

Configure alerts in `infra/prometheus/alertmanager.yml`:

```yaml
route:
  receiver: 'slack'
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#trading-alerts'
        title: 'SIGMAX Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### Critical Alerts

**High Latency**:
```yaml
- alert: HighTickToTradeLatency
  expr: histogram_quantile(0.99, rate(sigmax_latency_us_bucket{stage="tick_to_trade"}[5m])) > 20000
  for: 5m
  annotations:
    description: "Tick-to-trade p99 latency exceeds 20ms SLO"
```

**Risk Rejections**:
```yaml
- alert: HighRiskRejectionRate
  expr: rate(sigmax_risk_checks_total{result="reject"}[5m]) > 10
  for: 2m
  annotations:
    description: "Risk rejection rate > 10/sec"
```

**Position Limit Breach**:
```yaml
- alert: PositionLimitBreach
  expr: abs(sigmax_position_qty) > sigmax_position_limit
  for: 1m
  annotations:
    description: "Position exceeds configured limits"
```

---

## Troubleshooting

### Dashboard Not Loading

1. **Check Prometheus**: Verify http://localhost:9090 is accessible
2. **Check metrics**: Query `up{job="sigmax"}` in Prometheus
3. **Check data source**: Grafana → Configuration → Data Sources
4. **Check time range**: Ensure dashboards have data for selected time range

### No Data Shown

1. **Verify services running**: `docker ps` or `systemctl status sigmax-*`
2. **Check Prometheus targets**: http://localhost:9090/targets
3. **Verify metrics exported**: `curl http://localhost:8000/metrics`
4. **Check metric names**: May need to adjust queries if metric names changed

### Performance Issues

1. **Reduce refresh rate**: Change from 5s to 30s
2. **Limit time range**: Use shorter windows (1h instead of 24h)
3. **Optimize queries**: Use rate() instead of increase() where possible
4. **Increase Prometheus retention**: If historical data missing

---

## Best Practices

1. **Monitor SLOs**: Keep tick-to-trade p99 < 20ms (Profile A)
2. **Watch error rates**: Investigate spikes in error panels
3. **Track P&L**: Monitor realized P&L panel for unexpected losses
4. **Position limits**: Ensure positions stay within risk parameters
5. **System resources**: Watch CPU/memory to prevent resource exhaustion
6. **Alert fatigue**: Tune alert thresholds to reduce false positives

---

## Screenshots

### Trading Metrics Dashboard
- Real-time order flow visualization
- Latency heatmaps for performance analysis
- P&L tracking by symbol

### System Health Dashboard
- Service status overview
- Resource utilization trends
- Error and log aggregation

---

## Resources

- [Prometheus Query Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)

---

## Contributing

To contribute dashboards:

1. Create/modify dashboard in Grafana UI
2. Export as JSON
3. Format JSON (use `jq` for pretty-printing)
4. Add documentation to this README
5. Submit PR with dashboard + docs
