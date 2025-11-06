"""
SIGMAX Multi-Agent Orchestrator using LangGraph
Coordinates bull/bear/researcher debate system
"""

import asyncio
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import json
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger
import operator

# Add parent directory to path for protocol imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.protocols import (
    DataModuleProtocol,
    ExecutionModuleProtocol,
    QuantumModuleProtocol,
    ComplianceModuleProtocol,
    RLModuleProtocol,
    ArbitrageModuleProtocol
)

from .researcher import ResearcherAgent
from .analyzer import AnalyzerAgent
from .optimizer import OptimizerAgent
from .risk import RiskAgent
from .privacy import PrivacyAgent


class AgentState(TypedDict):
    """State shared across all agents in the debate"""
    messages: Annotated[List[dict], operator.add]
    symbol: str
    current_price: float
    market_data: Dict[str, Any]
    bull_argument: Optional[str]
    bear_argument: Optional[str]
    research_summary: Optional[str]
    technical_analysis: Optional[str]
    sentiment_score: float
    risk_assessment: Dict[str, Any]
    compliance_check: Dict[str, Any]
    final_decision: Optional[Dict[str, Any]]
    confidence: float
    iteration: int
    max_iterations: int


class SIGMAXOrchestrator:
    """
    Multi-agent orchestrator using LangGraph for structured debate

    Agent Flow:
    1. Researcher gathers market intelligence
    2. Bull agent presents bullish case
    3. Bear agent presents bearish case
    4. Analyzer performs technical + sentiment analysis
    5. Risk agent validates against policies
    6. Privacy agent checks for PII/collusion
    7. Optimizer suggests optimal action
    8. Final decision with confidence score
    """

    def __init__(
        self,
        data_module: DataModuleProtocol,
        execution_module: ExecutionModuleProtocol,
        quantum_module: Optional[QuantumModuleProtocol],
        rl_module: Optional[RLModuleProtocol],
        arbitrage_module: Optional[ArbitrageModuleProtocol],
        compliance_module: ComplianceModuleProtocol,
        risk_profile: str = "conservative"
    ):
        """
        Initialize SIGMAX Orchestrator with dependency injection

        Args:
            data_module: Module implementing DataModuleProtocol
            execution_module: Module implementing ExecutionModuleProtocol
            quantum_module: Optional module implementing QuantumModuleProtocol
            rl_module: Optional module implementing RLModuleProtocol
            arbitrage_module: Optional module implementing ArbitrageModuleProtocol
            compliance_module: Module implementing ComplianceModuleProtocol
            risk_profile: Risk profile ('conservative', 'balanced', 'aggressive')
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

        # Initialize agents
        self.researcher = ResearcherAgent(self.llm)
        self.analyzer = AnalyzerAgent(self.llm, data_module)
        self.optimizer = OptimizerAgent(self.llm, quantum_module)
        self.risk_agent = RiskAgent(self.llm, compliance_module)
        self.privacy_agent = PrivacyAgent(self.llm)

        # LangGraph workflow
        self.workflow: Optional[StateGraph] = None
        self.app = None

        # State
        self.running = False
        self.paused = False

        logger.info("✓ SIGMAX Orchestrator created")

    def _get_llm(self):
        """Get configured LLM with fallback"""
        import sys
        from pathlib import Path

        # Add core directory to path for imports
        core_path = Path(__file__).parent.parent
        if str(core_path) not in sys.path:
            sys.path.insert(0, str(core_path))

        from llm.factory import LLMProvider

        provider = LLMProvider()
        llm = provider.get_llm(temperature=0.7)

        if not llm:
            logger.warning("No LLM configured, using mock responses")

        return llm

    async def initialize(self):
        """Initialize the LangGraph workflow"""
        logger.info("Initializing agent workflow...")

        # Build the debate graph
        workflow = StateGraph(AgentState)

        # Add nodes for each agent
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("bull", self._bull_node)
        workflow.add_node("bear", self._bear_node)
        workflow.add_node("analyzer", self._analyzer_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_node("privacy", self._privacy_node)
        workflow.add_node("optimizer", self._optimizer_node)
        workflow.add_node("decide", self._decision_node)

        # Define the flow
        workflow.set_entry_point("researcher")
        workflow.add_edge("researcher", "bull")
        workflow.add_edge("bull", "bear")
        workflow.add_edge("bear", "analyzer")
        workflow.add_edge("analyzer", "risk")
        workflow.add_edge("risk", "privacy")
        workflow.add_edge("privacy", "optimizer")
        workflow.add_edge("optimizer", "decide")

        # Add conditional edge from decide
        workflow.add_conditional_edges(
            "decide",
            self._should_continue,
            {
                "continue": "researcher",  # Loop back for another iteration
                "end": END
            }
        )

        # Compile with memory
        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)

        logger.info("✓ Agent workflow initialized")

    async def _researcher_node(self, state: AgentState) -> AgentState:
        """Research agent node - gathers market intelligence"""
        logger.info(f"🔍 Researcher analyzing {state['symbol']}")

        try:
            research = await self.researcher.research(
                symbol=state["symbol"],
                market_data=state["market_data"]
            )

            return {
                "messages": [{"role": "researcher", "content": research["summary"]}],
                "research_summary": research["summary"],
                "sentiment_score": research.get("sentiment", 0.0)
            }

        except Exception as e:
            logger.error(f"Researcher error: {e}")
            return {
                "messages": [{"role": "researcher", "content": f"Research failed: {e}"}],
                "research_summary": "Unable to complete research"
            }

    async def _bull_node(self, state: AgentState) -> AgentState:
        """Bull agent node - presents bullish case"""
        logger.info(f"🐂 Bull agent arguing for {state['symbol']}")

        prompt = f"""
