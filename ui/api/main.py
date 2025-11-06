"""
SIGMAX FastAPI Backend
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from loguru import logger

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'core'))

# Import SIGMAX
try:
    from main import SIGMAX
    SIGMAX_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import SIGMAX: {e}")
    SIGMAX_AVAILABLE = False

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

# Global SIGMAX instance
sigmax_instance: Optional[SIGMAX] = None


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting SIGMAX API")

    # Initialize SIGMAX if available
    global sigmax_instance
    if SIGMAX_AVAILABLE:
        try:
            sigmax_instance = SIGMAX(
                mode=os.getenv("TRADING_MODE", "paper"),
                risk_profile=os.getenv("RISK_PROFILE", "conservative")
            )
            await sigmax_instance.initialize()
            logger.info("✓ SIGMAX instance initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SIGMAX: {e}")
            sigmax_instance = None

    yield

    # Shutdown
    if sigmax_instance:
        await sigmax_instance.stop()
    logger.info("👋 Shutting down SIGMAX API")


# Create FastAPI app
app = FastAPI(
    title="SIGMAX API",
    description="Autonomous Multi-Agent AI Trading OS API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class TradeRequest(BaseModel):
    symbol: str
    action: str
    size: float


class AnalysisRequest(BaseModel):
    symbol: str


# Routes
@app.get("/")
async def root():
    return {
        "name": "SIGMAX API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/status")
async def get_status():
    """Get system status"""
    if not sigmax_instance:
        return {
            "running": False,
            "mode": "offline",
            "error": "SIGMAX not initialized"
        }

    try:
        status = await sigmax_instance.get_status()
        return status
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "running": False,
            "error": str(e)
        }


@app.post("/api/analyze")
async def analyze_symbol(request: AnalysisRequest):
    """Analyze a trading symbol"""
    if not sigmax_instance or not sigmax_instance.orchestrator:
        raise HTTPException(status_code=503, detail="SIGMAX not available")

    try:
        result = await sigmax_instance.orchestrator.analyze_symbol(request.symbol)
        return result
    except Exception as e:
        logger.error(f"Error analyzing {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trade")
async def execute_trade(request: TradeRequest):
    """Execute a trade"""
    # TODO: Connect to execution module
    return {
        "success": True,
        "order_id": "mock_order_123",
        "symbol": request.symbol,
        "action": request.action,
        "size": request.size,
        "status": "filled"
    }


@app.get("/api/portfolio")
async def get_portfolio():
    """Get current portfolio"""
    return {
        "total_value": 50.0,
        "positions": [
            {
                "symbol": "BTC/USDT",
                "size": 0.0005,
                "value": 47.5,
                "pnl": 2.5,
                "pnl_pct": 5.56
            }
        ],
        "cash": 2.5
    }


@app.get("/api/history")
async def get_trade_history(limit: int = 50):
    """Get trade history"""
    return {
        "trades": [],
        "total": 0
    }


@app.get("/api/agents/debate/{symbol}")
async def get_agent_debate(symbol: str):
    """Get agent debate history for a symbol"""
    return {
        "symbol": symbol,
        "debate": [
            {
                "agent": "bull",
                "argument": "Strong upward momentum with increasing volume",
                "timestamp": datetime.now().isoformat()
            },
            {
                "agent": "bear",
                "argument": "Overbought conditions, potential correction",
                "timestamp": datetime.now().isoformat()
            },
            {
                "agent": "researcher",
                "verdict": "Moderate bullish sentiment with caution",
                "timestamp": datetime.now().isoformat()
            }
        ]
    }


@app.get("/api/quantum/circuit")
async def get_quantum_circuit():
    """Get latest quantum circuit visualization"""
    return {
        "svg": "",  # Base64 encoded SVG
        "timestamp": datetime.now().isoformat(),
        "method": "VQE",
        "shots": 1000
    }


@app.get("/api/alerts")
async def get_alerts(limit: int = 50, level: Optional[str] = None):
    """Get recent alerts"""
    if not sigmax_instance or not sigmax_instance.alert_manager:
        return {"alerts": [], "total": 0}

    try:
        from modules.alerts import AlertLevel
        alert_level = AlertLevel(level) if level else None
        alerts = sigmax_instance.alert_manager.get_recent_alerts(
            limit=limit,
            level=alert_level
        )

        return {
            "alerts": [
                {
                    "id": str(hash(f"{a.timestamp}{a.title}")),
                    "level": a.level.value,
                    "title": a.title,
                    "message": a.message,
                    "timestamp": a.timestamp.isoformat(),
                    "tags": a.tags
                }
                for a in alerts
            ],
            "total": len(alerts),
            "stats": sigmax_instance.alert_manager.get_alert_stats()
        }
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return {"alerts": [], "total": 0, "error": str(e)}


@app.get("/api/performance")
async def get_performance(timeframe: str = "24h"):
    """Get performance metrics"""
    if not sigmax_instance or not sigmax_instance.performance_monitor:
        return {"history": [], "metrics": None}

    try:
        metrics = sigmax_instance.performance_monitor.get_trading_metrics()

        # Get historical data (simplified for now)
        history = []
        for trade in list(sigmax_instance.performance_monitor.trade_history)[-100:]:
            history.append({
                "timestamp": trade['timestamp'].isoformat(),
                "pnl": trade.get('pnl', 0),
                "cumulative_pnl": metrics.get('total_pnl', 0),
                "trades": metrics.get('total_trades', 0),
                "win_rate": metrics.get('win_rate', 0)
            })

        return {
            "history": history,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        return {"history": [], "metrics": None, "error": str(e)}


@app.post("/api/ml/predict")
async def ml_predict(request: AnalysisRequest):
    """Get ML prediction for symbol"""
    if not sigmax_instance or not sigmax_instance.ml_predictor:
        raise HTTPException(status_code=503, detail="ML Predictor not available")

    try:
        # Get OHLCV data
        data_module = sigmax_instance.data_module
        ohlcv = await data_module.get_ohlcv(request.symbol, timeframe='1h', limit=200)

        # Make prediction
        prediction = await sigmax_instance.ml_predictor.predict(ohlcv)
        return prediction
    except Exception as e:
        logger.error(f"Error making ML prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Get sentiment analysis for symbol"""
    if not sigmax_instance or not sigmax_instance.sentiment_agent:
        raise HTTPException(status_code=503, detail="Sentiment Agent not available")

    try:
        sentiment = await sigmax_instance.sentiment_agent.analyze(symbol, lookback_hours=24)
        return sentiment
    except Exception as e:
        logger.error(f"Error getting sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/regime/{symbol}")
