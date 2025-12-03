# SIGMAX Security Remediation Plan

**Based on:** Security Audit Report (December 2, 2025)
**Total Issues:** 133+
**Estimated Effort:** 4-6 weeks with dedicated team

---

## Phase 1: Critical Security Fixes (P0)
**Timeline:** Immediate - Before any production deployment
**Effort:** 3-5 days

### 1.1 API Authentication Overhaul

#### Task 1.1.1: Require API Key in Production
**File:** `ui/api/main.py`
**Lines:** 95-112

**Current Code:**
```python
def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    api_key = os.getenv("SIGMAX_API_KEY")
    if not api_key:
        logger.warning("⚠️ No API key configured - running in open mode")
        return True  # DANGEROUS!
```

**Fix:**
```python
def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    api_key = os.getenv("SIGMAX_API_KEY")
    environment = os.getenv("ENVIRONMENT", "development")

    # Require API key in production
    if not api_key:
        if environment == "production":
            raise HTTPException(
                status_code=500,
                detail="Server configuration error: API key not configured"
            )
        logger.warning("⚠️ No API key configured - development mode only")
        return True

    if not credentials or not secrets.compare_digest(credentials.credentials, api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return True
```

**Additional Changes:**
- Add `import secrets` at top of file
- Use constant-time comparison to prevent timing attacks

---

#### Task 1.1.2: Add Authentication to WebSocket
**File:** `ui/api/main.py`
**Lines:** 699-712

**Current Code:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
```

**Fix:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """WebSocket endpoint with API key authentication"""
    api_key = os.getenv("SIGMAX_API_KEY")
    environment = os.getenv("ENVIRONMENT", "development")

    # Validate token in production
    if api_key and environment == "production":
        if not token or not secrets.compare_digest(token, api_key):
            await websocket.close(code=4001, reason="Unauthorized")
            return

    await manager.connect(websocket)
    try:
        # ... existing code
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Frontend Update Required:**
```typescript
// ui/web/src/hooks/useWebSocket.ts
const wsUrl = `${WS_BASE_URL}/ws?token=${API_KEY}`;
```

---

#### Task 1.1.3: Secure Exchange Credentials Endpoints
**File:** `ui/api/routes/exchanges.py`

**Current Code:**
```python
@router.get("/")
async def get_all_exchanges():
```

**Fix - Add auth dependency to router:**
```python
from ..main import verify_api_key

router = APIRouter(
    prefix="/api/exchanges",
    tags=["exchanges"],
    dependencies=[Depends(verify_api_key)]  # ADD THIS
)
```

---

### 1.2 Remove Unsafe Pickle Deserialization

#### Task 1.2.1: Replace Pickle with JSON
**File:** `core/utils/cache.py`

**Current Code (line 66):**
```python
return pickle.loads(value)
```

**Complete Rewrite:**
```python
import json
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib

