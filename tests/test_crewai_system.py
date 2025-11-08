"""
Tests for CrewAI Agent System
"""

import pytest
import asyncio
from core.agents.crewai_agents import SIGMAXCrewAIAgents, create_sigmax_agents, CREWAI_AVAILABLE
from core.agents.crewai_orchestrator import SIGMAXCrewAIOrchestrator


class MockDataModule:
    """Mock data module for testing"""
    async def get_market_data(self, symbol):
        return {
            "price": 50000,
            "volume": 1000000,
            "volatility": 0.2
        }


class MockExecutionModule:
    """Mock execution module"""
    async def execute_order(self, order):
        return {"status": "filled", "order_id": "test123"}


class MockQuantumModule:
    """Mock quantum module"""
    async def optimize_portfolio(self, portfolio):
        return {"optimized": True, "allocation": {}}


class MockComplianceModule:
    """Mock compliance module"""
    async def check_compliance(self, trade):
        return {"compliant": True}


class TestSIGMAXCrewAIAgents:
    """Test 17-agent system"""

    def test_agent_system_initialization(self):
        """Test agent system initializes correctly"""
        agent_system = create_sigmax_agents()

        assert agent_system is not None
        assert isinstance(agent_system.agents, dict)

        # If CrewAI available, should have 17 agents
        if CREWAI_AVAILABLE:
            assert len(agent_system.agents) == 17
            assert len(agent_system.crews) == 6

    def test_agent_system_list_agents(self):
        """Test listing all agents"""
        agent_system = create_sigmax_agents()
        agents = agent_system.list_agents()

        assert isinstance(agents, list)

        if CREWAI_AVAILABLE:
            assert len(agents) == 17

            # Check key agents exist
            assert 'market_researcher' in agents
            assert 'technical_analyst' in agents
            assert 'sentiment_analyst' in agents
            assert 'onchain_analyst' in agents
            assert 'risk_manager' in agents
            assert 'compliance_officer' in agents
            assert 'privacy_guard' in agents
            assert 'strategy_coordinator' in agents
            assert 'portfolio_manager' in agents
            assert 'execution_specialist' in agents
            assert 'arbitrage_hunter' in agents
            assert 'quantum_optimizer' in agents
            assert 'ml_predictor' in agents
            assert 'rl_agent' in agents
            assert 'performance_monitor' in agents
            assert 'safety_enforcer' in agents
            assert 'decision_coordinator' in agents

    def test_agent_system_list_crews(self):
        """Test listing all crews"""
        agent_system = create_sigmax_agents()
        crews = agent_system.list_crews()

        assert isinstance(crews, list)

        if CREWAI_AVAILABLE:
            assert len(crews) == 6
            assert 'analysis' in crews
            assert 'risk' in crews
            assert 'strategy' in crews
            assert 'advanced' in crews
            assert 'execution' in crews
            assert 'monitoring' in crews

    def test_get_specific_agent(self):
        """Test retrieving specific agents"""
        agent_system = create_sigmax_agents()

        market_researcher = agent_system.get_agent('market_researcher')
        # May be None if CrewAI not available (fallback mode)
        assert market_researcher is not None or not CREWAI_AVAILABLE

        decision_coordinator = agent_system.get_agent('decision_coordinator')
        assert decision_coordinator is not None or not CREWAI_AVAILABLE

    def test_get_specific_crew(self):
        """Test retrieving specific crews"""
        agent_system = create_sigmax_agents()

        analysis_crew = agent_system.get_crew('analysis')
        # May be None if CrewAI not available (fallback mode)
        assert analysis_crew is not None or not CREWAI_AVAILABLE

        if CREWAI_AVAILABLE and analysis_crew:
            assert 'agents' in analysis_crew
            assert 'description' in analysis_crew

    def test_create_analysis_crew(self):
        """Test creating analysis crew for symbol"""
        agent_system = create_sigmax_agents()

        crew = agent_system.create_analysis_crew(
            symbol="BTCUSDT",
            market_data={"price": 50000}
        )

        # Should return crew or None
        assert crew is not None or not CREWAI_AVAILABLE

    def test_create_decision_crew(self):
        """Test creating decision crew"""
        agent_system = create_sigmax_agents()

        crew = agent_system.create_decision_crew(
            symbol="BTCUSDT",
            analysis_results={"trend": "bullish"},
            risk_assessment={"approved": True}
        )

        # Should return crew or None
        assert crew is not None or not CREWAI_AVAILABLE

    def test_agent_system_status(self):
        """Test getting system status"""
        agent_system = create_sigmax_agents()
        status = agent_system.get_status()

        assert isinstance(status, dict)
        assert "crewai_available" in status
        assert "total_agents" in status
        assert "total_crews" in status
        assert "agents" in status
        assert "crews" in status


