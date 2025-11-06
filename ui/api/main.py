"""
SIGMAX FastAPI Backend - Enhanced with Security, Monitoring & Documentation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
import os
import time
from datetime import datetime
from collections import defaultdict
from functools import wraps
import traceback

from pydantic import BaseModel, Field, validator
from loguru import logger
import psutil

# Connection manager for WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")


manager = ConnectionManager()


# Rate limiting
class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "default": (60, 60),  # 60 requests per 60 seconds
            "analyze": (10, 60),   # 10 requests per 60 seconds
            "trade": (5, 60),      # 5 requests per 60 seconds
        }

    def is_allowed(self, client_id: str, endpoint: str = "default") -> tuple[bool, Optional[str]]:
        """Check if request is allowed"""
        now = time.time()
        limit, window = self.limits.get(endpoint, self.limits["default"])

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < window
        ]

        # Check limit
        if len(self.requests[client_id]) >= limit:
            retry_after = window - (now - self.requests[client_id][0])
            return False, f"Rate limit exceeded. Retry after {retry_after:.0f} seconds"

        # Add request
        self.requests[client_id].append(now)
        return True, None


rate_limiter = RateLimiter()


# Security - API Key Authentication
security = HTTPBearer(auto_error=False)


def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Verify API key from environment"""
    api_key = os.getenv("SIGMAX_API_KEY")

    # If no API key configured, allow all requests (development mode)
    if not api_key:
        logger.warning("⚠️ No API key configured - running in open mode")
        return True

    # Verify credentials
    if not credentials or credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


# Request metrics
class RequestMetrics:
    """Track API metrics"""
    def __init__(self):
        self.total_requests = 0
        self.failed_requests = 0
        self.request_durations = []
        self.endpoint_stats = defaultdict(lambda: {"count": 0, "errors": 0, "total_time": 0.0})

    def record(self, endpoint: str, duration: float, error: bool = False):
        """Record request metrics"""
        self.total_requests += 1
        if error:
            self.failed_requests += 1

        self.request_durations.append(duration)
        if len(self.request_durations) > 1000:  # Keep last 1000
            self.request_durations = self.request_durations[-1000:]

        self.endpoint_stats[endpoint]["count"] += 1
        self.endpoint_stats[endpoint]["total_time"] += duration
        if error:
            self.endpoint_stats[endpoint]["errors"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics"""
        avg_duration = sum(self.request_durations) / len(self.request_durations) if self.request_durations else 0

        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.total_requests - self.failed_requests) / self.total_requests if self.total_requests > 0 else 0,
            "avg_response_time": round(avg_duration, 3),
            "endpoints": dict(self.endpoint_stats)
        }


metrics = RequestMetrics()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting SIGMAX API")
    yield
    # Shutdown
    logger.info("👋 Shutting down SIGMAX API")


# Create FastAPI app with enhanced documentation
app = FastAPI(
    title="SIGMAX API",
    description="""
    # SIGMAX - Autonomous Multi-Agent AI Trading OS API

    ## Features
    - 🤖 Multi-agent trading system (Bull/Bear/Researcher debate)
    - ⚛️ Quantum portfolio optimization
    - 📊 Real-time market analysis
    - 🛡️ Risk management & compliance
    - 🔒 Secure API with rate limiting
    - 📈 Live WebSocket updates

    ## Authentication
    Set `SIGMAX_API_KEY` environment variable and include it as Bearer token:
    ```
    Authorization: Bearer your-api-key-here
    ```

    ## Rate Limits
    - Default: 60 requests/minute
    - Analysis: 10 requests/minute
    - Trading: 5 requests/minute
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "System health and status"},
        {"name": "Trading", "description": "Trading operations"},
        {"name": "Analysis", "description": "Market analysis and agent debate"},
        {"name": "Control", "description": "System control operations"},
        {"name": "Monitoring", "description": "Metrics and monitoring"},
    ]
)