class Cache:
    """Thread-safe cache with JSON serialization"""

    def __init__(self, redis_client=None, default_ttl: int = 3600):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self._local_cache: Dict[str, tuple] = {}  # (value, expiry)

    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string"""
        return json.dumps(value, default=str)

    def _deserialize(self, data: str) -> Any:
        """Deserialize JSON string to value"""
        return json.loads(data)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis:
            value = self.redis.get(key)
            if value:
                return self._deserialize(value.decode('utf-8'))
        else:
            # Local cache fallback
            if key in self._local_cache:
                value, expiry = self._local_cache[key]
                if expiry > datetime.now():
                    return value
                del self._local_cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        serialized = self._serialize(value)

        if self.redis:
            self.redis.setex(key, ttl, serialized)
        else:
            expiry = datetime.now() + timedelta(seconds=ttl)
            self._local_cache[key] = (value, expiry)
```

---

### 1.3 Remove Hardcoded Credentials

#### Task 1.3.1: Database Pool - Remove Default Password
**File:** `pkg/common/database_pool.py`
**Line:** 101

**Current Code:**
```python
database_url = os.getenv(
    "POSTGRES_URL",
    "postgresql+asyncpg://sigmax:password@localhost:5432/sigmax"
)
```

**Fix:**
```python
def get_database_url() -> str:
    """Get database URL from environment, fail if not configured"""
    database_url = os.getenv("POSTGRES_URL")
    if not database_url:
        raise RuntimeError(
            "POSTGRES_URL environment variable is required. "
            "Example: postgresql+asyncpg://user:pass@host:5432/db"
        )
    return database_url
```

---

#### Task 1.3.2: Health Check - Remove Default Password
**File:** `tools/health_check.py`
**Line:** 89

**Current Code:**
```python
password=os.getenv("POSTGRES_PASSWORD", "changeme"),
```

**Fix:**
```python
password = os.getenv("POSTGRES_PASSWORD")
if not password:
    raise ValueError("POSTGRES_PASSWORD environment variable is required")
```

---

#### Task 1.3.3: Docker Compose - Use Environment File
**File:** `docker-compose.yml`
**Line:** 120

**Current Code:**
```yaml
- POSTGRES_URL=${POSTGRES_URL:-postgresql://sigmax:changeme@postgres:5432/sigmax}
```

**Fix:**
```yaml
- POSTGRES_URL=${POSTGRES_URL:?POSTGRES_URL is required}
```

**Add to `.env.example`:**
```bash
# Required - Database connection
POSTGRES_URL=postgresql://sigmax:YOUR_SECURE_PASSWORD@postgres:5432/sigmax
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD

# Required - API Security
SIGMAX_API_KEY=your-secure-api-key-here

# Required - Encryption
EXCHANGE_ENCRYPTION_KEY=  # Will be auto-generated if empty
```

---

#### Task 1.3.4: Freqtrade Config - Remove Placeholder Secrets
**File:** `trading/freqtrade/config.json`

**Create:** `trading/freqtrade/config.example.json` with placeholders
**Update:** `trading/freqtrade/config.json` to `.gitignore`

**Template:**
```json
{
    "api_server": {
        "enabled": true,
        "jwt_secret_key": "${FREQTRADE_JWT_SECRET}",
        "ws_token": "${FREQTRADE_WS_TOKEN}",
        "username": "admin",
        "password": "${FREQTRADE_PASSWORD}"
    }
}
```

---

### 1.4 Fix Error Information Disclosure

#### Task 1.4.1: Create Safe Error Handler
**File:** `ui/api/middleware/error_handler.py` (NEW FILE)

```python
"""Centralized error handling to prevent information disclosure"""
import traceback
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os

logger = logging.getLogger(__name__)

class SafeErrorMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize error responses"""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            raise  # Let FastAPI handle HTTP exceptions
        except Exception as e:
            # Log full error server-side
            logger.error(
                f"Unhandled error: {e}\n{traceback.format_exc()}",
                extra={"path": request.url.path, "method": request.method}
            )

            # Return safe error to client
            is_debug = os.getenv("DEBUG", "false").lower() == "true"
            is_dev = os.getenv("ENVIRONMENT", "development") == "development"

            if is_debug and is_dev:
                detail = str(e)
            else:
                detail = "An internal error occurred. Please try again later."

            return JSONResponse(
                status_code=500,
                content={"detail": detail, "error_id": id(e)}
            )


def safe_error_detail(e: Exception) -> str:
    """Get safe error message for HTTP responses"""
    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"

    if is_debug and is_dev:
        return str(e)
    return "An error occurred processing your request"
```

#### Task 1.4.2: Update All Endpoints to Use Safe Errors
**Files:** `ui/api/main.py`, `ui/api/routes/exchanges.py`

**Pattern to find and replace:**
```python
# BEFORE
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# AFTER
from .middleware.error_handler import safe_error_detail