You are a BULL TRADER arguing why {state['symbol']} should be BOUGHT NOW.

Market Data:
- Current Price: ${state['current_price']}
- Research: {state.get('research_summary', 'N/A')}

Present a STRONG bullish case with:
1. Technical signals favoring long
2. Fundamental catalysts
3. Market momentum indicators
4. Risk/reward ratio

Be aggressive but data-driven. Cite specific metrics.
"""

        try:
            if self.llm:
                response = await self.llm.ainvoke([
                    SystemMessage(content="You are an aggressive bull trader"),
                    HumanMessage(content=prompt)
                ])
                bull_argument = response.content
            else:
                bull_argument = f"BULL: Price trending up, strong momentum indicators for {state['symbol']}"

            return {
                "messages": [{"role": "bull", "content": bull_argument}],
                "bull_argument": bull_argument
            }

        except Exception as e:
            logger.error(f"Bull agent error: {e}")
            return {
                "messages": [{"role": "bull", "content": f"Bull agent failed: {e}"}],
                "bull_argument": "Unable to generate bull case"
            }

    async def _bear_node(self, state: AgentState) -> AgentState:
        """Bear agent node - presents bearish case"""
        logger.info(f"🐻 Bear agent arguing against {state['symbol']}")

        prompt = f"""
You are a BEAR TRADER arguing why {state['symbol']} should be SOLD or AVOIDED.

Market Data:
- Current Price: ${state['current_price']}
- Research: {state.get('research_summary', 'N/A')}
- Bull's Argument: {state.get('bull_argument', 'N/A')}

Present a STRONG bearish case with:
1. Technical signals favoring short/avoid
2. Fundamental risks and red flags
3. Overvaluation indicators
4. Counterarguments to bull case

