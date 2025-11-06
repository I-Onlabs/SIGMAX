"""
Portfolio Rebalancer - Intelligent portfolio rebalancing with quantum optimization
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from loguru import logger


class PortfolioRebalancer:
    """
    Intelligent Portfolio Rebalancer

    Strategies:
    - Threshold rebalancing (rebalance when drift > threshold)
    - Calendar rebalancing (fixed schedule)
    - Volatility-adjusted rebalancing
    - Quantum-optimized weights
    """

    def __init__(
        self,
        quantum_module=None,
        rebalance_threshold: float = 0.05,  # 5% drift triggers rebalance
        min_rebalance_interval: int = 7     # Min days between rebalances
    ):
        self.quantum_module = quantum_module
        self.rebalance_threshold = rebalance_threshold
        self.min_rebalance_interval = min_rebalance_interval
        self.last_rebalance = None
        self.target_weights = {}
        self.rebalance_history = []

        logger.info("✓ Portfolio Rebalancer initialized")

    async def should_rebalance(
        self,
        current_portfolio: Dict[str, float],
        current_prices: Dict[str, float]
    ) -> bool:
        """
        Determine if portfolio should be rebalanced

        Args:
            current_portfolio: Current holdings {symbol: quantity}
            current_prices: Current prices {symbol: price}

        Returns:
            True if rebalancing is needed
        """
        # Check minimum interval
        if self.last_rebalance:
            days_since = (datetime.now() - self.last_rebalance).days
            if days_since < self.min_rebalance_interval:
                return False

        # Calculate current weights
        current_weights = self._calculate_weights(current_portfolio, current_prices)

        # Check drift from target
        if not self.target_weights:
            return True  # First time, need to set targets

        max_drift = self._calculate_max_drift(current_weights, self.target_weights)

        should_rebal = max_drift > self.rebalance_threshold

        if should_rebal:
            logger.info(f"📊 Rebalancing triggered: max drift = {max_drift:.2%}")

        return should_rebal

    async def calculate_target_weights(
        self,
        symbols: List[str],
        market_data: Dict[str, Any],
        method: str = 'quantum'
    ) -> Dict[str, float]:
        """
        Calculate optimal target weights

        Args:
            symbols: List of symbols to include
            market_data: Market data for each symbol
            method: 'quantum', 'risk_parity', 'equal', or 'market_cap'

        Returns:
            Target weights {symbol: weight}
        """
        logger.info(f"⚙️ Calculating target weights using {method} method...")

        if method == 'quantum' and self.quantum_module:
            weights = await self._quantum_optimize(symbols, market_data)

        elif method == 'risk_parity':
            weights = await self._risk_parity(symbols, market_data)

        elif method == 'market_cap':
            weights = await self._market_cap_weighted(symbols, market_data)

        else:  # equal weight
            n = len(symbols)
            weights = {symbol: 1.0 / n for symbol in symbols}

        # Normalize weights to sum to 1
        total = sum(weights.values())
        weights = {s: w / total for s, w in weights.items()}

        self.target_weights = weights

        logger.info(f"✓ Target weights: {weights}")

        return weights

    async def generate_rebalance_orders(
        self,
        current_portfolio: Dict[str, float],
        current_prices: Dict[str, float],
        total_value: float
    ) -> List[Dict[str, Any]]:
        """
        Generate orders to rebalance portfolio to target weights

        Args:
            current_portfolio: Current holdings {symbol: quantity}
            current_prices: Current prices {symbol: price}
            total_value: Total portfolio value

        Returns:
            List of orders {symbol, action, quantity}
        """
        orders = []

        for symbol, target_weight in self.target_weights.items():
            # Calculate target value for this position
            target_value = total_value * target_weight

            # Calculate current value
            current_quantity = current_portfolio.get(symbol, 0)
            current_value = current_quantity * current_prices.get(symbol, 0)

            # Calculate difference
            value_diff = target_value - current_value

            # Only rebalance if difference is significant (> $10 or > 1%)
            if abs(value_diff) > 10 and abs(value_diff / total_value) > 0.01:
                price = current_prices.get(symbol, 0)
                if price > 0:
                    quantity_diff = value_diff / price

                    action = 'buy' if quantity_diff > 0 else 'sell'
                    quantity = abs(quantity_diff)

                    orders.append({
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'price': price,
                        'value': value_diff,
                        'reason': 'rebalance'
                    })

        logger.info(f"📋 Generated {len(orders)} rebalance orders")

        return orders

    async def execute_rebalance(
        self,
        orders: List[Dict[str, Any]],
        execution_module
    ) -> Dict[str, Any]:
        """
        Execute rebalancing orders

        Args:
            orders: List of orders to execute
            execution_module: Execution module instance

        Returns:
            Execution summary
        """
        logger.info(f"🔄 Executing {len(orders)} rebalance orders...")

        results = {
            'executed': [],
            'failed': [],
            'total_orders': len(orders)
        }

        for order in orders:
            try:
                result = await execution_module.execute_trade(
                    symbol=order['symbol'],
                    action=order['action'],
                    size=order['quantity'],
                    price=order.get('price')
                )

                if result.get('success'):
                    results['executed'].append(order)
                else:
                    results['failed'].append({**order, 'error': result.get('error')})

            except Exception as e:
                logger.error(f"Error executing order for {order['symbol']}: {e}")
                results['failed'].append({**order, 'error': str(e)})

        self.last_rebalance = datetime.now()

        # Store in history
        self.rebalance_history.append({
            'timestamp': self.last_rebalance,
            'orders': orders,
            'results': results
        })

        logger.info(f"✓ Rebalancing complete: {len(results['executed'])} executed, "
                   f"{len(results['failed'])} failed")

        return results

    async def _quantum_optimize(
        self,
        symbols: List[str],
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Optimize portfolio using quantum algorithm"""
        if not self.quantum_module:
            logger.warning("Quantum module not available, falling back to equal weight")
            n = len(symbols)
            return {symbol: 1.0 / n for symbol in symbols}

        try:
            # Extract returns for each symbol
            returns_data = {}
            for symbol in symbols:
                if symbol in market_data:
                    # Calculate daily returns
                    closes = market_data[symbol].get('close', [])
                    if len(closes) > 1:
                        returns = np.diff(closes) / closes[:-1]
                        returns_data[symbol] = returns

            # Use quantum module to optimize
            result = await self.quantum_module.optimize_portfolio(
                symbols=symbols,
                returns_data=returns_data
            )

            weights = result.get('weights', {})

            # Fallback if quantum optimization fails
            if not weights or sum(weights.values()) == 0:
                n = len(symbols)
                weights = {symbol: 1.0 / n for symbol in symbols}

            return weights

        except Exception as e:
            logger.error(f"Quantum optimization failed: {e}")
            n = len(symbols)
            return {symbol: 1.0 / n for symbol in symbols}

    async def _risk_parity(
        self,
        symbols: List[str],
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Risk parity weighting (inverse volatility)"""
        volatilities = {}

        for symbol in symbols:
            if symbol in market_data:
                closes = market_data[symbol].get('close', [])
                if len(closes) > 20:
                    returns = np.diff(closes[-20:]) / closes[-20:-1]
                    vol = np.std(returns)
                    volatilities[symbol] = vol if vol > 0 else 1.0

        if not volatilities:
            n = len(symbols)
            return {symbol: 1.0 / n for symbol in symbols}

        # Inverse volatility weighting
        inv_vols = {s: 1.0 / v for s, v in volatilities.items()}
        total = sum(inv_vols.values())

        return {s: w / total for s, w in inv_vols.items()}

    async def _market_cap_weighted(
        self,
        symbols: List[str],
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Market cap weighted portfolio"""
        # TODO: Fetch actual market caps
        # For now, use price * volume as proxy

        caps = {}

        for symbol in symbols:
            if symbol in market_data:
                price = market_data[symbol].get('price', 0)
                volume = market_data[symbol].get('volume_24h', 0)
                caps[symbol] = price * volume

        if not caps or sum(caps.values()) == 0:
            n = len(symbols)
            return {symbol: 1.0 / n for symbol in symbols}

        total = sum(caps.values())
        return {s: c / total for s, c in caps.items()}

    def _calculate_weights(
        self,
        portfolio: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate current portfolio weights"""
        values = {
            symbol: quantity * prices.get(symbol, 0)
            for symbol, quantity in portfolio.items()
        }

        total_value = sum(values.values())

        if total_value == 0:
            return {}

        return {s: v / total_value for s, v in values.items()}

    def _calculate_max_drift(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> float:
        """Calculate maximum drift from target weights"""
        drifts = []

        all_symbols = set(current_weights.keys()) | set(target_weights.keys())

        for symbol in all_symbols:
            current = current_weights.get(symbol, 0)
            target = target_weights.get(symbol, 0)
            drift = abs(current - target)
            drifts.append(drift)

        return max(drifts) if drifts else 0

    def get_rebalance_summary(self) -> Dict[str, Any]:
        """Get summary of rebalancing history"""
        if not self.rebalance_history:
            return {
                "total_rebalances": 0,
                "last_rebalance": None,
                "avg_orders_per_rebalance": 0
            }

        total = len(self.rebalance_history)
        last = self.rebalance_history[-1]

        avg_orders = np.mean([
            len(r['orders']) for r in self.rebalance_history
        ])

        return {
            "total_rebalances": total,
            "last_rebalance": last['timestamp'],
            "avg_orders_per_rebalance": avg_orders,
            "current_targets": self.target_weights
        }
