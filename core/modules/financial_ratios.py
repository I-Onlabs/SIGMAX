"""
Financial Ratios Module - Phase 3
Calculates crypto-native financial and valuation metrics

Implements traditional finance ratios adapted for cryptocurrency:
- P/F (Price to Fees) - Similar to P/E for protocols
- P/S (Price to Sales) - Revenue multiples
- MC/TVL (Market Cap to Total Value Locked) - DeFi valuation
- Token Velocity - Circulation and usage metrics
- Network Value to Transactions (NVT) - Bitcoin's P/E equivalent
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class FinancialRatios:
    """Container for crypto financial ratios"""

    # Valuation ratios
    price_to_fees: Optional[float] = None  # P/F ratio (lower is better)
    price_to_sales: Optional[float] = None  # P/S ratio (protocol revenue)
    mc_to_tvl: Optional[float] = None  # Market cap / TVL
    mc_to_realized_cap: Optional[float] = None  # MVRV for Bitcoin

    # Network metrics
    nvt_ratio: Optional[float] = None  # Network Value to Transactions
    token_velocity: Optional[float] = None  # Transaction volume / Market cap
    active_address_value: Optional[float] = None  # MC / Active addresses

    # DeFi-specific
    protocol_revenue_yield: Optional[float] = None  # Annual revenue / MC
    fee_yield: Optional[float] = None  # Annual fees / MC
    tvl_to_revenue: Optional[float] = None  # TVL / Annual revenue

    # Growth metrics
    revenue_growth_30d: Optional[float] = None  # % change in revenue
    fee_growth_30d: Optional[float] = None  # % change in fees
    tvl_growth_30d: Optional[float] = None  # % change in TVL

    # Quality score
    overall_score: float = 0.5  # 0-1 score based on all ratios

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'valuation': {
                'price_to_fees': self.price_to_fees,
                'price_to_sales': self.price_to_sales,
                'mc_to_tvl': self.mc_to_tvl,
                'mc_to_realized_cap': self.mc_to_realized_cap
            },
            'network': {
                'nvt_ratio': self.nvt_ratio,
                'token_velocity': self.token_velocity,
                'active_address_value': self.active_address_value
            },
            'defi': {
                'protocol_revenue_yield': self.protocol_revenue_yield,
                'fee_yield': self.fee_yield,
                'tvl_to_revenue': self.tvl_to_revenue
            },
            'growth': {
                'revenue_growth_30d': self.revenue_growth_30d,
                'fee_growth_30d': self.fee_growth_30d,
                'tvl_growth_30d': self.tvl_growth_30d
            },
            'overall_score': self.overall_score
        }


class FinancialRatiosCalculator:
    """
    Calculates crypto-native financial ratios
    """

    def __init__(self):
        logger.info("✓ Financial ratios calculator initialized")

    def calculate(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        onchain_data: Dict[str, Any],
        fundamental_data: Dict[str, Any]
    ) -> FinancialRatios:
        """
        Calculate all financial ratios

        Args:
            symbol: Asset symbol (e.g., 'BTC', 'ETH')
            market_data: Market cap, price, volume
            onchain_data: On-chain metrics (TVL, fees, revenue)
            fundamental_data: Protocol fundamentals

        Returns:
            FinancialRatios object with calculated metrics
        """
        logger.info(f"Calculating financial ratios for {symbol}")

        ratios = FinancialRatios()

        # Extract data
        market_cap = market_data.get('market_cap', 0)
        price = market_data.get('current_price', 0)
        volume_24h = market_data.get('volume_24h', 0)

        tvl = onchain_data.get('tvl', 0)
        fees_24h = onchain_data.get('fees_24h', 0)
        revenue_24h = onchain_data.get('revenue_24h', 0)
        active_addresses = onchain_data.get('active_addresses', 0)

        # Calculate valuation ratios
        if fees_24h and fees_24h > 0:
            annual_fees = fees_24h * 365
            ratios.price_to_fees = market_cap / annual_fees if annual_fees > 0 else None
            ratios.fee_yield = (annual_fees / market_cap * 100) if market_cap > 0 else None

        if revenue_24h and revenue_24h > 0:
            annual_revenue = revenue_24h * 365
            ratios.price_to_sales = market_cap / annual_revenue if annual_revenue > 0 else None
            ratios.protocol_revenue_yield = (annual_revenue / market_cap * 100) if market_cap > 0 else None

        if tvl and tvl > 0 and market_cap > 0:
            ratios.mc_to_tvl = market_cap / tvl

        if tvl and tvl > 0 and revenue_24h and revenue_24h > 0:
            annual_revenue = revenue_24h * 365
            ratios.tvl_to_revenue = tvl / annual_revenue

        # Calculate network metrics
        if volume_24h and volume_24h > 0:
            # NVT ratio (Network Value to Transactions)
            ratios.nvt_ratio = market_cap / (volume_24h * 365) if volume_24h > 0 else None

            # Token velocity
            ratios.token_velocity = (volume_24h * 365) / market_cap if market_cap > 0 else None

        if active_addresses and active_addresses > 0:
            ratios.active_address_value = market_cap / active_addresses

        # Calculate growth metrics
        ratios.revenue_growth_30d = fundamental_data.get('revenue_growth_30d')
        ratios.fee_growth_30d = fundamental_data.get('fee_growth_30d')
        ratios.tvl_growth_30d = onchain_data.get('tvl_change_30d')

        # Calculate overall quality score
        ratios.overall_score = self._calculate_quality_score(ratios, symbol)

        logger.info(f"Financial ratios calculated: score={ratios.overall_score:.2f}")

        return ratios

    def _calculate_quality_score(self, ratios: FinancialRatios, symbol: str) -> float:
        """
        Calculate overall financial health score (0-1)

        Based on:
        - Low P/F is good (< 50)
        - Low P/S is good (< 20)
        - Low MC/TVL is good (< 3 for DeFi)
        - Moderate NVT is good (20-80 for BTC)
        - Positive growth is good
        """
        score = 0.5  # Neutral baseline
        points = 0
        total_checks = 0

        # P/F ratio (if available)
        if ratios.price_to_fees:
            total_checks += 1
            if ratios.price_to_fees < 30:
                points += 1  # Excellent
            elif ratios.price_to_fees < 50:
                points += 0.7  # Good
            elif ratios.price_to_fees < 100:
                points += 0.4  # Fair
            # else: 0 points (expensive)

        # P/S ratio (if available)
        if ratios.price_to_sales:
            total_checks += 1
            if ratios.price_to_sales < 10:
                points += 1  # Excellent
            elif ratios.price_to_sales < 20:
                points += 0.7  # Good
            elif ratios.price_to_sales < 50:
                points += 0.4  # Fair

        # MC/TVL ratio (DeFi specific)
        if ratios.mc_to_tvl:
            total_checks += 1
            if ratios.mc_to_tvl < 1.5:
                points += 1  # Undervalued
            elif ratios.mc_to_tvl < 3:
                points += 0.7  # Fair value
            elif ratios.mc_to_tvl < 6:
                points += 0.4  # Slightly expensive
            # else: 0 points (overvalued)

        # NVT ratio (Bitcoin/network specific)
        if ratios.nvt_ratio:
            total_checks += 1
            if symbol == 'BTC':
                # BTC specific ranges
                if 20 < ratios.nvt_ratio < 60:
                    points += 1  # Healthy range
                elif 60 <= ratios.nvt_ratio < 100:
                    points += 0.6  # Getting expensive
                elif ratios.nvt_ratio >= 100:
                    points += 0.2  # Overvalued
                else:
                    points += 0.4  # Too low, might indicate speculation
            else:
                # General guideline
                if ratios.nvt_ratio < 100:
                    points += 0.7
                else:
                    points += 0.3

        # Revenue/Fee yield (higher is better)
        if ratios.protocol_revenue_yield:
            total_checks += 1
            if ratios.protocol_revenue_yield > 10:
                points += 1  # Excellent yield
            elif ratios.protocol_revenue_yield > 5:
                points += 0.7  # Good yield
            elif ratios.protocol_revenue_yield > 2:
                points += 0.4  # Fair yield

        # Growth metrics
        if ratios.tvl_growth_30d is not None:
            total_checks += 1
            if ratios.tvl_growth_30d > 20:
                points += 1  # Strong growth
            elif ratios.tvl_growth_30d > 10:
                points += 0.7  # Good growth
            elif ratios.tvl_growth_30d > 0:
                points += 0.5  # Positive growth
            elif ratios.tvl_growth_30d > -10:
                points += 0.3  # Slight decline
            # else: 0 points (significant decline)

        # Calculate final score
        if total_checks > 0:
            score = points / total_checks
        else:
            score = 0.5  # Neutral if no data available

        return max(0.0, min(1.0, score))

    def interpret_ratios(self, ratios: FinancialRatios, symbol: str) -> Dict[str, str]:
        """
        Generate human-readable interpretations of ratios

        Returns:
            Dictionary of ratio interpretations
        """
        interpretations = {}

        # P/F interpretation
        if ratios.price_to_fees:
            if ratios.price_to_fees < 30:
                interpretations['price_to_fees'] = f"Excellent value (P/F={ratios.price_to_fees:.1f})"
            elif ratios.price_to_fees < 50:
                interpretations['price_to_fees'] = f"Good value (P/F={ratios.price_to_fees:.1f})"
            elif ratios.price_to_fees < 100:
                interpretations['price_to_fees'] = f"Fair value (P/F={ratios.price_to_fees:.1f})"
            else:
                interpretations['price_to_fees'] = f"Expensive (P/F={ratios.price_to_fees:.1f})"

        # MC/TVL interpretation
        if ratios.mc_to_tvl:
            if ratios.mc_to_tvl < 1.5:
                interpretations['mc_to_tvl'] = f"Undervalued (MC/TVL={ratios.mc_to_tvl:.2f})"
            elif ratios.mc_to_tvl < 3:
                interpretations['mc_to_tvl'] = f"Fair value (MC/TVL={ratios.mc_to_tvl:.2f})"
            elif ratios.mc_to_tvl < 6:
                interpretations['mc_to_tvl'] = f"Slightly overvalued (MC/TVL={ratios.mc_to_tvl:.2f})"
            else:
                interpretations['mc_to_tvl'] = f"Overvalued (MC/TVL={ratios.mc_to_tvl:.2f})"

        # Revenue yield interpretation
        if ratios.protocol_revenue_yield:
            yield_pct = ratios.protocol_revenue_yield
            if yield_pct > 10:
                interpretations['revenue_yield'] = f"Excellent yield ({yield_pct:.1f}% annual)"
            elif yield_pct > 5:
                interpretations['revenue_yield'] = f"Good yield ({yield_pct:.1f}% annual)"
            else:
                interpretations['revenue_yield'] = f"Low yield ({yield_pct:.1f}% annual)"

        # Growth interpretation
        if ratios.tvl_growth_30d is not None:
            growth = ratios.tvl_growth_30d
            if growth > 20:
                interpretations['growth'] = f"Strong growth ({growth:.1f}% 30d)"
            elif growth > 0:
                interpretations['growth'] = f"Positive growth ({growth:.1f}% 30d)"
            elif growth > -10:
                interpretations['growth'] = f"Slight decline ({growth:.1f}% 30d)"
            else:
                interpretations['growth'] = f"Significant decline ({growth:.1f}% 30d)"

        # Overall assessment
        if ratios.overall_score > 0.75:
            interpretations['overall'] = "Strong fundamentals"
        elif ratios.overall_score > 0.6:
            interpretations['overall'] = "Good fundamentals"
        elif ratios.overall_score > 0.4:
            interpretations['overall'] = "Mixed fundamentals"
        else:
            interpretations['overall'] = "Weak fundamentals"

        return interpretations

    def compare_to_benchmarks(
        self,
        ratios: FinancialRatios,
        symbol: str
    ) -> Dict[str, str]:
        """
        Compare ratios to industry benchmarks

        Returns:
            Dictionary of comparisons to benchmarks
        """
        comparisons = {}

        # DeFi protocol benchmarks (approximate)
        defi_benchmarks = {
            'p_to_fees': {
                'excellent': 30,
                'good': 50,
                'fair': 100
            },
            'mc_to_tvl': {
                'undervalued': 1.5,
                'fair': 3,
                'overvalued': 6
            },
            'revenue_yield': {
                'excellent': 10,
                'good': 5,
                'fair': 2
            }
        }

        # L1/L2 blockchain benchmarks
        l1_benchmarks = {
            'nvt_ratio': {
                'btc': (20, 60),  # Healthy range for Bitcoin
                'eth': (30, 100),  # Healthy range for Ethereum
            }
        }

        # Compare P/F
        if ratios.price_to_fees:
            benchmarks = defi_benchmarks['p_to_fees']
            if ratios.price_to_fees < benchmarks['excellent']:
                comparisons['p_to_fees'] = "Below excellent benchmark ✓"
            elif ratios.price_to_fees < benchmarks['good']:
                comparisons['p_to_fees'] = "Below good benchmark ✓"
            elif ratios.price_to_fees < benchmarks['fair']:
                comparisons['p_to_fees'] = "Above fair benchmark ⚠️"
            else:
                comparisons['p_to_fees'] = "Above all benchmarks ❌"

        # Compare MC/TVL
        if ratios.mc_to_tvl:
            benchmarks = defi_benchmarks['mc_to_tvl']
            if ratios.mc_to_tvl < benchmarks['undervalued']:
                comparisons['mc_to_tvl'] = "Below undervalued threshold ✓"
            elif ratios.mc_to_tvl < benchmarks['fair']:
                comparisons['mc_to_tvl'] = "In fair value range ✓"
            elif ratios.mc_to_tvl < benchmarks['overvalued']:
                comparisons['mc_to_tvl'] = "Approaching overvalued ⚠️"
            else:
                comparisons['mc_to_tvl'] = "Overvalued vs peers ❌"

        # Compare NVT (asset-specific)
        if ratios.nvt_ratio and symbol in ['BTC', 'ETH']:
            benchmark_range = l1_benchmarks['nvt_ratio'].get(symbol.lower(), (30, 100))
            if benchmark_range[0] < ratios.nvt_ratio < benchmark_range[1]:
                comparisons['nvt_ratio'] = f"In healthy range for {symbol} ✓"
            elif ratios.nvt_ratio >= benchmark_range[1]:
                comparisons['nvt_ratio'] = f"Above healthy range for {symbol} ⚠️"
            else:
                comparisons['nvt_ratio'] = f"Below typical range for {symbol} ⚠️"

        return comparisons

    def generate_summary(self, ratios: FinancialRatios, symbol: str) -> str:
        """Generate concise summary of financial ratios"""

        parts = []

        # Valuation
        if ratios.price_to_fees:
            parts.append(f"P/F: {ratios.price_to_fees:.1f}")

        if ratios.mc_to_tvl:
            parts.append(f"MC/TVL: {ratios.mc_to_tvl:.2f}")

        # Yield
        if ratios.protocol_revenue_yield:
            parts.append(f"Yield: {ratios.protocol_revenue_yield:.1f}%")

        # Growth
        if ratios.tvl_growth_30d:
            parts.append(f"TVL Growth: {ratios.tvl_growth_30d:+.1f}%")

        # Score
        score_pct = ratios.overall_score * 100
        parts.append(f"Score: {score_pct:.0f}/100")

        return " | ".join(parts) if parts else "No ratio data available"