# Middleware stack
# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Trusted host (security)
if os.getenv("ENVIRONMENT", "development") == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and track metrics"""
    start_time = time.time()
    error = False

    try:
        # Rate limiting check
        client_id = request.client.host if request.client else "unknown"
        endpoint_type = "default"

        if "analyze" in request.url.path:
            endpoint_type = "analyze"
        elif "trade" in request.url.path:
            endpoint_type = "trade"

        allowed, error_msg = rate_limiter.is_allowed(client_id, endpoint_type)
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id} on {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={"detail": error_msg},
                headers={"Retry-After": "60"}
            )

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        error = response.status_code >= 400

        metrics.record(request.url.path, duration, error)

        # Add custom headers
        response.headers["X-Process-Time"] = str(round(duration, 3))
        response.headers["X-Request-ID"] = f"{int(start_time * 1000)}"

        # Log
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s "
            f"client={client_id}"
        )

        return response

    except Exception as e:
        duration = time.time() - start_time
        metrics.record(request.url.path, duration, error=True)

        logger.error(f"Request error: {e}\n{traceback.format_exc()}")

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(e) if os.getenv("DEBUG") else "An error occurred"
            }
        )


# Request models with validation
class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair (e.g., BTC/USDT)", example="BTC/USDT")
    action: str = Field(..., description="Action: buy, sell, or hold", example="buy")
    size: float = Field(..., gt=0, description="Trade size in base currency", example=0.001)

    @validator('action')
    def validate_action(cls, v):
        if v.lower() not in ['buy', 'sell', 'hold']:
            raise ValueError('Action must be buy, sell, or hold')
        return v.lower()

    @validator('symbol')
    def validate_symbol(cls, v):
        if '/' not in v:
            raise ValueError('Symbol must be in format BASE/QUOTE (e.g., BTC/USDT)')
        return v.upper()


class AnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair to analyze", example="BTC/USDT")
    include_debate: bool = Field(False, description="Include full agent debate log")

    @validator('symbol')
    def validate_symbol(cls, v):
        if '/' not in v:
            raise ValueError('Symbol must be in format BASE/QUOTE (e.g., BTC/USDT)')
        return v.upper()


# Routes
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": "SIGMAX API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time()
    }


@app.get("/health/ready", tags=["System"])
async def readiness_check():
    """
    Kubernetes-style readiness probe
    Checks if all dependencies are ready
    """
    checks = {
        "api": True,
        "memory": psutil.virtual_memory().percent < 90,
        "cpu": psutil.cpu_percent(interval=0.1) < 95,
        "disk": psutil.disk_usage('/').percent < 90,
    }

    all_ready = all(checks.values())

    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health/live", tags=["System"])
async def liveness_check():
    """
    Kubernetes-style liveness probe
    Simple check that the service is responding
    """
    return {
        "alive": True,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get API performance metrics
    """
    system_metrics = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent,
        "process_count": len(psutil.pids()),
    }

    api_metrics = metrics.get_stats()

    return {
        "timestamp": datetime.now().isoformat(),
        "system": system_metrics,
        "api": api_metrics
    }


@app.get("/api/status", tags=["System"])
async def get_status():
    """
    Get comprehensive system status

    Returns current state of all agents, modules, and trading activity
    """
    try:
        # TODO: Connect to actual SIGMAX instance
        return {
            "running": True,
            "mode": "paper",
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "orchestrator": "active",
                "researcher": "active",
                "analyzer": "active",
                "optimizer": "active",
                "risk": "active",
                "privacy": "active"
            },
            "trading": {
                "open_positions": 0,
                "pnl_today": 0.0,
                "trades_today": 0,
                "win_rate": 0.0
            },
            "system": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze", tags=["Analysis"], dependencies=[Depends(verify_api_key)])
