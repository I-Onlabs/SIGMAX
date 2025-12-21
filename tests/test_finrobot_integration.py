"""
Tests for FinRobot + RD-Agent Integration
"""

import pytest
from core.agents.finrobot_integration import (
    FinRobotAgentWrapper,
    RDAgentWrapper,
    AutonomousStrategyEngine,
    FINROBOT_AVAILABLE,
    RDAGENT_AVAILABLE
)


class TestFinRobotIntegration:
    """Test FinRobot integration"""

    def test_finrobot_initialization(self):
        """Test FinRobot wrapper initializes correctly"""
        wrapper = FinRobotAgentWrapper(model="gpt-4")
        assert wrapper is not None
        assert wrapper.model == "gpt-4"
        assert isinstance(wrapper.agents, dict)
        # Agents may be empty if FinRobot not installed (fallback mode)
        # That's okay - the wrapper should still work

    def test_finrobot_availability_status(self):
        """Test availability status is reported correctly"""
        wrapper = FinRobotAgentWrapper()
        # Should work in fallback mode even if FinRobot not installed
        assert wrapper is not None

    @pytest.mark.asyncio
    async def test_market_analysis(self):
        """Test market analysis functionality"""
        wrapper = FinRobotAgentWrapper()
        result = await wrapper.analyze_market(
            symbol="BTCUSDT",
            context={"timeframe": "1h", "indicators": ["RSI", "MACD"]}
        )

        assert result is not None
        assert "symbol" in result
        assert result["symbol"] == "BTCUSDT"
        assert "trend" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_risk_assessment(self):
        """Test risk assessment functionality"""
        wrapper = FinRobotAgentWrapper()
        portfolio = {
            "total_value": 100000,
            "positions": [
                {"symbol": "BTCUSDT", "size": 0.5, "value": 50000}
            ]
        }

        result = await wrapper.assess_risk(portfolio)

        assert result is not None
        assert "overall_risk" in result
        assert "risk_score" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_portfolio_optimization(self):
        """Test portfolio optimization"""
        wrapper = FinRobotAgentWrapper()
        portfolio = {"total_value": 100000}
        market_data = {"volatility": 0.2}

        result = await wrapper.optimize_portfolio(portfolio, market_data)

        assert result is not None
        assert "recommended_allocation" in result
        assert "expected_return" in result
        assert "expected_risk" in result

    @pytest.mark.asyncio
    async def test_strategy_generation(self):
        """Test strategy generation"""
        wrapper = FinRobotAgentWrapper()
        market_conditions = {"trend": "bullish", "volatility": "moderate"}
        performance_history = []

        result = await wrapper.generate_strategy(market_conditions, performance_history)

        assert result is not None
        assert "name" in result
        assert "entry_criteria" in result
        assert "exit_criteria" in result


class TestRDAgentIntegration:
    """Test RD-Agent integration"""

    def test_rdagent_initialization(self):
        """Test RD-Agent wrapper initializes correctly"""
        wrapper = RDAgentWrapper()
        assert wrapper is not None

    @pytest.mark.asyncio
    async def test_strategy_evolution(self):
        """Test strategy evolution functionality"""
        wrapper = RDAgentWrapper()
        strategy = {
            "name": "Test Strategy",
            "version": 1
        }
        performance_metrics = {
            "sharpe_ratio": 1.5,
            "max_drawdown": 0.15
        }
        market_data = {}

        result = await wrapper.evolve_strategy(strategy, performance_metrics, market_data)

        assert result is not None
        assert "name" in result
        # Should be same or evolved version
        assert result["version"] >= strategy["version"]

    @pytest.mark.asyncio
    async def test_strategy_research(self):
        """Test new strategy research"""
        wrapper = RDAgentWrapper()
        market_conditions = {"volatility": "high"}
        constraints = {"max_risk": 0.05}

        result = await wrapper.research_new_strategies(market_conditions, constraints)

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_strategy_evaluation(self):
        """Test strategy evaluation"""
        wrapper = RDAgentWrapper()
        strategy = {"name": "Test Strategy"}
        backtest_data = {"returns": [0.01, 0.02, -0.01, 0.03]}

        result = await wrapper.evaluate_strategy(strategy, backtest_data)

        assert result is not None
        assert "viable" in result
        assert "score" in result


class TestAutonomousStrategyEngine:
    """Test combined autonomous strategy engine"""

    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        engine = AutonomousStrategyEngine(model="gpt-4")
        assert engine is not None
        assert engine.finrobot is not None
        assert engine.rdagent is not None

    @pytest.mark.asyncio
    async def test_analyze_and_decide(self):
        """Test combined analysis and decision"""
        engine = AutonomousStrategyEngine()

        result = await engine.analyze_and_decide(
            symbol="BTCUSDT",
            portfolio={"total_value": 100000},
            market_data={"volatility": 0.2}
        )

        assert result is not None
        assert "market_analysis" in result
        assert "risk_assessment" in result
        assert "portfolio_optimization" in result
        assert "overall_confidence" in result

    @pytest.mark.asyncio
    async def test_evolve_and_improve(self):
        """Test strategy evolution and improvement"""
        engine = AutonomousStrategyEngine()

        strategy = {"name": "Test Strategy", "version": 1}
        performance_history = [
            {"return": 0.01},
            {"return": 0.02},
            {"return": -0.01}
        ]
        market_data = {}

        result = await engine.evolve_and_improve(strategy, performance_history, market_data)

        assert result is not None
        assert "evolved_strategy" in result
        assert "evaluation" in result


class TestIntegrationStatus:
    """Test integration status reporting"""

    def test_package_availability(self):
        """Test package availability flags are set"""
        assert isinstance(FINROBOT_AVAILABLE, bool)
        assert isinstance(RDAGENT_AVAILABLE, bool)

    def test_fallback_mode(self):
        """Test system works in fallback mode"""
        # Should work even if packages not installed
        engine = AutonomousStrategyEngine()
        assert engine is not None

        # Check if using fallback or real implementation
        if not FINROBOT_AVAILABLE:
            assert not engine.finrobot.using_finrobot

        if not RDAGENT_AVAILABLE:
            assert not engine.rdagent.using_rdagent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
