-- SIGMAX PostgreSQL Schema
-- OLTP database for orders, fills, positions, and account state

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Symbols table
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id SERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    base VARCHAR(20) NOT NULL,
    quote VARCHAR(20) NOT NULL,
    pair VARCHAR(40) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exchange, base, quote)
);

CREATE INDEX idx_symbols_exchange ON symbols(exchange);
CREATE INDEX idx_symbols_pair ON symbols(pair);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    client_id UUID NOT NULL UNIQUE,
    exchange_order_id VARCHAR(100),
    symbol_id INTEGER NOT NULL REFERENCES symbols(symbol_id),
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT')),
    tif VARCHAR(10) NOT NULL CHECK (tif IN ('GTC', 'IOC', 'FOK', 'GTX')),
    price NUMERIC(20, 8),
    qty NUMERIC(20, 8) NOT NULL,
    filled_qty NUMERIC(20, 8) DEFAULT 0,
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'SUBMITTED', 'PARTIAL', 'FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED')),
    source VARCHAR(50) NOT NULL,  -- Which decision layer generated this
    route VARCHAR(50),  -- Venue routing
    created_at_ns BIGINT NOT NULL,
    submitted_at_ns BIGINT,
    updated_at_ns BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_client_id ON orders(client_id);
CREATE INDEX idx_orders_exchange_order_id ON orders(exchange_order_id);
CREATE INDEX idx_orders_symbol_id ON orders(symbol_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Fills table
CREATE TABLE IF NOT EXISTS fills (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    client_id UUID NOT NULL,
    exchange_order_id VARCHAR(100) NOT NULL,
    trade_id VARCHAR(100),
    symbol_id INTEGER NOT NULL REFERENCES symbols(symbol_id),
    side VARCHAR(10) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    price NUMERIC(20, 8) NOT NULL,
    qty NUMERIC(20, 8) NOT NULL,
    fee NUMERIC(20, 8) DEFAULT 0,
    fee_currency VARCHAR(10),
    is_maker BOOLEAN DEFAULT false,
    venue_code INTEGER,
    filled_at_ns BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fills_order_id ON fills(order_id);
CREATE INDEX idx_fills_client_id ON fills(client_id);
CREATE INDEX idx_fills_symbol_id ON fills(symbol_id);
CREATE INDEX idx_fills_created_at ON fills(created_at);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES symbols(symbol_id) UNIQUE,
    qty NUMERIC(20, 8) NOT NULL DEFAULT 0,
    avg_entry_price NUMERIC(20, 8) DEFAULT 0,
    realized_pnl NUMERIC(20, 8) DEFAULT 0,
    unrealized_pnl NUMERIC(20, 8) DEFAULT 0,
    total_fees NUMERIC(20, 8) DEFAULT 0,
    last_update_ns BIGINT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_symbol_id ON positions(symbol_id);

-- Account balances
CREATE TABLE IF NOT EXISTS balances (
    id SERIAL PRIMARY KEY,
    exchange VARCHAR(50) NOT NULL,
    currency VARCHAR(20) NOT NULL,
    available NUMERIC(20, 8) DEFAULT 0,
    locked NUMERIC(20, 8) DEFAULT 0,
    total NUMERIC(20, 8) DEFAULT 0,
    last_update_ns BIGINT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exchange, currency)
);

CREATE INDEX idx_balances_exchange ON balances(exchange);

-- Risk events log
CREATE TABLE IF NOT EXISTS risk_events (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- 'block', 'warning', 'limit_reached'
    reason_code INTEGER NOT NULL,
    reason_msg TEXT,
    client_id UUID,
    symbol_id INTEGER REFERENCES symbols(symbol_id),
    metadata JSONB,
    created_at_ns BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_events_type ON risk_events(event_type);
CREATE INDEX idx_risk_events_created_at ON risk_events(created_at);

-- Decision layer events log
CREATE TABLE IF NOT EXISTS decision_events (
    id BIGSERIAL PRIMARY KEY,
    layer INTEGER NOT NULL,  -- L0-L5
    symbol_id INTEGER REFERENCES symbols(symbol_id),
    action VARCHAR(50),  -- 'pass', 'modify', 'block'
    confidence NUMERIC(5, 4),
    metadata JSONB,
    created_at_ns BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decision_events_layer ON decision_events(layer);
CREATE INDEX idx_decision_events_created_at ON decision_events(created_at);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_symbols_updated_at BEFORE UPDATE ON symbols FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_balances_updated_at BEFORE UPDATE ON balances FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert common symbols
INSERT INTO symbols (exchange, base, quote, pair) VALUES
    ('binance', 'BTC', 'USDT', 'BTC/USDT'),
    ('binance', 'ETH', 'USDT', 'ETH/USDT'),
    ('binance', 'SOL', 'USDT', 'SOL/USDT'),
    ('binance', 'BNB', 'USDT', 'BNB/USDT'),
    ('binance', 'XRP', 'USDT', 'XRP/USDT')
ON CONFLICT (exchange, base, quote) DO NOTHING;
