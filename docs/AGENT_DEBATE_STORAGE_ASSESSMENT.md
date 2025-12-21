# Agent Debate Storage Assessment

**Date**: December 21, 2024
**Status**: ⚠️ 50% Complete (Better than expected!)
**Estimated Remaining Effort**: 16 hours (not 32!)

---

## Executive Summary

The comprehensive audit identified agent debate storage as missing, but investigation reveals it's **already 50% implemented**. The orchestrator captures debate data and stores it in memory/Redis via DecisionHistory. Only PostgreSQL persistence and API integration are needed.

### Key Findings

✅ **Already Working**:
1. Orchestrator captures debate data (`core/agents/orchestrator.py:823-833`)
2. DecisionHistory stores debates in memory/Redis (`core/utils/decision_history.py`)
3. Data structure already defined (bull_argument, bear_argument, research_summary)
4. API endpoint exists (`/api/agents/debate/{symbol}`)
5. Methods for retrieval (`get_decisions`, `get_last_decision`)

❌ **Missing** (Needs implementation):
1. PostgreSQL table for agent_debates (not in `db/migrations/postgres/001_init_schema.sql`)
2. Database persistence layer (debates lost on restart with in-memory)
3. API endpoint returns mock data instead of real data
4. No pagination or filtering in API
5. No historical query support beyond Redis TTL (7 days)

---

## Current Implementation Details

### 1. Orchestrator Capture (`core/agents/orchestrator.py`)

**Status**: ✅ Fully Implemented

**Code** (lines 823-833):
```python
# Store decision in history for explainability
agent_debate = {
    "bull_argument": state.get("bull_argument", ""),
    "bear_argument": state.get("bear_argument", ""),
}

self.decision_history.add_decision(
    symbol=state['symbol'],
    decision=decision,
    agent_debate=agent_debate
)
```

**What's Captured**:
- Bull agent's buying case
- Bear agent's selling case
- Symbol and timestamp
- Decision and confidence
- Sentiment score

### 2. Decision History Storage (`core/utils/decision_history.py`)

**Status**: ⚠️ Partial (Memory/Redis only)

**Storage Backends**:
1. **In-Memory**: `dict[symbol, deque]` with max 10 per symbol (lost on restart)
2. **Redis**: Optional, with 7-day TTL (lost after expiry)
3. **PostgreSQL**: ❌ NOT IMPLEMENTED

**Methods Available**:
- `add_decision(symbol, decision, agent_debate)` - Stores debate
- `get_last_decision(symbol)` - Gets most recent
- `get_decisions(symbol, limit, since)` - Gets history
- `get_all_symbols()` - Lists symbols with history
- `format_decision_explanation(decision)` - Human-readable format

**Limitations**:
- Max 10 decisions per symbol (in-memory limit)
- 7-day TTL on Redis
- No permanent historical record
- Lost on system restart (without Redis)

### 3. API Endpoint (`ui/api/main.py`)

**Status**: ❌ Returns Mock Data

**Endpoint**: `GET /api/agents/debate/{symbol}`

**Current Behavior** (lines 606-677):
```python
@app.get("/api/agents/debate/{symbol}", tags=["Analysis"])
async def get_agent_debate(symbol: str):
    """Get multi-agent debate history for a specific symbol"""
    try:
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "debate": [
                {
                    "agent": "researcher",
                    "role": "market_intelligence",
                    "content": "Gathered 50+ data points...",  # MOCK DATA
                    ...
                }
            ]
        }
```

**What's Wrong**:
- Returns hard-coded mock data
- Doesn't query DecisionHistory
- Doesn't query database
- No pagination or filtering

### 4. Database Schema (`db/migrations/postgres/001_init_schema.sql`)

**Status**: ❌ No Table for Debates

**Existing Tables**:
- `symbols` - Trading pairs
- `orders` - Order execution
- `fills` - Trade fills
- `positions` - Current positions
- `balances` - Account balances
- `risk_events` - Risk management events
- `decision_events` - Decision layer events (but NOT full debates)

**Missing**: `agent_debates` table

