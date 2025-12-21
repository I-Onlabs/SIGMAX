"""
Decision Engine

Implements hybrid L0-L5 decision architecture.
"""

from typing import Optional, Dict
from dataclasses import dataclass

from pkg.common import get_logger, get_metrics_collector, get_timestamp_ns, calculate_latency_us
from pkg.schemas import FeatureFrame, OrderIntent, Side, OrderType, TimeInForce


@dataclass
class DecisionContext:
    """Context passed through decision layers"""
    features: FeatureFrame
    # Layer outputs
    l0_passed: bool = False
    l1_action: Optional[str] = None  # "buy", "sell", "hold"
    l1_confidence: float = 0.0
    l2_action: Optional[str] = None
    l2_confidence: float = 0.0
    # Final decision
    final_action: Optional[str] = None
    final_confidence: float = 0.0
    final_qty: float = 0.0
    final_price: Optional[float] = None


class L0Constraints:
    """
    L0: Safety constraints layer.
    
    Defines safe operating bands - hard limits.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(f"{__name__}.L0")
        
        # Default constraints
        self.min_spread_bps = 1.0  # Minimum spread in bps
        self.max_spread_bps = 500.0  # Maximum spread in bps
        self.min_price = 0.0001  # Minimum price
        self.max_vol_threshold = 0.10  # 10% volatility threshold
        
    def check(self, ctx: DecisionContext) -> bool:
        """Check if features pass safety constraints"""
        features = ctx.features
        
        # Check spread
        if features.spread_bps < self.min_spread_bps:
            self.logger.debug("l0_reject_min_spread", 
                            symbol_id=features.symbol_id,
                            spread_bps=features.spread_bps)
            return False
        
        if features.spread_bps > self.max_spread_bps:
            self.logger.debug("l0_reject_max_spread",
                            symbol_id=features.symbol_id,
                            spread_bps=features.spread_bps)
            return False
        
        # Check price
        if features.mid_price < self.min_price:
            self.logger.debug("l0_reject_min_price",
                            symbol_id=features.symbol_id,
                            price=features.mid_price)
            return False
        
        # Check volatility
        if features.realized_vol > self.max_vol_threshold:
            self.logger.debug("l0_reject_high_vol",
                            symbol_id=features.symbol_id,
                            vol=features.realized_vol)
            return False
        
        return True


class L1Rules:
    """
    L1: Reflex rules layer.
    
    Simple rules for market making based on inventory and market conditions.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(f"{__name__}.L1")
        
        # Track positions (simplified - would come from database)
        self.positions: Dict[int, float] = {}
        
        # Rules parameters
        self.imbalance_threshold = 0.3  # Trade on imbalance > 30%
        self.momentum_threshold = 0.5  # Trade on momentum > 0.5%
        
    def decide(self, ctx: DecisionContext) -> DecisionContext:
        """Apply reflex rules"""
        features = ctx.features
        
        # Get current position (default to 0)
        position = self.positions.get(features.symbol_id, 0.0)
        
        # Rule 1: Mean reversion on imbalance
        if abs(features.imbalance) > self.imbalance_threshold:
            if features.imbalance > 0:
                # High bid volume - expect price to rise, but we sell (mean reversion)
                ctx.l1_action = "sell"
                ctx.l1_confidence = min(abs(features.imbalance), 1.0)
            else:
                # High ask volume - expect price to fall, but we buy (mean reversion)
                ctx.l1_action = "buy"
                ctx.l1_confidence = min(abs(features.imbalance), 1.0)
        
        # Rule 2: Momentum following
        elif abs(features.price_change_pct) > self.momentum_threshold:
            if features.price_change_pct > 0:
                # Price rising - buy
                ctx.l1_action = "buy"
                ctx.l1_confidence = min(abs(features.price_change_pct) / 2.0, 1.0)
            else:
                # Price falling - sell
                ctx.l1_action = "sell"
                ctx.l1_confidence = min(abs(features.price_change_pct) / 2.0, 1.0)
        else:
            ctx.l1_action = "hold"
            ctx.l1_confidence = 0.0
        
        # Inventory skew: reduce confidence if position is large
        if position != 0:
            if (ctx.l1_action == "buy" and position > 0) or \
               (ctx.l1_action == "sell" and position < 0):
                ctx.l1_confidence *= 0.5  # Reduce confidence
        
        self.logger.debug("l1_decision",
                        symbol_id=features.symbol_id,
                        action=ctx.l1_action,
                        confidence=ctx.l1_confidence,
                        imbalance=features.imbalance,
                        momentum=features.price_change_pct)
        
        return ctx


