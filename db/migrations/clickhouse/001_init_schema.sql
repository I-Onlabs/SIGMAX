-- SIGMAX ClickHouse Schema
-- OLAP database for ticks, latencies, signals, and audit logs

-- Ticks table - Market data updates
CREATE TABLE IF NOT EXISTS sigmax.ticks (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    symbol_id UInt32,
    bid_px Decimal(20, 8),
    bid_sz Decimal(20, 8),
    ask_px Decimal(20, 8),
    ask_sz Decimal(20, 8),
    seq UInt64,
    spread Decimal(20, 8) MATERIALIZED ask_px - bid_px,
    mid_price Decimal(20, 8) MATERIALIZED (bid_px + ask_px) / 2
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, ts_ns)
TTL timestamp + INTERVAL 90 DAY;

-- Book snapshots - Order book state
CREATE TABLE IF NOT EXISTS sigmax.book_snapshots (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    symbol_id UInt32,
    bid_px Decimal(20, 8),
    bid_sz Decimal(20, 8),
    ask_px Decimal(20, 8),
    ask_sz Decimal(20, 8),
    spread Decimal(20, 8),
    mid_price Decimal(20, 8),
    micro_price Decimal(20, 8),
    imbalance Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, ts_ns)
TTL timestamp + INTERVAL 90 DAY;

-- Latency measurements
CREATE TABLE IF NOT EXISTS sigmax.latencies (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    stage String,
    latency_us Float64,
    latency_ns UInt64,
    symbol_id UInt32,
    metadata String  -- JSON metadata
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (stage, ts_ns)
TTL timestamp + INTERVAL 30 DAY;

-- Signals table
CREATE TABLE IF NOT EXISTS sigmax.signals (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    symbol_id UInt32,
    sig_type UInt8,  -- SignalType enum
    value Float64,
    meta_code UInt32,
    confidence Float32,
    metadata String  -- JSON metadata
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, sig_type, ts_ns)
TTL timestamp + INTERVAL 90 DAY;

-- Features table
CREATE TABLE IF NOT EXISTS sigmax.features (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    symbol_id UInt32,
    mid_price Decimal(20, 8),
    micro_price Decimal(20, 8),
    spread Decimal(20, 8),
    spread_bps Float32,
    bid_volume Decimal(20, 8),
    ask_volume Decimal(20, 8),
    imbalance Float32,
    realized_vol Float32,
    price_range Decimal(20, 8),
    price_change Decimal(20, 8),
    price_change_pct Float32,
    regime_bits UInt32
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, ts_ns)
TTL timestamp + INTERVAL 90 DAY;

-- Order flow events
CREATE TABLE IF NOT EXISTS sigmax.order_events (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    event_type String,  -- 'intent', 'ack', 'fill', 'reject'
    client_id String,
    symbol_id UInt32,
    side String,
    order_type String,
    price Nullable(Decimal(20, 8)),
    qty Decimal(20, 8),
    status String,
    metadata String  -- JSON metadata
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, ts_ns)
TTL timestamp + INTERVAL 180 DAY;

-- Audit log (WORM - Write Once Read Many)
CREATE TABLE IF NOT EXISTS sigmax.audit_log (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    event_type String,
    service String,
    payload String,  -- JSON payload
    hash String,  -- SHA256 hash for tamper evidence
    prev_hash String  -- Previous record hash for chain
) ENGINE = MergeTree()
ORDER BY ts_ns
SETTINGS index_granularity = 8192;

-- Performance metrics table
CREATE TABLE IF NOT EXISTS sigmax.performance_metrics (
    ts_ns UInt64,
    timestamp DateTime64(9, 'UTC') MATERIALIZED fromUnixTimestamp64Nano(ts_ns),
    service String,
    metric_name String,
    metric_value Float64,
    labels String  -- JSON labels
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (service, metric_name, ts_ns)
TTL timestamp + INTERVAL 30 DAY;

-- Materialized views for common queries

-- Tick-to-trade latency view
CREATE MATERIALIZED VIEW IF NOT EXISTS sigmax.tick_to_trade_latency_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, timestamp)
AS SELECT
    toStartOfMinute(timestamp) AS timestamp,
    symbol_id,
    quantileState(0.50)(latency_us) AS p50_latency,
    quantileState(0.99)(latency_us) AS p99_latency,
    quantileState(0.999)(latency_us) AS p999_latency,
    avgState(latency_us) AS avg_latency,
    maxState(latency_us) AS max_latency,
    count() AS sample_count
FROM sigmax.latencies
WHERE stage = 'tick_to_trade'
GROUP BY timestamp, symbol_id;

-- Signal statistics view
CREATE MATERIALIZED VIEW IF NOT EXISTS sigmax.signal_stats_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, sig_type, timestamp)
AS SELECT
    toStartOfHour(timestamp) AS timestamp,
    symbol_id,
    sig_type,
    avgState(value) AS avg_value,
    quantileState(0.50)(value) AS median_value,
    minState(value) AS min_value,
    maxState(value) AS max_value,
    count() AS signal_count
FROM sigmax.signals
GROUP BY timestamp, symbol_id, sig_type;

-- Spread statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS sigmax.spread_stats_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (symbol_id, timestamp)
AS SELECT
    toStartOfMinute(timestamp) AS timestamp,
    symbol_id,
    avgState(spread) AS avg_spread,
    quantileState(0.50)(spread) AS median_spread,
    minState(spread) AS min_spread,
    maxState(spread) AS max_spread
FROM sigmax.ticks
GROUP BY timestamp, symbol_id;
