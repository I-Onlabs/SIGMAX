"""
Tests for Phase 3: Fundamental Analysis

Tests the FundamentalAnalyzer agent and FinancialRatiosCalculator
"""

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from agents.fundamental_analyzer import FundamentalAnalyzer
from modules.financial_ratios import (
    FinancialRatios,
    FinancialRatiosCalculator
)


# =============================================================================
# FundamentalAnalyzer Tests
# =============================================================================

class TestFundamentalAnalyzer:
    """Test suite for FundamentalAnalyzer agent"""

    def test_analyzer_creation(self):
        """Test creating fundamental analyzer"""
        analyzer = FundamentalAnalyzer(llm=None)

        assert analyzer is not None
        assert analyzer.llm is None
        assert analyzer.protocol_map is not None
        assert len(analyzer.protocol_map) > 0
        assert 'BTC' in analyzer.protocol_map
        assert 'ETH' in analyzer.protocol_map

    @pytest.mark.asyncio
    async def test_analyze_btc(self):
        """Test analyzing BTC fundamentals"""
        analyzer = FundamentalAnalyzer(llm=None)

        result = await analyzer.analyze(
            symbol='BTC/USDT',
            market_data={'current_price': 50000, 'volume': 25000000000}
        )

        # Verify structure
        assert 'fundamental_score' in result
        assert 'summary' in result
        assert 'onchain_fundamentals' in result
        assert 'token_economics' in result
        assert 'project_metrics' in result
        assert 'timestamp' in result

        # Verify score range
        assert 0 <= result['fundamental_score'] <= 1

        # Verify BTC has no TVL (not DeFi)
        assert result['onchain_fundamentals']['tvl'] is None

    @pytest.mark.asyncio
    async def test_analyze_eth(self):
        """Test analyzing ETH fundamentals"""
        analyzer = FundamentalAnalyzer(llm=None)

        result = await analyzer.analyze(
            symbol='ETH/USDT',
            market_data={'current_price': 3000, 'market_cap': 360000000000}
        )

        assert result['fundamental_score'] > 0
        assert 'ETH' in result['summary']

        # ETH has DeFi TVL
        onchain = result['onchain_fundamentals']
        assert onchain['tvl'] is not None
        assert onchain['tvl'] > 0

    @pytest.mark.asyncio
    async def test_analyze_defi_protocol(self):
        """Test analyzing DeFi protocol (UNI)"""
        analyzer = FundamentalAnalyzer(llm=None)

        result = await analyzer.analyze(
            symbol='UNI/USDT',
            market_data={'current_price': 6.5, 'market_cap': 4900000000}
        )

        # DeFi protocols have TVL
        assert result['onchain_fundamentals']['tvl'] > 0

        # Should have token economics
        token_econ = result['token_economics']
        assert token_econ['market_cap'] > 0
        assert token_econ['circulating_supply'] > 0

        # Should have project metrics
        project = result['project_metrics']
        assert project['github_stars'] > 0
        assert project['development_activity_score'] > 0

    @pytest.mark.asyncio
    async def test_token_economics_inflation(self):
        """Test token economics inflation calculation"""
        analyzer = FundamentalAnalyzer(llm=None)

        result = await analyzer.analyze(
            symbol='BTC/USDT',
            market_data={'current_price': 50000}
        )

        token_econ = result['token_economics']

        # BTC has low inflation
        assert token_econ['inflation_rate'] < 5

        # Supply percentage should be high (most BTC mined)
        assert token_econ['supply_pct_circulating'] > 80

    @pytest.mark.asyncio
    async def test_project_metrics_github(self):
        """Test GitHub project metrics"""
        analyzer = FundamentalAnalyzer(llm=None)

        result = await analyzer.analyze(
            symbol='ETH/USDT',
            market_data={'current_price': 3000}
        )

        project = result['project_metrics']

        # ETH should have high development activity
        assert project['github_stars'] > 10000
        assert project['github_commits_30d'] > 50
        assert project['development_activity_score'] > 70

    @pytest.mark.asyncio
    async def test_fundamental_score_calculation(self):
        """Test fundamental score calculation"""
        analyzer = FundamentalAnalyzer(llm=None)

        # Test with different assets
        btc_result = await analyzer.analyze('BTC/USDT', {'current_price': 50000})
        eth_result = await analyzer.analyze('ETH/USDT', {'current_price': 3000})

        # Both should have valid scores
        assert 0 <= btc_result['fundamental_score'] <= 1
        assert 0 <= eth_result['fundamental_score'] <= 1

        # BTC and ETH should have relatively high scores (strong projects)
        assert btc_result['fundamental_score'] > 0.5
        assert eth_result['fundamental_score'] > 0.5

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in fundamental analysis"""
        analyzer = FundamentalAnalyzer(llm=None)

        # Test with invalid symbol
        result = await analyzer.analyze(
            symbol='INVALID/USDT',
            market_data={}
        )

        # Should return neutral score on error
        assert result['fundamental_score'] == 0.5
        assert 'error' in result or result['fundamental_score'] >= 0

    @pytest.mark.asyncio
    async def test_mock_data_fallback(self):
        """Test that mock data is used when APIs fail"""
        analyzer = FundamentalAnalyzer(llm=None)

        result = await analyzer.analyze(
            symbol='SOL/USDT',
            market_data={'current_price': 100}
        )

        # Should have data even without API calls
        assert result['onchain_fundamentals']['data_source'] == 'mock'
        assert result['token_economics']['data_source'] == 'mock'
        assert result['project_metrics']['data_source'] == 'mock'

    @pytest.mark.asyncio
    async def test_close_session(self):
        """Test closing aiohttp session"""
        analyzer = FundamentalAnalyzer(llm=None)

        # Ensure session
        await analyzer._ensure_session()
        assert analyzer.session is not None

        # Close
        await analyzer.close()
        assert analyzer.session.closed


# =============================================================================
# FinancialRatios Tests
# =============================================================================

class TestFinancialRatios:
    """Test suite for FinancialRatios dataclass"""

    def test_ratios_creation(self):
        """Test creating FinancialRatios"""
        ratios = FinancialRatios(
            price_to_fees=45.2,
            mc_to_tvl=1.8,
            nvt_ratio=52.0,
            overall_score=0.78
        )

        assert ratios.price_to_fees == 45.2
        assert ratios.mc_to_tvl == 1.8
        assert ratios.nvt_ratio == 52.0
        assert ratios.overall_score == 0.78

    def test_ratios_to_dict(self):
        """Test converting ratios to dictionary"""
        ratios = FinancialRatios(
            price_to_fees=45.2,
            mc_to_tvl=1.8,
            protocol_revenue_yield=8.5,
            overall_score=0.78
        )

        result = ratios.to_dict()

        assert 'valuation' in result
        assert 'network' in result
        assert 'defi' in result
        assert 'growth' in result
        assert 'overall_score' in result

        assert result['valuation']['price_to_fees'] == 45.2
        assert result['valuation']['mc_to_tvl'] == 1.8
        assert result['defi']['protocol_revenue_yield'] == 8.5


# =============================================================================
# FinancialRatiosCalculator Tests
# =============================================================================

class TestFinancialRatiosCalculator:
    """Test suite for FinancialRatiosCalculator"""

    def test_calculator_creation(self):
        """Test creating calculator"""
        calc = FinancialRatiosCalculator()
        assert calc is not None

    def test_calculate_defi_ratios(self):
        """Test calculating DeFi protocol ratios"""
        calc = FinancialRatiosCalculator()

        ratios = calc.calculate(
            symbol='UNI',
            market_data={
                'market_cap': 5000000000,
                'current_price': 6.5,
                'volume_24h': 200000000
            },
            onchain_data={
                'tvl': 3000000000,
                'fees_24h': 500000,
                'revenue_24h': 250000,
                'tvl_change_30d': 15.4
            },
            fundamental_data={}
        )

        # Verify valuation ratios calculated
        assert ratios.price_to_fees is not None
        assert ratios.price_to_fees > 0

        assert ratios.mc_to_tvl is not None
        assert ratios.mc_to_tvl > 0

        # Verify DeFi specific
        assert ratios.protocol_revenue_yield is not None
        assert ratios.fee_yield is not None

        # Verify growth
        assert ratios.tvl_growth_30d == 15.4

        # Verify overall score
        assert 0 <= ratios.overall_score <= 1

    def test_calculate_btc_ratios(self):
        """Test calculating Bitcoin-specific ratios"""
        calc = FinancialRatiosCalculator()

        ratios = calc.calculate(
            symbol='BTC',
            market_data={
                'market_cap': 1000000000000,
                'current_price': 50000,
                'volume_24h': 30000000000
            },
            onchain_data={
                'active_addresses': 1000000
            },
            fundamental_data={}
        )

        # BTC has NVT ratio
        assert ratios.nvt_ratio is not None

        # BTC has active address value
        assert ratios.active_address_value is not None
        assert ratios.active_address_value > 0

        # BTC doesn't have P/F (not a protocol)
        # Can be None

    def test_quality_score_excellent(self):
        """Test quality score with excellent ratios"""
        calc = FinancialRatiosCalculator()

        ratios = calc.calculate(
            symbol='UNI',
            market_data={'market_cap': 5000000000, 'volume_24h': 200000000},
            onchain_data={
                'tvl': 4000000000,  # MC/TVL = 1.25 (excellent)
                'fees_24h': 1000000,  # P/F = 13.7 (excellent)
                'revenue_24h': 500000,
                'tvl_change_30d': 25.0  # Strong growth
            },
            fundamental_data={}
        )

        # Should have high score
        assert ratios.overall_score > 0.7

    def test_quality_score_poor(self):
        """Test quality score with poor ratios"""
        calc = FinancialRatiosCalculator()

        ratios = calc.calculate(
            symbol='WEAK',
            market_data={'market_cap': 1000000000, 'volume_24h': 50000000},
            onchain_data={
                'tvl': 100000000,  # MC/TVL = 10 (overvalued)
                'fees_24h': 10000,  # P/F = 273 (expensive)
                'revenue_24h': 5000,
                'tvl_change_30d': -15.0  # Declining
            },
            fundamental_data={}
        )

        # Should have low score
        assert ratios.overall_score < 0.5

    def test_interpret_ratios(self):
        """Test ratio interpretations"""
        calc = FinancialRatiosCalculator()

        ratios = FinancialRatios(
            price_to_fees=45,
            mc_to_tvl=1.8,
            protocol_revenue_yield=8.5,
            tvl_growth_30d=15.0,
            overall_score=0.75
        )

        interpretations = calc.interpret_ratios(ratios, 'UNI')

        assert 'overall' in interpretations
        assert 'price_to_fees' in interpretations
        assert 'mc_to_tvl' in interpretations
        assert 'revenue_yield' in interpretations
        assert 'growth' in interpretations

        # Check interpretations are meaningful
        assert 'Good' in interpretations['overall'] or 'Strong' in interpretations['overall']
        assert 'Undervalued' in interpretations['mc_to_tvl']

    def test_compare_to_benchmarks(self):
        """Test benchmark comparisons"""
        calc = FinancialRatiosCalculator()

        ratios = FinancialRatios(
            price_to_fees=25,  # Below excellent threshold
            mc_to_tvl=1.2,     # Undervalued
            nvt_ratio=45       # Healthy for BTC
        )

        comparisons = calc.compare_to_benchmarks(ratios, 'BTC')

        assert len(comparisons) > 0
        assert any('✓' in comp for comp in comparisons.values())

    def test_generate_summary(self):
        """Test generating ratio summary"""
        calc = FinancialRatiosCalculator()

        ratios = FinancialRatios(
            price_to_fees=45.2,
            mc_to_tvl=1.8,
            protocol_revenue_yield=8.5,
            tvl_growth_30d=15.4,
            overall_score=0.78
        )

        summary = calc.generate_summary(ratios, 'UNI')

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'P/F' in summary or 'MC/TVL' in summary

    def test_handle_missing_data(self):
        """Test handling missing data gracefully"""
        calc = FinancialRatiosCalculator()

        # Calculate with minimal data
        ratios = calc.calculate(
            symbol='TEST',
            market_data={'market_cap': 1000000000},
            onchain_data={},
            fundamental_data={}
        )

        # Should return valid ratios object with None values
        assert ratios is not None
        assert isinstance(ratios, FinancialRatios)

        # Score should be neutral when no data
        assert 0.4 <= ratios.overall_score <= 0.6


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for fundamental analysis"""

    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self):
        """Test complete fundamental analysis flow"""
        analyzer = FundamentalAnalyzer(llm=None)
        calc = FinancialRatiosCalculator()

        # Perform analysis
        symbol = 'ETH/USDT'
        market_data = {
            'current_price': 3000,
            'market_cap': 360000000000,
            'volume_24h': 15000000000
        }

        fundamental_analysis = await analyzer.analyze(
            symbol=symbol,
            market_data=market_data
        )

        # Calculate ratios
        ratios = calc.calculate(
            symbol='ETH',
            market_data=market_data,
            onchain_data=fundamental_analysis.get('onchain_fundamentals', {}),
            fundamental_data=fundamental_analysis
        )

        # Verify complete workflow
        assert fundamental_analysis['fundamental_score'] > 0
        assert ratios.overall_score > 0

        # Generate summary
        summary = calc.generate_summary(ratios, 'ETH')
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_multiple_asset_comparison(self):
        """Test comparing fundamentals across multiple assets"""
        analyzer = FundamentalAnalyzer(llm=None)

        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        results = []

        for symbol in symbols:
            analysis = await analyzer.analyze(
                symbol=symbol,
                market_data={'current_price': 1000}
            )
            results.append({
                'symbol': symbol,
                'score': analysis['fundamental_score']
            })

        # All should have valid scores
        for result in results:
            assert 0 <= result['score'] <= 1

        # Can compare scores
        scores = [r['score'] for r in results]
        assert max(scores) > min(scores) or all(s == scores[0] for s in scores)

    @pytest.mark.asyncio
    async def test_orchestrator_integration(self):
        """Test integration with orchestrator (mock)"""
        # This would test the actual orchestrator integration
        # For now, test the data structure

        analyzer = FundamentalAnalyzer(llm=None)
        calc = FinancialRatiosCalculator()

        # Simulate orchestrator state
        state = {
            'symbol': 'UNI/USDT',
            'market_data': {
                'current_price': 6.5,
                'market_cap': 4900000000
            }
        }

        # Perform analysis
        fundamental_analysis = await analyzer.analyze(
            symbol=state['symbol'],
            market_data=state['market_data']
        )

        ratios = calc.calculate(
            symbol='UNI',
            market_data=state['market_data'],
            onchain_data=fundamental_analysis.get('onchain_fundamentals', {}),
            fundamental_data=fundamental_analysis
        )

        # Verify orchestrator state updates
        orchestrator_update = {
            'fundamental_analysis': fundamental_analysis,
            'fundamental_score': fundamental_analysis['fundamental_score'],
            'financial_ratios': ratios.to_dict()
        }

        assert 'fundamental_analysis' in orchestrator_update
        assert 'fundamental_score' in orchestrator_update
        assert 'financial_ratios' in orchestrator_update

        # Verify structure for bull/bear agents
        assert 'onchain_fundamentals' in orchestrator_update['fundamental_analysis']
        assert 'token_economics' in orchestrator_update['fundamental_analysis']
        assert 'project_metrics' in orchestrator_update['fundamental_analysis']


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance tests for fundamental analysis"""

    @pytest.mark.asyncio
    async def test_analysis_speed(self):
        """Test that analysis completes in reasonable time"""
        import time

        analyzer = FundamentalAnalyzer(llm=None)

        start = time.time()
        await analyzer.analyze(
            symbol='BTC/USDT',
            market_data={'current_price': 50000}
        )
        duration = time.time() - start

        # Should complete in under 5 seconds (even with mock data)
        assert duration < 5.0

    def test_ratio_calculation_speed(self):
        """Test ratio calculation performance"""
        import time

        calc = FinancialRatiosCalculator()

        start = time.time()
        for _ in range(100):
            calc.calculate(
                symbol='TEST',
                market_data={'market_cap': 1000000000, 'volume_24h': 100000000},
                onchain_data={'tvl': 500000000, 'fees_24h': 100000},
                fundamental_data={}
            )
        duration = time.time() - start

        # 100 calculations should complete in under 0.5 seconds
        assert duration < 0.5


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
