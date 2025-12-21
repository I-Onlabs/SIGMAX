-- SIGMAX PostgreSQL Schema - Agent Debates
-- Stores multi-agent debate history for trading decisions
-- Migration 002 - Agent Debate Storage

-- Agent debates table
CREATE TABLE IF NOT EXISTS agent_debates (
    id BIGSERIAL PRIMARY KEY,

    -- Symbol reference
    symbol_id INTEGER NOT NULL REFERENCES symbols(symbol_id),
    symbol VARCHAR(40) NOT NULL,  -- Denormalized for convenience (e.g., "BTC/USDT")

    -- Debate participants (agent arguments)
    bull_argument TEXT,           -- Bull agent's buying case
    bear_argument TEXT,           -- Bear agent's selling case
    research_summary TEXT,        -- Researcher agent's market intelligence
    technical_analysis JSONB,     -- Technical analyzer's findings
    fundamental_analysis JSONB,   -- Fundamental analyzer's findings

    -- Decision outcome
    final_decision VARCHAR(20) NOT NULL CHECK (final_decision IN ('buy', 'sell', 'hold')),
    confidence NUMERIC(5, 4),     -- 0.0 to 1.0
    sentiment NUMERIC(6, 4),      -- -1.0 to 1.0

    -- Agent scores and detailed reasoning
    bull_score NUMERIC(5, 4),     -- Bull agent's conviction score
    bear_score NUMERIC(5, 4),     -- Bear agent's conviction score
    agent_scores JSONB,           -- Full agent scores: {"bull": 0.75, "bear": 0.45, ...}
    reasoning JSONB,              -- Detailed reasoning from orchestrator

    -- Risk validation
    risk_approved BOOLEAN DEFAULT true,
    risk_constraints JSONB,       -- Risk limits applied

    -- Timestamps (nanosecond precision for ordering)
    created_at_ns BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_agent_debates_symbol_id ON agent_debates(symbol_id);
CREATE INDEX idx_agent_debates_symbol ON agent_debates(symbol);
CREATE INDEX idx_agent_debates_created_at ON agent_debates(created_at DESC);
CREATE INDEX idx_agent_debates_created_at_ns ON agent_debates(created_at_ns DESC);
CREATE INDEX idx_agent_debates_final_decision ON agent_debates(final_decision);
CREATE INDEX idx_agent_debates_confidence ON agent_debates(confidence DESC);

-- Composite index for common filtered queries
CREATE INDEX idx_agent_debates_symbol_decision ON agent_debates(symbol, final_decision, created_at DESC);
CREATE INDEX idx_agent_debates_symbol_time ON agent_debates(symbol, created_at DESC);

-- Comments for documentation
COMMENT ON TABLE agent_debates IS 'Multi-agent debate history for trading decisions';
COMMENT ON COLUMN agent_debates.bull_argument IS 'Bull agent buying case with supporting evidence';
COMMENT ON COLUMN agent_debates.bear_argument IS 'Bear agent selling case with risk factors';
COMMENT ON COLUMN agent_debates.research_summary IS 'Market intelligence gathered by researcher agent';
COMMENT ON COLUMN agent_debates.final_decision IS 'Final trading decision: buy, sell, or hold';
COMMENT ON COLUMN agent_debates.confidence IS 'Decision confidence level (0.0-1.0)';
COMMENT ON COLUMN agent_debates.sentiment IS 'Market sentiment score (-1.0 to 1.0)';
COMMENT ON COLUMN agent_debates.agent_scores IS 'JSON object with all agent conviction scores';
COMMENT ON COLUMN agent_debates.reasoning IS 'Detailed reasoning structure from orchestrator';