**decision_events table** (lines 123-132):
```sql
CREATE TABLE IF NOT EXISTS decision_events (
    id BIGSERIAL PRIMARY KEY,
    layer INTEGER NOT NULL,  -- L0-L5
    symbol_id INTEGER REFERENCES symbols(symbol_id),
    action VARCHAR(50),  -- 'pass', 'modify', 'block'
    confidence NUMERIC(5, 4),
    metadata JSONB,  -- Could store debate data here, but not designed for it
    created_at_ns BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Problem**: This table is for decision layer events, not agent debates. It could store debates in the JSONB `metadata` field, but that's not optimal for querying.

---

## What Needs to Be Done

### Task 1: Create Database Migration (4 hours)

**File**: `db/migrations/postgres/002_agent_debates.sql`

**Schema**:
```sql
-- Agent debates table
CREATE TABLE IF NOT EXISTS agent_debates (
    id BIGSERIAL PRIMARY KEY,
    symbol_id INTEGER NOT NULL REFERENCES symbols(symbol_id),
    symbol VARCHAR(40) NOT NULL,  -- Denormalized for convenience

    -- Debate participants
    bull_argument TEXT,
    bear_argument TEXT,
    research_summary TEXT,
    technical_analysis JSONB,
    fundamental_analysis JSONB,

    -- Decision outcome
    final_decision VARCHAR(20) NOT NULL,  -- 'buy', 'sell', 'hold'
    confidence NUMERIC(5, 4),  -- 0.0 to 1.0
    sentiment NUMERIC(5, 4),   -- -1.0 to 1.0

    -- Metadata
    agent_scores JSONB,  -- Bull score, bear score, etc.
    reasoning JSONB,     -- Detailed reasoning from orchestrator

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at_ns BIGINT NOT NULL
);

-- Indexes for common queries
CREATE INDEX idx_agent_debates_symbol_id ON agent_debates(symbol_id);
CREATE INDEX idx_agent_debates_symbol ON agent_debates(symbol);
CREATE INDEX idx_agent_debates_created_at ON agent_debates(created_at DESC);
CREATE INDEX idx_agent_debates_final_decision ON agent_debates(final_decision);
```

**Run Migration**:
```bash
psql -U sigmax -d sigmax -f db/migrations/postgres/002_agent_debates.sql
```

### Task 2: Update DecisionHistory to Save to PostgreSQL (6 hours)

**File**: `core/utils/decision_history.py`

**Add Database Support**:
```python
class DecisionHistory:
    def __init__(self, max_history_per_symbol: int = 10, use_redis: bool = False, use_postgres: bool = True):
        self.use_postgres = use_postgres
        self.db_connection = None

        if use_postgres:
            # Initialize PostgreSQL connection pool
            self.db_connection = self._init_postgres()

    def add_decision(self, symbol: str, decision: Dict[str, Any], agent_debate: Optional[Dict[str, Any]] = None):
        # ... existing in-memory/Redis logic ...

        # NEW: Save to PostgreSQL
        if self.use_postgres and self.db_connection:
            self._save_to_postgres(symbol, decision, agent_debate)

    def _save_to_postgres(self, symbol: str, decision: Dict[str, Any], agent_debate: Dict[str, Any]):
        """Save debate to PostgreSQL"""
        # INSERT INTO agent_debates ...
        pass
```

**Alternative**: Create separate `AgentDebateRepository` class for database operations (cleaner separation).

### Task 3: Update API Endpoint to Query Real Data (4 hours)

**File**: `ui/api/main.py`

**Replace Mock Data**:
```python
@app.get("/api/agents/debate/{symbol}", tags=["Analysis"])
async def get_agent_debate(
    symbol: str,
    limit: int = 10,
    offset: int = 0,
    since: Optional[str] = None
):
    """
    Get multi-agent debate history for a specific symbol

    Query Parameters:
    - limit: Max number of debates to return (default: 10, max: 100)
    - offset: Pagination offset (default: 0)
    - since: ISO timestamp - only return debates after this time
    """
    try:
        manager = await get_sigmax_manager()
        decision_history = manager.get_decision_history()

        # Parse since timestamp if provided
        since_dt = None
        if since:
            since_dt = datetime.fromisoformat(since)

        # Query from database (or fallback to in-memory)
        debates = decision_history.get_decisions(
            symbol=symbol,
            limit=limit,
            since=since_dt
        )

        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "count": len(debates),
            "debates": debates,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(debates) == limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting debate for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch debate history")