Be skeptical and risk-focused. Cite specific concerns.
"""

        try:
            if self.llm:
                response = await self.llm.ainvoke([
                    SystemMessage(content="You are a skeptical bear trader focused on risk"),
                    HumanMessage(content=prompt)
                ])
                bear_argument = response.content
            else:
                bear_argument = f"BEAR: High volatility, potential for pullback on {state['symbol']}"

            return {
                "messages": [{"role": "bear", "content": bear_argument}],
                "bear_argument": bear_argument
            }

        except Exception as e:
            logger.error(f"Bear agent error: {e}")
            return {
                "messages": [{"role": "bear", "content": f"Bear agent failed: {e}"}],
                "bear_argument": "Unable to generate bear case"
            }

    async def _analyzer_node(self, state: AgentState) -> AgentState:
        """Analyzer node - technical + sentiment analysis"""
        logger.info(f"📊 Analyzer processing {state['symbol']}")

        try:
            analysis = await self.analyzer.analyze(
                symbol=state["symbol"],
                market_data=state["market_data"],
                bull_case=state.get("bull_argument"),
                bear_case=state.get("bear_argument")
            )

            return {
                "messages": [{"role": "analyzer", "content": analysis["summary"]}],
                "technical_analysis": analysis["summary"],
                "sentiment_score": analysis.get("sentiment", 0.0)
            }

        except Exception as e:
            logger.error(f"Analyzer error: {e}")
            return {
                "messages": [{"role": "analyzer", "content": f"Analysis failed: {e}"}],
                "technical_analysis": "Unable to complete analysis"
            }

    async def _risk_node(self, state: AgentState) -> AgentState:
        """Risk agent node - validates against policies"""
        logger.info(f"🛡️ Risk agent validating {state['symbol']}")

        try:
            risk_assessment = await self.risk_agent.assess(
                symbol=state["symbol"],
                bull_case=state.get("bull_argument"),
                bear_case=state.get("bear_argument"),
                technical=state.get("technical_analysis"),
                risk_profile=self.risk_profile
            )

            return {
                "messages": [{"role": "risk", "content": risk_assessment["summary"]}],
                "risk_assessment": risk_assessment
            }

        except Exception as e:
            logger.error(f"Risk agent error: {e}")
            return {
                "messages": [{"role": "risk", "content": f"Risk check failed: {e}"}],
                "risk_assessment": {"approved": False, "reason": str(e)}
            }

    async def _privacy_node(self, state: AgentState) -> AgentState:
        """Privacy agent node - checks for PII/collusion"""
        logger.info(f"🔒 Privacy agent checking {state['symbol']}")

        try:
            privacy_check = await self.privacy_agent.check(
                messages=state.get("messages", []),
                symbol=state["symbol"]
            )

            return {
                "messages": [{"role": "privacy", "content": privacy_check["summary"]}],
                "compliance_check": privacy_check
            }

        except Exception as e:
            logger.error(f"Privacy agent error: {e}")
            return {
                "messages": [{"role": "privacy", "content": f"Privacy check failed: {e}"}],
                "compliance_check": {"approved": False, "reason": str(e)}
            }

    async def _optimizer_node(self, state: AgentState) -> AgentState:
        """Optimizer node - quantum portfolio optimization"""
        logger.info(f"⚛️ Optimizer calculating optimal action for {state['symbol']}")

        try:
            optimization = await self.optimizer.optimize(
                symbol=state["symbol"],
                bull_score=self._extract_score(state.get("bull_argument", "")),
                bear_score=self._extract_score(state.get("bear_argument", "")),
                risk_assessment=state.get("risk_assessment", {}),
                current_portfolio={}  # TODO: Get from execution module
            )

            return {
                "messages": [{"role": "optimizer", "content": optimization["summary"]}],
                "confidence": optimization.get("confidence", 0.0)
            }

        except Exception as e:
            logger.error(f"Optimizer error: {e}")
            return {
                "messages": [{"role": "optimizer", "content": f"Optimization failed: {e}"}],
                "confidence": 0.0
            }

    async def _decision_node(self, state: AgentState) -> AgentState:
        """Final decision node - synthesizes all agent inputs"""
        logger.info(f"⚖️ Making final decision for {state['symbol']}")

        # Check if risk/compliance approved
        risk_approved = state.get("risk_assessment", {}).get("approved", False)
        compliance_approved = state.get("compliance_check", {}).get("approved", True)

        if not risk_approved or not compliance_approved:
            decision = {
                "action": "hold",
                "reason": "Failed risk or compliance check",
                "confidence": 0.0
            }
        else:
            # Synthesize decision from all agents
            sentiment = state.get("sentiment_score", 0.0)
            confidence = state.get("confidence", 0.0)

            if sentiment > 0.3 and confidence > 0.6:
                action = "buy"
            elif sentiment < -0.3 and confidence > 0.6:
                action = "sell"
            else:
                action = "hold"

            decision = {
                "action": action,
                "symbol": state["symbol"],
                "confidence": confidence,
                "sentiment": sentiment,
                "timestamp": datetime.now().isoformat(),
                "reasoning": {
                    "bull": state.get("bull_argument", "")[:200],
                    "bear": state.get("bear_argument", "")[:200],
                    "technical": state.get("technical_analysis", "")[:200]
                }
            }

        logger.info(f"📊 Decision: {decision['action'].upper()} {state['symbol']} "
                   f"(confidence: {decision.get('confidence', 0):.2%})")

        return {
            "messages": [{"role": "decision", "content": json.dumps(decision)}],
            "final_decision": decision,
            "iteration": state.get("iteration", 0) + 1
        }

    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue iterating or end"""
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 1)
        confidence = state.get("confidence", 0.0)

        # End if max iterations reached or high confidence
        if iteration >= max_iterations or confidence > 0.8:
            return "end"

        return "continue"

    def _extract_score(self, argument: str) -> float:
        """
        Extract numerical score from argument using multiple methods

        Priority:
        1. Explicit score markers (e.g., "Score: 0.8", "Confidence: 75%")
        2. Semantic analysis with negation handling
        3. Fallback word counting
        """
        if not argument:
            return 0.0

        text_lower = argument.lower()

        # Method 1: Look for explicit numeric scores
        import re
        score_patterns = [
            r'score[:\s]+([0-9.]+)',
            r'confidence[:\s]+([0-9.]+)%?',
            r'rating[:\s]+([0-9.]+)',
            r'\b([0-9]\.?[0-9]?)/10\b'
        ]

        for pattern in score_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value = float(match.group(1))
                # Normalize to [-1, 1] range
                if value > 1:
                    value = (value / 100) if value <= 100 else (value / 10)
                return max(-1.0, min(1.0, value))

        # Method 2: Semantic patterns with negation handling
        strong_positive = ['strongly bullish', 'very strong', 'excellent', 'outstanding', 'compelling']
        moderate_positive = ['bullish', 'positive', 'good', 'favorable', 'uptrend', 'support', 'buy', 'growth']
        strong_negative = ['strongly bearish', 'very weak', 'terrible', 'avoid at all costs', 'high risk']
        moderate_negative = ['bearish', 'negative', 'weak', 'unfavorable', 'downtrend', 'resistance', 'sell', 'decline']
        negations = ['not', 'no', 'hardly', 'barely', 'neither', "isn't", "aren't", "won't"]

        # Count with negation awareness
        score = 0.0
        sentences = text_lower.split('.')

        for sentence in sentences:
            words = sentence.split()
            has_negation = any(neg in words for neg in negations)

            # Weight patterns by strength
            if any(phrase in sentence for phrase in strong_positive):
                score += -0.6 if has_negation else 0.6
            elif any(phrase in sentence for phrase in moderate_positive):
                score += -0.3 if has_negation else 0.3
            elif any(phrase in sentence for phrase in strong_negative):
                score += 0.6 if has_negation else -0.6
            elif any(phrase in sentence for phrase in moderate_negative):
                score += 0.3 if has_negation else -0.3

        # Normalize by sentence count
        if sentences:
            score = score / len(sentences)

        return max(-1.0, min(1.0, score))

    async def analyze_symbol(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a symbol using multi-agent debate

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            market_data: Optional market data override

        Returns:
            Decision dict with action, confidence, reasoning
        """
        if not self.app:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")

        # Fetch market data if not provided
        if not market_data:
            market_data = await self.data_module.get_market_data(symbol)

        # Initial state
        initial_state = {
            "messages": [],
            "symbol": symbol,
            "current_price": market_data.get("price", 0.0),
            "market_data": market_data,
            "bull_argument": None,
            "bear_argument": None,
            "research_summary": None,
            "technical_analysis": None,
            "sentiment_score": 0.0,
            "risk_assessment": {},
            "compliance_check": {},
            "final_decision": None,
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": 1
        }

        # Run the workflow
        config = {"configurable": {"thread_id": f"{symbol}_{datetime.now().timestamp()}"}}

        try:
            result = await self.app.ainvoke(initial_state, config)
            return result.get("final_decision", {})

        except Exception as e:
            logger.error(f"Error in analyze_symbol: {e}", exc_info=True)
            return {
                "action": "hold",
                "symbol": symbol,
                "confidence": 0.0,
                "error": str(e)
            }

    async def start(self):
        """Start the orchestrator"""
        self.running = True
        self.paused = False
        logger.info("✓ Orchestrator started")

    async def pause(self):
        """Pause the orchestrator"""
        self.paused = True
        logger.info("⏸️ Orchestrator paused")

    async def resume(self):
        """Resume the orchestrator"""
        self.paused = False
        logger.info("▶️ Orchestrator resumed")

    async def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("🛑 Orchestrator stopped")

    async def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "running": self.running,
            "paused": self.paused,
            "risk_profile": self.risk_profile,
            "agents": {
                "researcher": "active",
                "analyzer": "active",
                "optimizer": "active",
                "risk": "active",
                "privacy": "active"
            }
        }