class TestSIGMAXCrewAIOrchestrator:
    """Test CrewAI orchestrator"""

    def setup_orchestrator(self):
        """Setup orchestrator for tests"""
        return SIGMAXCrewAIOrchestrator(
            data_module=MockDataModule(),
            execution_module=MockExecutionModule(),
            quantum_module=MockQuantumModule(),
            rl_module=None,
            arbitrage_module=None,
            compliance_module=MockComplianceModule(),
            risk_profile="conservative",
            enable_autonomous_engine=False  # Disable for faster tests
        )

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly"""
        orchestrator = self.setup_orchestrator()

        assert orchestrator is not None
        assert orchestrator.agent_system is not None
        assert orchestrator.running == False
        assert orchestrator.paused == False

    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self):
        """Test starting and stopping orchestrator"""
        orchestrator = self.setup_orchestrator()

        await orchestrator.start()
        assert orchestrator.running == True
        assert orchestrator.paused == False

        await orchestrator.pause()
        assert orchestrator.paused == True

        await orchestrator.resume()
        assert orchestrator.paused == False

        await orchestrator.stop()
        assert orchestrator.running == False

    @pytest.mark.asyncio
    async def test_orchestrator_get_status(self):
        """Test getting orchestrator status"""
        orchestrator = self.setup_orchestrator()
        status = await orchestrator.get_status()

        assert isinstance(status, dict)
        assert "running" in status
        assert "paused" in status
        assert "risk_profile" in status
        assert "agent_system" in status
        assert "autonomous_engine" in status

        assert status["risk_profile"] == "conservative"

    @pytest.mark.asyncio
    async def test_orchestrator_analyze_symbol(self):
        """Test analyzing a symbol with CrewAI"""
        orchestrator = self.setup_orchestrator()

        result = await orchestrator.analyze_symbol(
            symbol="BTCUSDT",
            market_data={"price": 50000, "volume": 1000000}
        )

        assert isinstance(result, dict)
        assert "symbol" in result or "action" in result
        assert "timestamp" in result

        # Should have an action
        if "action" in result:
            assert result["action"] in ["buy", "sell", "hold"]

        # Should have confidence
        if "confidence" in result:
            assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_orchestrator_decision_history(self):
        """Test decision history tracking"""
        orchestrator = self.setup_orchestrator()

        # Make a decision
        await orchestrator.analyze_symbol("BTCUSDT")

        # Get history
        history = orchestrator.get_decision_history("BTCUSDT")

        assert isinstance(history, list)
        if len(history) > 0:
            assert "timestamp" in history[0]

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_mode(self):
        """Test orchestrator works in fallback mode"""
        orchestrator = self.setup_orchestrator()

        # Should work even if CrewAI not available
        result = await orchestrator.analyze_symbol("ETHUSDT")

        assert result is not None
        assert isinstance(result, dict)


class TestCrewAIIntegration:
    """Test full integration scenarios"""

    def setup_full_orchestrator(self):
        """Setup orchestrator with all modules"""
        return SIGMAXCrewAIOrchestrator(
            data_module=MockDataModule(),
            execution_module=MockExecutionModule(),
            quantum_module=MockQuantumModule(),
            rl_module=None,
            arbitrage_module=None,
            compliance_module=MockComplianceModule(),
            enable_autonomous_engine=True
        )

    @pytest.mark.asyncio
    async def test_full_trading_workflow(self):
        """Test complete trading workflow"""
        orchestrator = self.setup_full_orchestrator()

        await orchestrator.start()

        # Analyze symbol
        decision = await orchestrator.analyze_symbol("BTCUSDT")

        assert decision is not None
        assert "action" in decision

        # Check status
        status = await orchestrator.get_status()
        assert status["running"] == True

        await orchestrator.stop()

    @pytest.mark.asyncio
    async def test_multiple_symbol_analysis(self):
        """Test analyzing multiple symbols"""
        orchestrator = self.setup_full_orchestrator()

        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        results = []

        for symbol in symbols:
            result = await orchestrator.analyze_symbol(symbol)
            results.append(result)

        assert len(results) == 3
        for result in results:
            assert "symbol" in result or "action" in result

    def test_agent_count_verification(self):
        """Verify we have exactly 17 agents as per October vision"""
        agent_system = create_sigmax_agents()

        if CREWAI_AVAILABLE:
            assert len(agent_system.agents) == 17, "Should have exactly 17 agents"

            # Verify agent categories
            market_intel = ['market_researcher', 'technical_analyst', 'sentiment_analyst', 'onchain_analyst']
            risk_compliance = ['risk_manager', 'compliance_officer', 'privacy_guard']
            strategy_exec = ['strategy_coordinator', 'portfolio_manager', 'execution_specialist', 'arbitrage_hunter']
            advanced = ['quantum_optimizer', 'ml_predictor', 'rl_agent']
            monitoring = ['performance_monitor', 'safety_enforcer', 'decision_coordinator']

            all_expected = market_intel + risk_compliance + strategy_exec + advanced + monitoring
            assert len(all_expected) == 17

            for agent_name in all_expected:
                assert agent_name in agent_system.agents, f"Missing agent: {agent_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