class L2MicroML:
    """
    L2: Micro-ML layer.
    
    Lightweight ML model for price/size predictions.
    Stub implementation - would use LightGBM/ONNX in production.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(f"{__name__}.L2")
        self.enabled = config.decision.enable_ml if hasattr(config, 'decision') else False
        
    def decide(self, ctx: DecisionContext) -> DecisionContext:
        """Apply ML model"""
        if not self.enabled:
            ctx.l2_action = ctx.l1_action
            ctx.l2_confidence = ctx.l1_confidence
            return ctx
        
        # Stub: In production, would run ONNX model here
        # For now, just pass through L1 decision with slight adjustment
        ctx.l2_action = ctx.l1_action
        ctx.l2_confidence = ctx.l1_confidence * 0.9  # Slight discount
        
        self.logger.debug("l2_decision",
                        symbol_id=ctx.features.symbol_id,
                        action=ctx.l2_action,
                        confidence=ctx.l2_confidence)
        
        return ctx


class L5Arbiter:
    """
    L5: Arbiter layer.
    
    Mixes outputs from all layers and generates final OrderIntent.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(f"{__name__}.L5")
        
        # Get risk limits from config
        self.max_order_usd = 500.0
        if hasattr(config, 'risk'):
            self.max_order_usd = config.risk.max_order_usd
        
        self.min_confidence = 0.5  # Minimum confidence to trade
        
    def decide(self, ctx: DecisionContext) -> DecisionContext:
        """Arbitrate and generate final decision"""
        
        # Use L2 output (or L1 if L2 not enabled)
        action = ctx.l2_action or ctx.l1_action
        confidence = ctx.l2_confidence or ctx.l1_confidence
        
        # Filter by confidence
        if confidence < self.min_confidence:
            action = "hold"
        
        ctx.final_action = action
        ctx.final_confidence = confidence
        
        # Size the order based on confidence and max size
        if action in ["buy", "sell"]:
            # Calculate order size in USD
            order_size_usd = self.max_order_usd * confidence
            
            # Convert to quantity
            ctx.final_qty = order_size_usd / ctx.features.mid_price
            
            # Set price (use microprice for better execution)
            ctx.final_price = ctx.features.micro_price
        
        self.logger.debug("l5_decision",
                        symbol_id=ctx.features.symbol_id,
                        action=ctx.final_action,
                        confidence=ctx.final_confidence,
                        qty=ctx.final_qty,
                        price=ctx.final_price)
        
        return ctx


class DecisionEngine:
    """
    Main decision engine coordinating all layers.
    """
    
    def __init__(self, config, publisher):
        self.config = config
        self.publisher = publisher
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector("decision")
        
        # Initialize layers
        self.l0 = L0Constraints(config)
        self.l1 = L1Rules(config)
        self.l2 = L2MicroML(config)
        self.l5 = L5Arbiter(config)
        
        # Get enabled layers from config
        self.enabled_layers = [0, 1, 2, 5]  # Default
        if hasattr(config, 'decision') and hasattr(config.decision, 'enabled_layers'):
            self.enabled_layers = config.decision.enabled_layers
        
        self.running = False
        
    async def start(self):
        """Start the decision engine"""
        self.logger.info("decision_engine_started", 
                        enabled_layers=self.enabled_layers)
        self.running = True
        
    async def stop(self):
        """Stop the decision engine"""
        self.running = False
        self.logger.info("decision_engine_stopped")
    
    async def process_features(self, features: FeatureFrame):
        """
        Process features through decision layers and generate orders.
        
        Args:
            features: FeatureFrame from features service
        """
        try:
            start_ts = get_timestamp_ns()
            
            # Create decision context
            ctx = DecisionContext(features=features)
            
            # L0: Safety constraints
            if 0 in self.enabled_layers:
                ctx.l0_passed = self.l0.check(ctx)
                if not ctx.l0_passed:
                    self.logger.debug("l0_rejected", symbol_id=features.symbol_id)
                    self.metrics.record_error("l0_reject")
                    return
            else:
                ctx.l0_passed = True
            
            # L1: Reflex rules
            if 1 in self.enabled_layers:
                ctx = self.l1.decide(ctx)
            
            # L2: Micro-ML
            if 2 in self.enabled_layers:
                ctx = self.l2.decide(ctx)
            
            # L5: Arbiter
            if 5 in self.enabled_layers:
                ctx = self.l5.decide(ctx)
            
            # Generate OrderIntent if we have an action
            if ctx.final_action in ["buy", "sell"] and ctx.final_qty > 0:
                order_intent = OrderIntent.create(
                    symbol_id=features.symbol_id,
                    side=Side.BUY if ctx.final_action == "buy" else Side.SELL,
                    order_type=OrderType.LIMIT,
                    qty=ctx.final_qty,
                    price=ctx.final_price,
                    tif=TimeInForce.GTC
                )
                order_intent.decision_layer = 2  # L2 (or highest enabled)
                order_intent.confidence = ctx.final_confidence
                
                # Publish order intent
                await self.publisher.publish(order_intent)
                
                self.logger.info("order_intent_generated",
                               symbol_id=features.symbol_id,
                               side=ctx.final_action,
                               qty=ctx.final_qty,
                               price=ctx.final_price,
                               confidence=ctx.final_confidence)
            
            # Record latency
            end_ts = get_timestamp_ns()
            decision_latency_us = calculate_latency_us(start_ts, end_ts)
            total_latency_us = calculate_latency_us(features.ts_ns, end_ts)
            
            self.metrics.record_latency("decision", decision_latency_us)
            self.metrics.record_latency("features_to_decision", total_latency_us)
            
        except Exception as e:
            self.logger.error("process_features_error",
                            symbol_id=features.symbol_id,
                            error=str(e),
                            exc_info=True)
            self.metrics.record_error("process_features_failed")
