"""
Unit tests for SIGMAX Orchestrator
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.agents.orchestrator import SIGMAXOrchestrator, AgentState


class TestSIGMAXOrchestrator:
    """Test suite for multi-agent orchestrator"""

    @pytest.fixture
    def mock_modules(self):
        """Create mock modules for testing"""
        return {
            'data_module': AsyncMock(),
            'execution_module': AsyncMock(),
            'quantum_module': AsyncMock(),
            'rl_module': AsyncMock(),
            'arbitrage_module': AsyncMock(),
            'compliance_module': AsyncMock()
        }

    @pytest.fixture
    def orchestrator(self, mock_modules):
        """Create orchestrator instance"""
        return SIGMAXOrchestrator(
            **mock_modules,
            risk_profile='conservative'
        )

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly"""
        assert orchestrator is not None
        assert orchestrator.risk_profile == 'conservative'
        assert orchestrator.running is False

    @pytest.mark.asyncio
    async def test_initialize_workflow(self, orchestrator):
        """Test workflow initialization"""
        await orchestrator.initialize()

        assert orchestrator.app is not None
        assert orchestrator.researcher is not None
        assert orchestrator.analyzer is not None

    @pytest.mark.asyncio
    async def test_analyze_symbol(self, orchestrator, mock_modules):
        """Test symbol analysis"""
        # Setup mocks
        mock_modules['data_module'].get_market_data = AsyncMock(return_value={
            'symbol': 'BTC/USDT',
            'price': 95000.0,
            'volume_24h': 1000000000.0
        })

        # Initialize
        await orchestrator.initialize()

        # Analyze
        result = await orchestrator.analyze_symbol('BTC/USDT')

        assert result is not None
        assert 'action' in result
        assert result['action'] in ['buy', 'sell', 'hold']

    @pytest.mark.asyncio
    async def test_bull_agent_bullish_signal(self, orchestrator):
        """Test bull agent generates bullish arguments"""
        await orchestrator.initialize()

        state = {
            'symbol': 'BTC/USDT',
            'current_price': 95000.0,
            'research_summary': 'Positive news',
            'messages': []
        }

        result = await orchestrator._bull_node(state)

        assert 'bull_argument' in result
        assert result['bull_argument'] is not None

    @pytest.mark.asyncio
    async def test_bear_agent_bearish_signal(self, orchestrator):
        """Test bear agent generates bearish arguments"""
        await orchestrator.initialize()

        state = {
            'symbol': 'BTC/USDT',
            'current_price': 95000.0,
            'research_summary': 'Negative news',
            'bull_argument': 'Price going up',
            'messages': []
        }

        result = await orchestrator._bear_node(state)

        assert 'bear_argument' in result
        assert result['bear_argument'] is not None

    @pytest.mark.asyncio
    async def test_risk_validation(self, orchestrator, mock_modules):
        """Test risk agent validation"""
        await orchestrator.initialize()

        state = {
            'symbol': 'BTC/USDT',
            'bull_argument': 'Strong momentum',
            'bear_argument': 'High risk',
            'technical_analysis': 'RSI neutral',
            'messages': []
        }

        result = await orchestrator._risk_node(state)

        assert 'risk_assessment' in result
        assert 'approved' in result['risk_assessment']

    @pytest.mark.asyncio
    async def test_decision_making(self, orchestrator):
        """Test final decision making"""
        await orchestrator.initialize()

        state = {
            'symbol': 'BTC/USDT',
            'sentiment_score': 0.5,
            'confidence': 0.7,
            'risk_assessment': {'approved': True},
            'compliance_check': {'approved': True},
            'messages': []
        }

        result = await orchestrator._decision_node(state)

        assert 'final_decision' in result
        assert result['final_decision']['action'] in ['buy', 'sell', 'hold']
        assert 'confidence' in result['final_decision']

    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self, orchestrator):
        """Test starting and stopping orchestrator"""
        await orchestrator.initialize()

        await orchestrator.start()
        assert orchestrator.running is True

        await orchestrator.stop()
        assert orchestrator.running is False

    @pytest.mark.asyncio
    async def test_orchestrator_pause_resume(self, orchestrator):
        """Test pausing and resuming orchestrator"""
        await orchestrator.initialize()
        await orchestrator.start()

        await orchestrator.pause()
        assert orchestrator.paused is True

        await orchestrator.resume()
        assert orchestrator.paused is False

        await orchestrator.stop()

    def test_extract_score_positive(self, orchestrator):
        """Test score extraction from positive text"""
        text = "strong bullish momentum with growth potential"
        score = orchestrator._extract_score(text)

        assert score > 0

    def test_extract_score_negative(self, orchestrator):
        """Test score extraction from negative text"""
        text = "weak bearish trend with high risk of downtrend"
        score = orchestrator._extract_score(text)

        assert score < 0

    def test_extract_score_neutral(self, orchestrator):
        """Test score extraction from neutral text"""
        text = "market conditions are uncertain"
        score = orchestrator._extract_score(text)

        assert -0.5 < score < 0.5
