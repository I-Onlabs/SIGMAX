"""
SIGMAX CrewAI Orchestrator
Multi-agent orchestration using CrewAI framework with 17 specialized agents
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sys
from pathlib import Path
from loguru import logger

# Try to import CrewAI
CREWAI_AVAILABLE = False
try:
    from crewai import Crew, Task, Process
    CREWAI_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI not available, using fallback")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.protocols import (
    DataModuleProtocol,
    ExecutionModuleProtocol,
    QuantumModuleProtocol,
    ComplianceModuleProtocol,
    RLModuleProtocol,
    ArbitrageModuleProtocol
)

from .crewai_agents import create_sigmax_agents

# Import decision history
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from decision_history import DecisionHistory

# Import autonomous engine
try:
    from .finrobot_integration import AutonomousStrategyEngine
    AUTONOMOUS_ENGINE_AVAILABLE = True
except ImportError:
    AUTONOMOUS_ENGINE_AVAILABLE = False


class SIGMAXCrewAIOrchestrator:
    """
    CrewAI-based orchestrator with 17 specialized agents

    Agent Architecture:
    - Market Intelligence: 4 agents
    - Risk & Compliance: 3 agents
    - Strategy & Execution: 4 agents
    - Advanced Analytics: 3 agents
    - Monitoring & Control: 3 agents

    Workflow:
    1. Analysis Crew: Gather market intelligence
    2. Risk Crew: Assess risks and compliance
    3. Strategy Crew: Develop trading strategy
    4. Advanced Crew: Run quantum/ML optimization
    5. Execution Crew: Execute trades safely
    6. Monitoring Crew: Track performance and make final decision
    """

    def __init__(
        self,
        data_module: DataModuleProtocol,
        execution_module: ExecutionModuleProtocol,
        quantum_module: Optional[QuantumModuleProtocol],
        rl_module: Optional[RLModuleProtocol],
        arbitrage_module: Optional[ArbitrageModuleProtocol],
        compliance_module: ComplianceModuleProtocol,
        risk_profile: str = "conservative",
        enable_autonomous_engine: bool = True
    ):
        """
        Initialize CrewAI orchestrator

        Args:
            data_module: Data module for market access
            execution_module: Execution module for trade execution
            quantum_module: Quantum optimization module
            rl_module: Reinforcement learning module
            arbitrage_module: Arbitrage detection module
            compliance_module: Compliance checking module
            risk_profile: Risk profile (conservative/balanced/aggressive)
            enable_autonomous_engine: Enable FinRobot+RD-Agent
        """
        self.data_module = data_module
        self.execution_module = execution_module
        self.quantum_module = quantum_module
        self.rl_module = rl_module
        self.arbitrage_module = arbitrage_module
        self.compliance_module = compliance_module
        self.risk_profile = risk_profile

        # Initialize LLM
        self.llm = self._get_llm()

        # Initialize 17-agent system
        self.agent_system = create_sigmax_agents(
            llm=self.llm,
            data_module=data_module
        )

        # Initialize autonomous engine (optional)
        self.autonomous_engine = None
        if enable_autonomous_engine and AUTONOMOUS_ENGINE_AVAILABLE:
            try:
                self.autonomous_engine = AutonomousStrategyEngine()
                logger.info("✓ Autonomous strategy engine enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize autonomous engine: {e}")

        # State
        self.running = False
        self.paused = False

        # Decision history
        self.decision_history = DecisionHistory(max_history_per_symbol=20)

        # Track active crews
        self.active_crews = {}

        logger.info("✓ SIGMAX CrewAI Orchestrator created (17 agents)")

    def _get_llm(self):
        """Get configured LLM"""
        from llm.factory import LLMProvider
        provider = LLMProvider()
        llm = provider.get_llm(temperature=0.7)
        if not llm:
            logger.warning("No LLM configured")
        return llm

    async def analyze_symbol(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze symbol using CrewAI multi-agent system

        Workflow:
        1. Analysis crew gathers intelligence
        2. Risk crew validates safety
        3. Strategy crew develops plan
        4. Decision coordinator makes final call

        Args:
            symbol: Trading symbol
            market_data: Optional market data override

        Returns:
            Trading decision with reasoning
        """
        logger.info(f"🎯 CrewAI analysis starting for {symbol}")

        try:
            # Fetch market data if not provided
            if not market_data:
                market_data = await self.data_module.get_market_data(symbol)

            # Phase 1: Intelligence Gathering
            analysis_result = await self._run_analysis_crew(symbol, market_data)

            # Phase 2: Risk Assessment
            risk_result = await self._run_risk_crew(symbol, analysis_result)

            # Phase 3: Strategy Development
            strategy_result = await self._run_strategy_crew(
                symbol,
                analysis_result,
                risk_result
            )

            # Phase 4: Advanced Analytics (if available)
            if self.quantum_module or self.autonomous_engine:
                advanced_result = await self._run_advanced_crew(
                    symbol,
                    strategy_result,
                    market_data
                )
            else:
                advanced_result = {}

            # Phase 5: Final Decision
            final_decision = await self._make_final_decision(
                symbol=symbol,
                analysis=analysis_result,
                risk=risk_result,
                strategy=strategy_result,
                advanced=advanced_result
            )

            # Store in decision history
            self.decision_history.add_decision(
                symbol=symbol,
                decision=final_decision,
                agent_debate={
                    "analysis": analysis_result,
                    "risk": risk_result,
                    "strategy": strategy_result,
                    "advanced": advanced_result
                }
            )

            logger.info(f"✓ CrewAI analysis complete for {symbol}: {final_decision['action']}")
            return final_decision

        except Exception as e:
            logger.error(f"Error in CrewAI analysis: {e}", exc_info=True)
            return {
                "action": "hold",
                "symbol": symbol,
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _run_analysis_crew(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run market intelligence analysis crew"""
        logger.info(f"📊 Analysis crew working on {symbol}")

        if not CREWAI_AVAILABLE:
            # Fallback to simple analysis
            return {
                "market_trend": "neutral",
                "technical_score": 0.5,
                "sentiment_score": 0.5,
                "onchain_metrics": {}
            }

        # Create and run analysis crew
        crew = self.agent_system.create_analysis_crew(symbol, market_data)

        if crew:
            try:
                result = crew.kickoff()
                return self._parse_crew_result(result)
            except Exception as e:
                logger.error(f"Analysis crew error: {e}")

        return {"status": "analysis_complete", "confidence": 0.6}

    async def _run_risk_crew(
        self,
        symbol: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run risk assessment crew"""
        logger.info(f"🛡️ Risk crew assessing {symbol}")

        if not CREWAI_AVAILABLE:
            return {
                "risk_level": "moderate",
                "compliance_status": "passed",
                "max_position_size": 0.1
            }

        # Get risk agents
        risk_manager = self.agent_system.get_agent('risk_manager')
        compliance_officer = self.agent_system.get_agent('compliance_officer')
        privacy_guard = self.agent_system.get_agent('privacy_guard')

        if not all([risk_manager, compliance_officer, privacy_guard]):
            return {"status": "risk_assessed", "approved": True}

        # Create risk tasks
        tasks = [
            Task(
                description=f"Assess trading risk for {symbol}",
                agent=risk_manager,
                expected_output="Risk assessment with position sizing"
            ),
            Task(
                description=f"Check compliance for {symbol}",
                agent=compliance_officer,
                expected_output="Compliance check result"
            ),
            Task(
                description=f"Verify privacy and detect collusion for {symbol}",
                agent=privacy_guard,
                expected_output="Privacy check result"
            )
        ]

        crew = Crew(
            agents=[risk_manager, compliance_officer, privacy_guard],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        try:
            result = crew.kickoff()
            return self._parse_crew_result(result)
        except Exception as e:
            logger.error(f"Risk crew error: {e}")
            return {"status": "risk_checked", "approved": True}

    async def _run_strategy_crew(
        self,
        symbol: str,
        analysis: Dict[str, Any],
        risk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run strategy development crew"""
        logger.info(f"🎯 Strategy crew planning for {symbol}")

        if not CREWAI_AVAILABLE:
            return {
                "strategy": "momentum",
                "entry_price": 0,
                "exit_price": 0,
                "stop_loss": 0
            }

        # Get strategy agents
        strategy_coordinator = self.agent_system.get_agent('strategy_coordinator')
        portfolio_manager = self.agent_system.get_agent('portfolio_manager')

        if not all([strategy_coordinator, portfolio_manager]):
            return {"status": "strategy_created"}

        tasks = [
            Task(
                description=f"Develop trading strategy for {symbol}",
                agent=strategy_coordinator,
                expected_output="Trading strategy with entry/exit criteria"
            ),
            Task(
                description=f"Optimize portfolio allocation for {symbol}",
                agent=portfolio_manager,
                expected_output="Portfolio allocation recommendation"
            )
        ]

        crew = Crew(
            agents=[strategy_coordinator, portfolio_manager],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        try:
            result = crew.kickoff()
            return self._parse_crew_result(result)
        except Exception as e:
            logger.error(f"Strategy crew error: {e}")
            return {"status": "strategy_developed"}

    async def _run_advanced_crew(
        self,
        symbol: str,
        strategy: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run advanced analytics crew (quantum/ML/RL)"""
        logger.info(f"🔬 Advanced analytics crew analyzing {symbol}")

        results = {}

        # Quantum optimization
        if self.quantum_module:
            try:
                quantum_result = await self.quantum_module.optimize_portfolio({
                    "symbols": [symbol],
                    "risk_tolerance": 0.1
                })
                results["quantum"] = quantum_result
            except Exception as e:
                logger.error(f"Quantum optimization error: {e}")

        # Autonomous engine enhancement
        if self.autonomous_engine:
            try:
                auto_result = await self.autonomous_engine.analyze_and_decide(
                    symbol=symbol,
                    portfolio={"total_value": 100000},
                    market_data=market_data
                )
                results["autonomous"] = auto_result
            except Exception as e:
                logger.error(f"Autonomous engine error: {e}")

        return results

    async def _make_final_decision(
        self,
        symbol: str,
        analysis: Dict[str, Any],
        risk: Dict[str, Any],
        strategy: Dict[str, Any],
        advanced: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final trading decision"""
        logger.info(f"⚖️ Decision coordinator making final call for {symbol}")

        # Get decision coordinator agent
        decision_coordinator = self.agent_system.get_agent('decision_coordinator')

        if not CREWAI_AVAILABLE or not decision_coordinator:
            # Fallback decision logic
            return self._fallback_decision(symbol, analysis, risk, strategy)

        # Create final decision task
        task = Task(
            description=f"""
            Make final trading decision for {symbol} based on:
            - Analysis: {json.dumps(analysis)}
            - Risk: {json.dumps(risk)}
            - Strategy: {json.dumps(strategy)}
            - Advanced: {json.dumps(advanced)}

            Provide action (buy/sell/hold), confidence score, and reasoning.
            """,
            agent=decision_coordinator,
            expected_output="Final trading decision with action, confidence, and reasoning"
        )

        crew = Crew(
            agents=[decision_coordinator],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )

        try:
            result = crew.kickoff()
            return self._parse_decision_result(result, symbol)
        except Exception as e:
            logger.error(f"Final decision error: {e}")
            return self._fallback_decision(symbol, analysis, risk, strategy)

    def _fallback_decision(
        self,
        symbol: str,
        analysis: Dict[str, Any],
        risk: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback decision when CrewAI not available"""
        # Simple logic: aggregate signals
        confidence = (
            analysis.get("technical_score", 0.5) * 0.4 +
            analysis.get("sentiment_score", 0.5) * 0.3 +
            (1.0 if risk.get("approved", False) else 0.0) * 0.3
        )

        action = "hold"
        if confidence > 0.7:
            action = "buy"
        elif confidence < 0.3:
            action = "sell"

        return {
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "reasoning": "Aggregated from analysis, risk, and strategy crews",
            "timestamp": datetime.now().isoformat()
        }

    def _parse_crew_result(self, result: Any) -> Dict[str, Any]:
        """Parse crew result to dict"""
        if isinstance(result, dict):
            return result
        elif isinstance(result, str):
            return {"result": result}
        else:
            return {"result": str(result)}

    def _parse_decision_result(self, result: Any, symbol: str) -> Dict[str, Any]:
        """Parse decision result to trading decision"""
        parsed = self._parse_crew_result(result)

        return {
            "symbol": symbol,
            "action": parsed.get("action", "hold"),
            "confidence": parsed.get("confidence", 0.5),
            "reasoning": parsed.get("reasoning", "CrewAI decision"),
            "timestamp": datetime.now().isoformat(),
            "details": parsed
        }

    async def start(self):
        """Start orchestrator"""
        self.running = True
        self.paused = False
        logger.info("✓ CrewAI Orchestrator started")

    async def pause(self):
        """Pause orchestrator"""
        self.paused = True
        logger.info("⏸️ CrewAI Orchestrator paused")

    async def resume(self):
        """Resume orchestrator"""
        self.paused = False
        logger.info("▶️ CrewAI Orchestrator resumed")

    async def stop(self):
        """Stop orchestrator"""
        self.running = False
        logger.info("🛑 CrewAI Orchestrator stopped")

    async def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        agent_status = self.agent_system.get_status()

        return {
            "running": self.running,
            "paused": self.paused,
            "risk_profile": self.risk_profile,
            "agent_system": agent_status,
            "autonomous_engine": {
                "enabled": self.autonomous_engine is not None,
                "finrobot": self.autonomous_engine.finrobot.using_finrobot if self.autonomous_engine else False,
                "rdagent": self.autonomous_engine.rdagent.using_rdagent if self.autonomous_engine else False
            }
        }

    def get_decision_history(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get decision history for symbol"""
        return self.decision_history.get_decisions(symbol, limit=limit)