except Exception as e:
    logger.error(f"Error in endpoint: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=safe_error_detail(e))
```

---

## Phase 2: Financial Precision Fixes (P0)
**Timeline:** Week 1-2
**Effort:** 5-7 days

### 2.1 Create Decimal Types Module

#### Task 2.1.1: Create Financial Types
**File:** `pkg/schemas/financial_types.py` (NEW FILE)

```python
"""Financial types with proper precision handling"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from typing import Union
from pydantic import BaseModel, field_validator

# Precision constants
PRICE_PRECISION = Decimal('0.00000001')  # 8 decimals (satoshi)
QTY_PRECISION = Decimal('0.00000001')    # 8 decimals
USD_PRECISION = Decimal('0.01')          # 2 decimals
BPS_PRECISION = Decimal('0.01')          # Basis points


def to_decimal(value: Union[float, int, str, Decimal]) -> Decimal:
    """Safely convert any numeric to Decimal"""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_price(value: Union[float, Decimal], precision: Decimal = PRICE_PRECISION) -> Decimal:
    """Round price to specified precision"""
    return to_decimal(value).quantize(precision, rounding=ROUND_HALF_UP)


def round_qty(value: Union[float, Decimal], precision: Decimal = QTY_PRECISION) -> Decimal:
    """Round quantity down to prevent over-ordering"""
    return to_decimal(value).quantize(precision, rounding=ROUND_DOWN)


def round_usd(value: Union[float, Decimal]) -> Decimal:
    """Round USD amount to cents"""
    return to_decimal(value).quantize(USD_PRECISION, rounding=ROUND_HALF_UP)


def calculate_notional(qty: Decimal, price: Decimal) -> Decimal:
    """Calculate notional value with proper rounding"""
    return round_usd(qty * price)


def calculate_fee(notional: Decimal, fee_rate: Decimal) -> Decimal:
    """Calculate fee with proper rounding"""
    return round_usd(notional * fee_rate)


def calculate_pnl(entry_price: Decimal, exit_price: Decimal, qty: Decimal, fees: Decimal = Decimal('0')) -> Decimal:
    """Calculate P&L with proper precision"""
    gross_pnl = (exit_price - entry_price) * qty
    return round_usd(gross_pnl - fees)


def bps_to_decimal(bps: Union[float, Decimal]) -> Decimal:
    """Convert basis points to decimal (e.g., 50 bps -> 0.005)"""
    return to_decimal(bps) / Decimal('10000')


class DecimalPrice(Decimal):
    """Price type with validation"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v is None:
            return None
        d = to_decimal(v)
        if d < 0:
            raise ValueError("Price cannot be negative")
        return round_price(d)


class DecimalQty(Decimal):
    """Quantity type with validation"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if v is None:
            return None
        d = to_decimal(v)
        if d < 0:
            raise ValueError("Quantity cannot be negative")
        return round_qty(d)
```

---

#### Task 2.1.2: Update Order Schema
**File:** `pkg/schemas/orders.py`

**Current Code:**
```python
class OrderIntent(BaseModel):
    qty: float
    price: Optional[float] = None
```

**Fix:**
```python
from decimal import Decimal
from .financial_types import DecimalPrice, DecimalQty, round_price, round_qty

class OrderIntent(BaseModel):
    qty: Decimal
    price: Optional[Decimal] = None

    @field_validator('qty', mode='before')
    @classmethod
    def validate_qty(cls, v):
        if v is None:
            return None
        return round_qty(Decimal(str(v)))

    @field_validator('price', mode='before')
    @classmethod
    def validate_price(cls, v):
        if v is None:
            return None
        return round_price(Decimal(str(v)))

    @property
    def notional(self) -> Optional[Decimal]:
        """Calculate notional value"""
        if self.price is None:
            return None
        return round_usd(self.qty * self.price)
```

---

#### Task 2.1.3: Update Risk Engine
**File:** `apps/risk/risk_engine.py`

**Current Code (line 165):**
```python
order_notional = order.qty * order.price
```

**Fix:**
```python
from pkg.schemas.financial_types import calculate_notional, to_decimal

order_notional = calculate_notional(to_decimal(order.qty), to_decimal(order.price))
```

---

#### Task 2.1.4: Update Execution Module
**File:** `core/modules/execution.py`

**Current Code (lines 186-188):**
```python
cost = size * price
self.paper_balance[quote] -= cost
```

**Fix:**
```python
from pkg.schemas.financial_types import calculate_notional, to_decimal, round_usd

cost = calculate_notional(to_decimal(size), to_decimal(price))
current_balance = to_decimal(self.paper_balance.get(quote, 0))
if current_balance >= cost:
    self.paper_balance[quote] = float(current_balance - cost)  # Store as float for JSON compat
```

---

#### Task 2.1.5: Update Backtest Module
**File:** `core/modules/backtest.py`

**Current Code (lines 158-189):**
```python
entry_price = current_price * (1 + self.slippage)
cost = size * entry_price
fees = cost * self.commission
# ...
trade.pnl = (exit_price - trade.entry_price) * trade.size - trade.fees - fees
trade.pnl_pct = ((exit_price / trade.entry_price) - 1) * 100
```

**Fix:**
```python
from decimal import Decimal
from pkg.schemas.financial_types import (
    to_decimal, round_price, round_usd,
    calculate_notional, calculate_fee, calculate_pnl
)

# Entry
entry_price = round_price(to_decimal(current_price) * (Decimal('1') + to_decimal(self.slippage)))
cost = calculate_notional(to_decimal(size), entry_price)
fees = calculate_fee(cost, to_decimal(self.commission))

# Exit
exit_price = round_price(to_decimal(current_price) * (Decimal('1') - to_decimal(self.slippage)))
proceeds = calculate_notional(to_decimal(trade.size), exit_price)
exit_fees = calculate_fee(proceeds, to_decimal(self.commission))

# P&L
trade.pnl = float(calculate_pnl(
    to_decimal(trade.entry_price),
    exit_price,
    to_decimal(trade.size),
    to_decimal(trade.fees) + exit_fees
))

if trade.entry_price > 0:
    trade.pnl_pct = float(
        ((exit_price / to_decimal(trade.entry_price)) - Decimal('1')) * Decimal('100')
    )
```

---

## Phase 3: Async & Connection Fixes (P1)
**Timeline:** Week 2-3
**Effort:** 4-5 days

### 3.1 Fix Blocking I/O in Async Contexts

#### Task 3.1.1: Replace psycopg2 with asyncpg in Health Check
**File:** `core/utils/healthcheck.py`

**Current Code (lines 154-162):**
```python
async def _check_postgres(self) -> HealthStatus:
    conn = psycopg2.connect(db_url, connect_timeout=5)  # BLOCKING!
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
```

**Fix:**
```python
import asyncpg

async def _check_postgres(self) -> HealthStatus:
    """Check PostgreSQL connectivity using async driver"""
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(db_url),
            timeout=5.0
        )
        try:
            result = await conn.fetchval("SELECT 1")
            return HealthStatus(
                name="postgres",
                status="healthy" if result == 1 else "degraded",
                latency_ms=(time.time() - start) * 1000
            )
        finally:
            await conn.close()
    except asyncio.TimeoutError:
        return HealthStatus(name="postgres", status="unhealthy", error="Connection timeout")
    except Exception as e:
        return HealthStatus(name="postgres", status="unhealthy", error=str(e))
```

---

#### Task 3.1.2: Fix psutil Blocking Call
**File:** `core/modules/performance_monitor.py`

**Current Code (line 153):**
```python
async def _collect_system_metrics(self):
    self.system_metrics.cpu_percent = psutil.cpu_percent(interval=1)  # BLOCKS 1 SECOND!
```

**Fix:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class PerformanceMonitor:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="metrics")

    async def _collect_system_metrics(self):
        """Collect system metrics in thread pool to avoid blocking"""
        loop = asyncio.get_event_loop()

        # Run blocking calls in executor
        cpu_percent = await loop.run_in_executor(
            self._executor,
            lambda: psutil.cpu_percent(interval=1)
        )

        memory = await loop.run_in_executor(
            self._executor,
            psutil.virtual_memory
        )

        self.system_metrics.cpu_percent = cpu_percent
        self.system_metrics.memory_percent = memory.percent
```

---

#### Task 3.1.3: Fix Sync DB Lookup in Feed Manager
**File:** `apps/ingest_cex/feed_manager.py`

**Current Code (lines 337-347):**
```python
def _lookup_symbol_from_db(self, symbol: str) -> Optional[int]:
    conn = psycopg2.connect(db_url)  # BLOCKING!
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM symbols WHERE name = %s LIMIT 1", (symbol,))
```

**Fix:**
```python
import asyncpg
from typing import Dict

class FeedManager:
    def __init__(self):
        self._symbol_cache: Dict[str, int] = {}
        self._db_pool: Optional[asyncpg.Pool] = None

    async def _get_db_pool(self) -> asyncpg.Pool:
        if self._db_pool is None:
            self._db_pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=5
            )
        return self._db_pool

    async def _lookup_symbol_from_db(self, symbol: str) -> Optional[int]:
        """Async symbol lookup with caching"""
        # Check cache first
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]

        try:
            pool = await self._get_db_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT id FROM symbols WHERE name = $1 LIMIT 1",
                    symbol
                )
                if result is not None:
                    self._symbol_cache[symbol] = result
                return result
        except Exception as e:
            self.logger.debug("db_lookup_error", symbol=symbol, error=str(e))
            return None
```

---

### 3.2 Fix Connection Leaks

#### Task 3.2.1: Add Context Managers
**Files:** `apps/book_shard/book_manager.py`, `apps/ingest_cex/feed_manager.py`

**Pattern to apply:**
```python
# BEFORE
conn = psycopg2.connect(db_url)
cursor = conn.cursor()
cursor.execute(...)
result = cursor.fetchone()
cursor.close()
conn.close()

# AFTER
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(db_url)
    try:
        yield conn
    finally:
        conn.close()

# Usage
with get_db_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(...)
        result = cursor.fetchone()
```

---

### 3.3 Add Async Locks for Shared State

#### Task 3.3.1: Protect Shared Collections
**File:** `apps/signals/listings_watcher/main.py`

**Current Code:**
```python
class ListingsWatcher:
    def __init__(self):
        self.known_symbols = set()  # UNPROTECTED
```

**Fix:**
```python
import asyncio

class ListingsWatcher:
    def __init__(self):
        self._known_symbols: set = set()
        self._symbols_lock = asyncio.Lock()

    async def get_known_symbols(self) -> set:
        async with self._symbols_lock:
            return self._known_symbols.copy()

    async def update_known_symbols(self, symbols: set) -> set:
        """Update known symbols and return new ones"""
        async with self._symbols_lock:
            new_symbols = symbols - self._known_symbols
            self._known_symbols.update(symbols)
            return new_symbols
```

---

### 3.4 Add Error Callbacks to Async Tasks

#### Task 3.4.1: Create Task Wrapper Utility
**File:** `pkg/common/async_utils.py` (NEW FILE)

```python
"""Async utilities for safe task management"""
import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)


def create_monitored_task(
    coro: Coroutine,
    name: str,
    on_error: Callable[[Exception], None] = None
) -> asyncio.Task:
    """Create an async task with error monitoring"""
    task = asyncio.create_task(coro, name=name)

    def _done_callback(t: asyncio.Task):
        try:
            exc = t.exception()
            if exc:
                logger.error(f"Task '{name}' failed with error: {exc}", exc_info=exc)
                if on_error:
                    on_error(exc)
        except asyncio.CancelledError:
            logger.info(f"Task '{name}' was cancelled")

    task.add_done_callback(_done_callback)
    return task
```

**Usage in `ui/api/sigmax_manager.py`:**
```python
from pkg.common.async_utils import create_monitored_task

async def initialize(self):
    # BEFORE
    asyncio.create_task(self._sigmax.start())

    # AFTER
    create_monitored_task(
        self._sigmax.start(),
        name="sigmax-core",
        on_error=lambda e: logger.critical(f"SIGMAX core crashed: {e}")
    )
```

---

## Phase 4: Database & Performance (P1)
**Timeline:** Week 3
**Effort:** 2-3 days

### 4.1 Add Missing Database Indexes

#### Task 4.1.1: Create Migration File
**File:** `db/migrations/postgres/002_add_missing_indexes.sql` (NEW FILE)

```sql
-- Migration: Add missing indexes for performance
-- Date: 2025-12-02

-- Risk events by symbol (for filtering)
CREATE INDEX IF NOT EXISTS idx_risk_events_symbol_id
ON risk_events(symbol_id);

-- Decision events by symbol (for querying)
CREATE INDEX IF NOT EXISTS idx_decision_events_symbol_id
ON decision_events(symbol_id);

-- Fills by trade_id (for reconciliation)
CREATE INDEX IF NOT EXISTS idx_fills_trade_id
ON fills(trade_id);

-- Orders by route (for venue analytics)
CREATE INDEX IF NOT EXISTS idx_orders_route
ON orders(route);

-- Composite index for client date range queries
CREATE INDEX IF NOT EXISTS idx_fills_client_created
ON fills(client_id, created_at DESC);

-- Composite index for symbol + time queries
CREATE INDEX IF NOT EXISTS idx_risk_events_symbol_created
ON risk_events(symbol_id, created_at DESC);

-- Partial index for active orders only
CREATE INDEX IF NOT EXISTS idx_orders_active
ON orders(client_id, created_at DESC)
WHERE status IN ('pending', 'open', 'partial');

-- Add index statistics comment
COMMENT ON INDEX idx_risk_events_symbol_id IS 'Added 2025-12-02 per audit findings';
```

---

### 4.2 Add ClickHouse Connection Pooling

#### Task 4.2.1: Update ClickHouse Client
**File:** `pkg/common/database_pool.py`

**Add connection pooling:**
```python
from clickhouse_pool import ChPool

_clickhouse_pool: Optional[ChPool] = None

def get_clickhouse_pool(
    host: str = None,
    port: int = 9000,
    database: str = "default",
    pool_size: int = 10
) -> ChPool:
    """Get or create ClickHouse connection pool"""
    global _clickhouse_pool

    if _clickhouse_pool is None:
        host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        _clickhouse_pool = ChPool(
            host=host,
            port=port,
            database=database,
            connections_min=2,
            connections_max=pool_size
        )

    return _clickhouse_pool
```

---

## Phase 5: Code Quality Fixes (P2)
**Timeline:** Week 3-4
**Effort:** 3-4 days

### 5.1 Fix Bare Exception Clause

#### Task 5.1.1: Update ZKML Compliance
**File:** `core/modules/zkml_compliance.py`
**Line:** 440

**Current Code:**
```python
except:
    return False
```

**Fix:**
```python
except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as e:
    logger.warning(f"Failed to parse proof data: {e}")
    return False
```

---

### 5.2 Add Null/Bounds Checks

#### Task 5.2.1: Create Validation Utilities
**File:** `pkg/common/validation.py` (NEW FILE)

```python
"""Common validation utilities"""
from typing import List, Optional, TypeVar, Sequence

T = TypeVar('T')


def safe_get_last(seq: Sequence[T], default: T = None) -> Optional[T]:
    """Safely get last element of sequence"""
    if seq and len(seq) > 0:
        return seq[-1]
    return default


def safe_get_index(seq: Sequence[T], index: int, default: T = None) -> Optional[T]:
    """Safely get element at index"""
    if seq and -len(seq) <= index < len(seq):
        return seq[index]
    return default


def require_length(seq: Sequence, min_length: int, name: str = "sequence") -> None:
    """Raise if sequence is too short"""
    if len(seq) < min_length:
        raise ValueError(f"{name} requires at least {min_length} elements, got {len(seq)}")


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default for zero denominator"""
    if denominator == 0:
        return default
    return numerator / denominator
```

---

#### Task 5.2.2: Update Regime Detector
**File:** `core/modules/regime_detector.py`

**Current Code (lines 118-128):**
```python
current_price = prices[-1]
sma_20 = calculate_sma(prices, 20)
# ...
momentum = sma_20[-1]
```

**Fix:**
```python
from pkg.common.validation import require_length, safe_get_last

def analyze_regime(self, prices: List[float], volumes: List[float]) -> str:
    # Validate inputs
    require_length(prices, 50, "prices")  # Need at least 50 for SMA50
    require_length(volumes, 20, "volumes")

    current_price = prices[-1]  # Safe now due to validation

    sma_20 = calculate_sma(prices, 20)
    sma_50 = calculate_sma(prices, 50)

    # Use safe access for calculated arrays
    sma_20_current = safe_get_last(sma_20, current_price)
    sma_50_current = safe_get_last(sma_50, current_price)
```

---

### 5.3 Add Division Guards

#### Task 5.3.1: Update Analyzer
**File:** `core/agents/analyzer.py`

**Current Code (line 334):**
```python
price_similarity = abs(peak1_price - peak2_price) / peak1_price
```

**Fix:**
```python
from pkg.common.validation import safe_divide

price_similarity = safe_divide(
    abs(peak1_price - peak2_price),
    peak1_price,
    default=1.0  # Maximum dissimilarity if price is 0
)
```

---

## Phase 6: Security Hardening (P2)
**Timeline:** Week 4
**Effort:** 2-3 days

### 6.1 Add Security Headers

#### Task 6.1.1: Create Security Headers Middleware
**File:** `ui/api/middleware/security_headers.py` (NEW FILE)

```python
"""Security headers middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:;"
        )

        # HSTS (only in production with HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
```

**Add to `ui/api/main.py`:**
```python
from .middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

---

### 6.2 Disable Docs in Production

#### Task 6.2.1: Conditional Documentation
**File:** `ui/api/main.py`

**Current Code:**
```python
app = FastAPI(
    title="SIGMAX API",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

**Fix:**
```python
import os

environment = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="SIGMAX API",
    docs_url="/docs" if environment != "production" else None,
    redoc_url="/redoc" if environment != "production" else None,
    openapi_url="/openapi.json" if environment != "production" else None,
)
```

---

### 6.3 Implement API Key Rotation

#### Task 6.3.1: Support Multiple API Keys
**File:** `ui/api/main.py`

```python
def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Verify API key with support for rotation"""
    # Support multiple keys for rotation
    primary_key = os.getenv("SIGMAX_API_KEY")
    secondary_key = os.getenv("SIGMAX_API_KEY_SECONDARY")  # For rotation

    valid_keys = [k for k in [primary_key, secondary_key] if k]

    if not valid_keys:
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            raise HTTPException(status_code=500, detail="Server configuration error")
        return True

    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")

    # Use constant-time comparison
    for key in valid_keys:
        if secrets.compare_digest(credentials.credentials, key):
            return True

    raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## Testing Checklist

### Security Tests
- [ ] API returns 401 without valid API key
- [ ] WebSocket rejects unauthenticated connections
- [ ] Exchange endpoints require authentication
- [ ] Error responses don't leak internal details
- [ ] No hardcoded credentials in codebase

### Financial Precision Tests
- [ ] P&L calculations match expected Decimal results
- [ ] Fee calculations round correctly
- [ ] Position sizing uses proper rounding
- [ ] Cumulative calculations don't drift

### Async Tests
- [ ] No blocking calls in async functions
- [ ] Shared state properly locked
- [ ] Tasks have error handling
- [ ] Connections properly cleaned up

### Performance Tests
- [ ] Database queries use indexes
- [ ] Connection pools configured correctly
- [ ] No connection leaks under load

---

## Deployment Checklist

### Pre-deployment
- [ ] All critical fixes implemented
- [ ] Security tests passing
- [ ] `.env` properly configured (no defaults)
- [ ] API key set and secure
- [ ] Database passwords changed from defaults
- [ ] HTTPS configured

### Post-deployment
- [ ] API docs disabled in production
- [ ] Security headers present
- [ ] Error responses sanitized
- [ ] Monitoring active
- [ ] Backup/recovery tested

---

## Summary

| Phase | Focus | Effort | Priority |
|-------|-------|--------|----------|
| 1 | Critical Security | 3-5 days | P0 |
| 2 | Financial Precision | 5-7 days | P0 |
| 3 | Async & Connections | 4-5 days | P1 |
| 4 | Database Performance | 2-3 days | P1 |
| 5 | Code Quality | 3-4 days | P2 |
| 6 | Security Hardening | 2-3 days | P2 |
| **Total** | | **19-27 days** | |

---

**Document Version:** 1.0
**Last Updated:** December 2, 2025
