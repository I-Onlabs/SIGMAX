"""
Optimizer Agent - Quantum Portfolio Optimization
"""

from typing import Dict, Any, Optional
from loguru import logger


class OptimizerAgent:
    """
    Optimizer Agent - Uses quantum computing for portfolio optimization
    """

    def __init__(self, llm, quantum_module):
        self.llm = llm
        self.quantum_module = quantum_module
        logger.info("✓ Optimizer agent initialized")

    async def optimize(
        self,
        symbol: str,
        bull_score: float,
        bear_score: float,
        risk_assessment: Dict[str, Any],
        current_portfolio: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Optimize position sizing and portfolio allocation

        Args:
            symbol: Trading pair
            bull_score: Bullish sentiment score
            bear_score: Bearish sentiment score
            risk_assessment: Risk constraints
            current_portfolio: Current holdings

        Returns:
            Optimization result with confidence
        """
        logger.info(f"⚛️ Optimizing portfolio for {symbol}...")

        try:
            # Calculate net signal
            net_signal = bull_score + bear_score  # Bear is negative

            # Use quantum optimizer if available
            if self.quantum_module and self.quantum_module.enabled:
                optimization = await self.quantum_module.optimize_portfolio(
                    symbol=symbol,
                    signal=net_signal,
                    current_portfolio=current_portfolio
                )
            else:
                # Classical fallback
                optimization = self._classical_optimize(
                    symbol=symbol,
                    signal=net_signal,
                    current_portfolio=current_portfolio
                )

            # Calculate confidence
            confidence = self._calculate_confidence(
                signal=net_signal,
                risk_assessment=risk_assessment,
                optimization=optimization
            )

            summary = f"""
Portfolio Optimization for {symbol}:

Signal Strength: {net_signal:.2f}
Recommended Action: {optimization.get('action', 'hold').upper()}
Position Size: {optimization.get('size', 0):.2%}
Confidence: {confidence:.2%}

Method: {'Quantum (VQE)' if self.quantum_module and self.quantum_module.enabled else 'Classical'}
"""

            return {
                "summary": summary,
                "action": optimization.get("action", "hold"),
                "size": optimization.get("size", 0.0),
                "confidence": confidence,
                "method": "quantum" if self.quantum_module and self.quantum_module.enabled else "classical"
            }

        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return {
                "summary": f"Optimization failed: {e}",
                "confidence": 0.0,
                "error": str(e)
            }

    def _classical_optimize(
        self,
        symbol: str,
        signal: float,
        current_portfolio: Dict[str, float]
    ) -> Dict[str, Any]:
        """Classical portfolio optimization (Kelly Criterion)"""

        # Simple Kelly Criterion approximation
        win_rate = 0.5 + (signal * 0.2)  # Convert signal to win rate
        win_rate = max(0.3, min(0.7, win_rate))

        avg_win = 1.03  # 3% avg win
        avg_loss = 0.98  # 2% avg loss

        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        # Cap at 10% position size for safety
        position_size = max(0.0, min(0.10, kelly / 2))  # Half-Kelly

        if signal > 0.3:
            action = "buy"
        elif signal < -0.3:
            action = "sell"
        else:
            action = "hold"

        return {
            "action": action,
            "size": position_size,
            "kelly": kelly
        }

    def _calculate_confidence(
        self,
        signal: float,
        risk_assessment: Dict[str, Any],
        optimization: Dict[str, Any]
    ) -> float:
        """Calculate confidence score"""

        # Base confidence from signal strength
        confidence = abs(signal) * 0.5

        # Boost if risk approved
        if risk_assessment.get("approved", False):
            confidence += 0.3

        # Reduce if high volatility
        if risk_assessment.get("volatility", "low") == "high":
            confidence *= 0.7

        return max(0.0, min(1.0, confidence))