async def get_market_regime(symbol: str):
    """Get market regime for symbol"""
    if not sigmax_instance or not sigmax_instance.regime_detector:
        raise HTTPException(status_code=503, detail="Regime Detector not available")

    try:
        # Get OHLCV data
        data_module = sigmax_instance.data_module
        ohlcv = await data_module.get_ohlcv(symbol, timeframe='1h', limit=200)

        # Detect regime
        regime = await sigmax_instance.regime_detector.detect_regime(ohlcv, lookback=100)
        return regime
    except Exception as e:
        logger.error(f"Error detecting regime: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/control/start")
async def start_trading():
    """Start trading"""
    if not sigmax_instance:
        raise HTTPException(status_code=503, detail="SIGMAX not available")

    try:
        if not sigmax_instance.running:
            asyncio.create_task(sigmax_instance.start())
        return {"message": "Trading started", "success": True}
    except Exception as e:
        logger.error(f"Error starting trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control/pause")
async def pause_trading():
    """Pause trading"""
    if not sigmax_instance:
        raise HTTPException(status_code=503, detail="SIGMAX not available")

    try:
        await sigmax_instance.pause()
        return {"message": "Trading paused", "success": True}
    except Exception as e:
        logger.error(f"Error pausing trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control/stop")
async def stop_trading():
    """Stop trading"""
    if not sigmax_instance:
        raise HTTPException(status_code=503, detail="SIGMAX not available")

    try:
        await sigmax_instance.stop()
        return {"message": "Trading stopped", "success": True}
    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control/panic")
async def emergency_stop():
    """Emergency stop"""
    if not sigmax_instance:
        raise HTTPException(status_code=503, detail="SIGMAX not available")

    try:
        await sigmax_instance.emergency_stop()
        if sigmax_instance.trading_alerts:
            await sigmax_instance.trading_alerts.emergency_stop_triggered(
                reason="User initiated emergency stop",
                trigger_details={"timestamp": datetime.now().isoformat()}
            )
        return {"message": "Emergency stop executed", "success": True}
    except Exception as e:
        logger.error(f"Error executing emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        log_level="info"
    )