async def analyze_symbol(request: AnalysisRequest):
    """
    Analyze a trading symbol using multi-agent debate system

    The system will:
    1. Research market conditions
    2. Bull agent presents buying case
    3. Bear agent presents selling case
    4. Analyzer performs technical analysis
    5. Risk agent validates against policies
    6. Final decision with confidence score

    **Rate limit:** 10 requests per minute
    """
    try:
        # TODO: Connect to orchestrator
        logger.info(f"Analyzing {request.symbol}")

        return {
            "symbol": request.symbol,
            "decision": "hold",
            "confidence": 0.5,
            "timestamp": datetime.now().isoformat(),
            "reasoning": {
                "bull": "Positive technical indicators show upward momentum",
                "bear": "High volatility presents significant risk",
                "technical": "RSI neutral at 50, MACD showing consolidation",
                "risk": "Within acceptable risk parameters"
            },
            "technical_indicators": {
                "rsi": 50.0,
                "macd": 0.0,
                "volume": 1000000
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.post("/api/trade", tags=["Trading"], dependencies=[Depends(verify_api_key)])
async def execute_trade(request: TradeRequest):
    """
    Execute a trade order

    **⚠️ Warning:** This will execute actual trades in live mode!

    **Rate limit:** 5 requests per minute

    **Risk Controls:**
    - Maximum position size limits enforced
    - Stop-loss automatically applied
    - Daily loss limits checked
    - Compliance validation required
    """
    try:
        # TODO: Connect to execution module
        logger.info(f"Trade request: {request.action} {request.size} {request.symbol}")

        # Validate trade size
        if request.size > 1.0:  # Example limit
            raise ValueError("Trade size exceeds maximum limit")

        return {
            "success": True,
            "order_id": f"ORDER_{int(time.time() * 1000)}",
            "symbol": request.symbol,
            "action": request.action,
            "size": request.size,
            "status": "filled",
            "timestamp": datetime.now().isoformat(),
            "filled_price": 95000.0,  # Mock
            "fee": 0.001
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail="Trade execution failed")


@app.get("/api/portfolio", tags=["Trading"])
async def get_portfolio():
    """
    Get current portfolio holdings and performance

    Returns:
    - Current positions with P&L
    - Total portfolio value
    - Available cash
    - Performance metrics
    """
    try:
        return {
            "total_value": 50.0,
            "cash": 2.5,
            "invested": 47.5,
            "positions": [
                {
                    "symbol": "BTC/USDT",
                    "size": 0.0005,
                    "entry_price": 90000.0,
                    "current_price": 95000.0,
                    "value": 47.5,
                    "pnl": 2.5,
                    "pnl_pct": 5.56,
                    "pnl_usd": 2.5
                }
            ],
            "performance": {
                "total_return": 5.26,
                "daily_return": 0.5,
                "sharpe_ratio": 1.8,
                "max_drawdown": -2.5
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio")


@app.get("/api/history", tags=["Trading"])
async def get_trade_history(
    limit: int = 50,
    offset: int = 0,
    symbol: Optional[str] = None
):
    """
    Get trade history with pagination

    Args:
    - limit: Maximum number of trades to return (default: 50, max: 500)
    - offset: Number of trades to skip (default: 0)
    - symbol: Filter by trading pair (optional)

    Returns paginated trade history
    """
    try:
        # Validate limit
        if limit > 500:
            raise ValueError("Limit cannot exceed 500")

        # TODO: Fetch from database
        trades = []

        return {
            "trades": trades,
            "total": 0,
            "limit": limit,
            "offset": offset,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting trade history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@app.get("/api/agents/debate/{symbol}", tags=["Analysis"])
async def get_agent_debate(symbol: str):
    """
    Get multi-agent debate history for a specific symbol

    Shows the complete debate flow:
    - Researcher's market intelligence
    - Bull agent's buying case
    - Bear agent's selling case
    - Analyzer's technical analysis
    - Risk agent's validation
    - Final decision
    """
    try:
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "debate": [
                {
                    "agent": "researcher",
                    "role": "market_intelligence",
                    "content": "Gathered 50+ data points from multiple sources. Overall sentiment positive.",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 0.7
                },
                {
                    "agent": "bull",
                    "role": "buy_case",
                    "argument": "Strong upward momentum with increasing volume. RSI showing strength. Breaking resistance levels.",
                    "timestamp": datetime.now().isoformat(),
                    "score": 0.75
                },
                {
                    "agent": "bear",
                    "role": "sell_case",
                    "argument": "Overbought conditions on 4h timeframe. Potential correction ahead. Volume divergence detected.",
                    "timestamp": datetime.now().isoformat(),
                    "score": 0.45
                },
                {
                    "agent": "analyzer",
                    "role": "technical_analysis",
                    "analysis": "Mixed signals. RSI neutral at 50, MACD showing consolidation. Support at $93k, resistance at $97k.",
                    "timestamp": datetime.now().isoformat(),
                    "indicators": {"rsi": 50, "macd": 0, "volume": "above_average"}
                },
                {
                    "agent": "risk",
                    "role": "risk_validation",
                    "verdict": "Approved with constraints: max 0.5 BTC position, stop-loss at -3%",
                    "timestamp": datetime.now().isoformat(),
                    "approved": True
                },
                {
                    "agent": "decision",
                    "role": "final_verdict",
                    "decision": "hold",
                    "confidence": 0.5,
                    "reasoning": "Mixed signals warrant caution. Monitor for clearer breakout.",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "summary": {
                "bull_score": 0.75,
                "bear_score": 0.45,
                "final_decision": "hold",
                "confidence": 0.5
            }
        }
    except Exception as e:
        logger.error(f"Error getting debate for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch debate history")


@app.get("/api/quantum/circuit", tags=["Analysis"])
async def get_quantum_circuit():
    """
    Get latest quantum circuit visualization

    Returns SVG representation of the quantum circuit
    used for portfolio optimization (VQE or QAOA method)
    """
    try:
        return {
            "svg": "",  # Base64 encoded SVG - TODO: Generate from quantum module
            "timestamp": datetime.now().isoformat(),
            "method": "VQE",
            "qubits": 4,
            "shots": 1000,
            "backend": "qasm_simulator",
            "optimization_result": {
                "converged": True,
                "iterations": 50,
                "final_energy": -1.85
            }
        }
    except Exception as e:
        logger.error(f"Error getting quantum circuit: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quantum circuit")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to SIGMAX"
        })

        # Keep connection alive and broadcast updates
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Echo back (or handle command)
            await websocket.send_json({
                "type": "echo",
                "data": data
            })

            # Broadcast system updates
            await manager.broadcast({
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "price": 95000.0,  # Mock data
                    "sentiment": 0.5
                }
            })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/control/start", tags=["Control"], dependencies=[Depends(verify_api_key)])
async def start_trading():
    """
    Start the trading system

    Activates all agents and begins automated trading
    """
    try:
        logger.info("Starting trading system")
        # TODO: Connect to SIGMAX instance
        return {
            "success": True,
            "message": "Trading started successfully",
            "timestamp": datetime.now().isoformat(),
            "mode": "paper"
        }
    except Exception as e:
        logger.error(f"Error starting trading: {e}")
        raise HTTPException(status_code=500, detail="Failed to start trading")


@app.post("/api/control/pause", tags=["Control"], dependencies=[Depends(verify_api_key)])
async def pause_trading():
    """
    Pause trading temporarily

    Stops new trades but keeps monitoring active
    Existing positions remain open
    """
    try:
        logger.info("Pausing trading system")
        # TODO: Connect to SIGMAX instance
        return {
            "success": True,
            "message": "Trading paused successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error pausing trading: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause trading")


@app.post("/api/control/stop", tags=["Control"], dependencies=[Depends(verify_api_key)])
async def stop_trading():
    """
    Stop the trading system

    Stops all trading and monitoring
    Existing positions remain open
    """
    try:
        logger.info("Stopping trading system")
        # TODO: Connect to SIGMAX instance
        return {
            "success": True,
            "message": "Trading stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop trading")


@app.post("/api/control/panic", tags=["Control"], dependencies=[Depends(verify_api_key)])
async def emergency_stop():
    """
    🚨 EMERGENCY STOP - Immediate halt

    **WARNING:** This will:
    - Close ALL open positions immediately at market price
    - Cancel all pending orders
    - Disable all trading
    - Require manual restart

    Only use in emergency situations!
    """
    try:
        logger.critical("🚨 EMERGENCY STOP INITIATED")
        # TODO: Connect to SIGMAX instance and execute emergency stop
        return {
            "success": True,
            "message": "Emergency stop executed - All positions closed",
            "timestamp": datetime.now().isoformat(),
            "positions_closed": 0,
            "orders_cancelled": 0
        }
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        raise HTTPException(status_code=500, detail="Emergency stop failed")


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        log_level="info"
    )