```

### Task 4: Add Pagination and Filtering (2 hours)

**Query Parameters to Support**:
- `limit` - Max results (default: 10, max: 100)
- `offset` - Skip N results
- `since` - ISO timestamp filter
- `decision` - Filter by final_decision ('buy', 'sell', 'hold')
- `min_confidence` - Minimum confidence threshold

**Example**:
```bash
# Get last 10 debates for BTC/USDT
GET /api/agents/debate/BTC%2FUSDT?limit=10

# Get debates with buy decision and confidence > 0.7
GET /api/agents/debate/BTC%2FUSDT?decision=buy&min_confidence=0.7

# Get debates from last 24 hours
GET /api/agents/debate/BTC%2FUSDT?since=2024-12-20T00:00:00Z
```

---

## Revised Effort Estimate

| Task | Original Estimate | Actual Complexity | New Estimate |
|------|-------------------|-------------------|--------------|
| Initial assessment | 2h | Done | 1h (done) |
| Database schema | 4h | Straightforward | 4h |
| Capture debate data | 8h | Already done | 0h |
| API implementation | 8h | Partial | 6h |
| Testing | 8h | Reduced scope | 4h |
| Documentation | 2h | Quick updates | 1h |
| **Total** | **32h** | - | **16h** |

**Reduction**: 32 hours → 16 hours (50% complete already!)

---

## Testing Checklist

Before marking agent debate storage as complete:

- [ ] Run database migration
  ```bash
  psql -U sigmax -d sigmax -f db/migrations/postgres/002_agent_debates.sql
  ```

- [ ] Verify debate storage in database
  ```sql
  SELECT * FROM agent_debates ORDER BY created_at DESC LIMIT 5;
  ```

- [ ] Test API endpoint with real data
  ```bash
  curl -X POST http://localhost:8000/api/analyze \
    -H "X-API-Key: test-key" \
    -d '{"symbol": "BTC/USDT", "include_debate": true}'

  curl http://localhost:8000/api/agents/debate/BTC%2FUSDT
  ```

- [ ] Test pagination
  ```bash
  curl "http://localhost:8000/api/agents/debate/BTC%2FUSDT?limit=5&offset=0"
  curl "http://localhost:8000/api/agents/debate/BTC%2FUSDT?limit=5&offset=5"
  ```

- [ ] Test filtering
  ```bash
  curl "http://localhost:8000/api/agents/debate/BTC%2FUSDT?decision=buy&min_confidence=0.7"
  ```

- [ ] Verify data survives restart
  ```bash
  # 1. Run analysis to create debate
  # 2. Restart application
  # 3. Query debate - should still exist
  ```

---

## Success Criteria

✅ **Complete when**:
1. PostgreSQL table `agent_debates` created with proper schema
2. Orchestrator saves debates to database (in addition to memory/Redis)
3. API endpoint returns real debate data from database
4. Pagination works (limit, offset parameters)
5. Filtering works (since, decision, confidence)
6. Debates persist across application restarts
7. Historical debates queryable beyond 7-day Redis TTL

---

## Conclusion

**Actual Status**: Agent debate storage is 50% complete, not missing as originally thought. The orchestrator already captures debate data and stores it in memory/Redis.

**Original Audit Claim**: "API returns mock debate data, no database persistence"

**Reality**:
- ✅ Orchestrator captures debate data
- ✅ DecisionHistory stores in memory/Redis
- ❌ No PostgreSQL table (debates lost on restart)
- ❌ API returns mock data instead of querying real data

**Recommendation**:
- Spend 16 hours (not 32) on database schema and API integration
- Mark agent debate storage as "partially complete" in remediation plan
- Focus on PostgreSQL persistence to ensure historical data retention

---

**Document Version**: 1.0
**Assessment Date**: December 21, 2024
**Assessor**: Development Team
**Next Action**: Create PostgreSQL migration for agent_debates table
