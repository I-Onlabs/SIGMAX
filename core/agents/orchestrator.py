"""
SIGMAX Multi-Agent Orchestrator using LangGraph
Coordinates bull/bear/researcher debate system
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import json
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
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
from modules.research_safety import ResearchSafety

from .researcher import ResearcherAgent
from .analyzer import AnalyzerAgent
from .optimizer import OptimizerAgent
from .risk import RiskAgent
from .privacy import PrivacyAgent
from .validator import ValidationAgent
from .planner import PlanningAgent, ResearchTask, TaskPriority
from .fundamental_analyzer import FundamentalAnalyzer

# Import task execution system
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from task_queue import TaskExecutor

# Import financial ratios module
from modules.financial_ratios import FinancialRatiosCalculator

# Import decision history
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from decision_history import DecisionHistory

# Import autonomous strategy engine (optional)
try:
    from .finrobot_integration import AutonomousStrategyEngine
    AUTONOMOUS_ENGINE_AVAILABLE = True
except ImportError:
    AUTONOMOUS_ENGINE_AVAILABLE = False
    logger.warning("Autonomous strategy engine not available")


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
    # NEW: Validation fields
    validation_score: float
    validation_passed: bool
    data_gaps: List[str]
    validation_checks: Dict[str, Any]
    research_data: Optional[Dict[str, Any]]
    # NEW: Planning fields (Phase 2)
    research_plan: Optional[Dict[str, Any]]
    planned_tasks: List[Dict[str, Any]]
    completed_task_ids: List[str]
    task_execution_results: Dict[str, Any]
    # NEW: Fundamental analysis fields (Phase 3)
    fundamental_analysis: Optional[Dict[str, Any]]
    fundamental_score: float
    financial_ratios: Optional[Dict[str, Any]]


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
        risk_profile: str = "conservative",
        enable_autonomous_engine: bool = True
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
            enable_autonomous_engine: Enable FinRobot+RD-Agent autonomous strategy evolution
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

        # NEW: Initialize validation agent
        validation_config = {
            'validation_threshold': 0.7,
            'data_freshness_seconds': 300,  # 5 minutes
            'required_data_sources': ['news', 'social', 'onchain', 'technical']
        }
        self.validator = ValidationAgent(self.llm, config=validation_config)

        # NEW: Initialize research safety module
        safety_config = {
            'max_research_iterations': 5,
            'max_api_calls_per_minute': 30,
            'max_llm_cost_per_decision': 0.50,
            'max_daily_research_cost': 10.0,
            'data_freshness_threshold': 300,
            'max_research_time_seconds': 120
        }
        self.research_safety = ResearchSafety(config=safety_config)

        # NEW: Initialize planning agent (Phase 2)
        planning_config = {
            'enable_parallel_tasks': True,
            'max_parallel_tasks': 3,
            'include_optional_tasks': risk_profile != 'aggressive'  # Skip optional for aggressive
        }
        self.planner = PlanningAgent(self.llm, config=planning_config)

        # NEW: Initialize task executor for parallel execution (Phase 2)
        self.task_executor = TaskExecutor(
            max_parallel=planning_config['max_parallel_tasks'],
            retry_failed=True,
            max_retries=2
        )
        # Register task handlers for the researcher
        self._register_task_handlers()

        # NEW: Initialize fundamental analyzer (Phase 3)
        self.fundamental_analyzer = FundamentalAnalyzer(self.llm)
        self.financial_ratios_calc = FinancialRatiosCalculator()
        logger.info("✓ Fundamental analyzer initialized")

        # Initialize autonomous strategy engine (optional)
        self.autonomous_engine = None
        if enable_autonomous_engine and AUTONOMOUS_ENGINE_AVAILABLE:
            try:
                self.autonomous_engine = AutonomousStrategyEngine()
                logger.info("✓ Autonomous strategy engine enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize autonomous engine: {e}")

        # LangGraph workflow
        self.workflow: Optional[StateGraph] = None
        self.app = None

        # State
        self.running = False
        self.paused = False

        # Decision history for explainability
        self.decision_history = DecisionHistory(max_history_per_symbol=20)

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

    def _register_task_handlers(self):
        """
        Register task handlers for parallel execution
        Maps task data sources to execution functions
        """
        # Register handler for news/sentiment tasks
        async def sentiment_handler(task: ResearchTask, context: Dict[str, Any]):
            """Handle sentiment analysis tasks"""
            symbol = context.get('symbol', '')
            news_data = await self.researcher._get_news_sentiment(symbol)
            social_data = await self.researcher._get_social_sentiment(symbol)
            return {
                'news': news_data,
                'social': social_data,
                'sentiment': (news_data.get('score', 0.0) + social_data.get('score', 0.0)) / 2
            }

        # Register handler for on-chain metrics
        async def onchain_handler(task: ResearchTask, context: Dict[str, Any]):
            """Handle on-chain metrics tasks"""
            symbol = context.get('symbol', '')
            market_data = context.get('market_data', {})
            rpc_snapshot = market_data.get('onchain', {})
            try:
                data = await self.researcher._get_onchain_metrics(symbol)
            except Exception as e:
                logger.warning(f"On-chain metrics fallback used: {e}")
                data = {}

            if rpc_snapshot:
                data["rpc_snapshot"] = rpc_snapshot
                data["rpc_source"] = "chain_rpc"

            return data

        # Register handler for technical analysis
        async def technical_handler(task: ResearchTask, context: Dict[str, Any]):
            """Handle technical analysis tasks"""
            # Use existing market data or fetch new
            market_data = context.get('market_data', {})
            return {
                'price': market_data.get('current_price', 0),
                'volume': market_data.get('volume', 0),
                'indicators': market_data.get('indicators', {})
            }

        # Register handler for macro factors
        async def macro_handler(task: ResearchTask, context: Dict[str, Any]):
            """Handle macro factor analysis"""
            return await self.researcher._get_macro_factors()

        # Register handlers with task executor
        self.task_executor.register_handler('news', sentiment_handler)
        self.task_executor.register_handler('social', sentiment_handler)
        self.task_executor.register_handler('fear_greed', sentiment_handler)
        self.task_executor.register_handler('onchain', onchain_handler)
        self.task_executor.register_handler('coingecko', onchain_handler)
        self.task_executor.register_handler('price_data', technical_handler)
        self.task_executor.register_handler('volume_data', technical_handler)
        self.task_executor.register_handler('macro_data', macro_handler)

        logger.info("✓ Task handlers registered for parallel execution")

    async def initialize(self):
        """Initialize the LangGraph workflow"""
        logger.info("Initializing agent workflow...")

        # Build the debate graph
        workflow = StateGraph(AgentState)

        # Add nodes for each agent
        workflow.add_node("planner", self._planner_node)      # NEW: Phase 2
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("validator", self._validator_node)  # NEW: Phase 1
        workflow.add_node("fundamental", self._fundamental_node)  # NEW: Phase 3
        workflow.add_node("bull", self._bull_node)
        workflow.add_node("bear", self._bear_node)
        workflow.add_node("analyzer", self._analyzer_node)
        workflow.add_node("risk", self._risk_node)
        workflow.add_node("privacy", self._privacy_node)
        workflow.add_node("optimizer", self._optimizer_node)
        workflow.add_node("decide", self._decision_node)

        # Define the flow (ENHANCED with planning + validation)
        workflow.set_entry_point("planner")                   # NEW: Phase 2 - Start with planning
        workflow.add_edge("planner", "researcher")            # NEW: Phase 2 - Plan → Research
        workflow.add_edge("researcher", "validator")  # NEW: Validate after research

        # NEW: Conditional edge after validation
        workflow.add_conditional_edges(
            "validator",
            self._validation_router,
            {
                "re_research": "researcher",      # Loop back if validation fails
                "proceed": "fundamental"          # Continue to fundamental analysis
            }
        )

        # NEW: Phase 3 - Fundamental analysis before debate
        workflow.add_edge("fundamental", "bull")

        workflow.add_edge("bull", "bear")
        workflow.add_edge("bear", "analyzer")
        workflow.add_edge("analyzer", "risk")
        workflow.add_edge("risk", "privacy")
        workflow.add_edge("privacy", "optimizer")
        workflow.add_edge("optimizer", "decide")

        # ENHANCED: Conditional edge from decide with validation awareness
        workflow.add_conditional_edges(
            "decide",
            self._should_continue_enhanced,
            {
                "iterate": "researcher",      # Full loop for low confidence
                "refine_research": "researcher",  # Re-research only
                "end": END
            }
        )

        # Compile with memory
        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)

        logger.info("✓ Agent workflow initialized")

    async def _planner_node(self, state: AgentState) -> AgentState:
        """
        NEW: Planner node - creates structured research plan
        Phase 2: Dexter-inspired task decomposition
        """
        logger.info(f"📋 Planning research for {state['symbol']}")

        try:
            # Create research plan
            plan = await self.planner.create_plan(
                symbol=state["symbol"],
                decision_context=state.get("market_data", {}),
                risk_profile=self.risk_profile
            )

            return {
                "messages": [{"role": "planner", "content": plan["summary"]}],
                "research_plan": plan,
                "planned_tasks": plan.get("tasks", []),
                "completed_task_ids": [],
                "task_execution_results": {}
            }

        except Exception as e:
            logger.error(f"Planning error: {e}")
            return {
                "messages": [{"role": "planner", "content": f"Planning failed: {e}"}],
                "research_plan": None,
                "planned_tasks": [],
                "completed_task_ids": [],
                "task_execution_results": {}
            }

    async def _researcher_node(self, state: AgentState) -> AgentState:
        """
        Research agent node - gathers market intelligence
        ENHANCED: Executes planned tasks in parallel if plan exists (Phase 2)
        """
        logger.info(f"🔍 Researcher analyzing {state['symbol']}")

        try:
            # Check if we have a research plan to execute
            research_plan = state.get('research_plan')

            if research_plan and research_plan.get('tasks'):
                # Phase 2: Execute planned tasks in parallel
                logger.info(f"📋 Executing {len(research_plan['tasks'])} planned tasks")

                # Convert task dicts to ResearchTask objects
                tasks = []
                for task_dict in research_plan['tasks']:
                    task = ResearchTask(
                        task_id=task_dict['task_id'],
                        name=task_dict['name'],
                        description=task_dict['description'],
                        priority=TaskPriority(task_dict['priority']),
                        data_sources=task_dict['data_sources'],
                        dependencies=task_dict.get('dependencies', []),
                        estimated_cost=task_dict.get('estimated_cost', 0.0),
                        timeout_seconds=task_dict.get('timeout_seconds', 30)
                    )
                    tasks.append(task)

                # Execute plan with parallel execution
                execution_summary = await self.task_executor.execute_plan(
                    tasks=tasks,
                    execution_order=research_plan['execution_order'],
                    context={
                        'symbol': state['symbol'],
                        'market_data': state.get('market_data', {})
                    }
                )

                # Aggregate results from completed tasks
                task_results = execution_summary.get('task_results', {})
                research_data = {
                    'news': {},
                    'social': {},
                    'onchain': {},
                    'macro': {},
                    'sentiment': 0.0,
                    'timestamp': datetime.now().isoformat()
                }

                # Extract data from task results
                sentiment_scores = []
                for task_id, result in task_results.items():
                    if result.get('status') == 'completed':
                        data = result.get('result', {})
                        if 'news' in data:
                            research_data['news'] = data['news']
                        if 'social' in data:
                            research_data['social'] = data['social']
                        if 'sentiment' in data:
                            sentiment_scores.append(data['sentiment'])
                        # Merge other data types
                        for key in ['onchain', 'macro', 'price', 'volume']:
                            if key in data:
                                research_data[key] = data.get(key, {})

                # Calculate aggregate sentiment
                if sentiment_scores:
                    research_data['sentiment'] = sum(sentiment_scores) / len(sentiment_scores)

                # Generate summary from aggregated results
                summary = f"""Research completed using parallel execution:
- Completed: {execution_summary.get('completed', 0)}/{execution_summary.get('total_tasks', 0)} tasks
- Sentiment: {research_data['sentiment']:.2f}
- Duration: {execution_summary.get('duration_seconds', 0):.1f}s
- Speedup: {research_plan.get('speedup', 1.0):.1f}x
"""

                logger.info(f"✓ Parallel research completed: {execution_summary['completed']}/{execution_summary['total_tasks']} tasks")

                return {
                    "messages": [{"role": "researcher", "content": summary}],
                    "research_summary": summary,
                    "sentiment_score": research_data['sentiment'],
                    "research_data": research_data,
                    "task_execution_results": task_results,
                    "completed_task_ids": list(task_results.keys())
                }

            else:
                # Fallback: Use traditional sequential research (backward compatibility)
                logger.info("📝 Using traditional sequential research (no plan)")
                research = await self.researcher.research(
                    symbol=state["symbol"],
                    market_data=state["market_data"]
                )

                # NEW: Capture full research data for validation
                research_data = {
                    'news': research.get("news", {}),
                    'social': research.get("social", {}),
                    'onchain': research.get("onchain", {}),
                    'macro': research.get("macro", {}),
                    'sentiment': research.get("sentiment", 0.0),
                    'timestamp': research.get("timestamp", datetime.now().isoformat())
                }

                return {
                    "messages": [{"role": "researcher", "content": research["summary"]}],
                    "research_summary": research["summary"],
                    "sentiment_score": research.get("sentiment", 0.0),
                    "research_data": research_data  # NEW: Full data for validation
                }

        except Exception as e:
            logger.error(f"Researcher error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "messages": [{"role": "researcher", "content": f"Research failed: {e}"}],
                "research_summary": "Unable to complete research",
                "research_data": {"error": str(e)}  # NEW: Capture error
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

    async def _validator_node(self, state: AgentState) -> AgentState:
        """
        NEW: Validator node - checks research quality and completeness
        Inspired by Dexter's validation approach
        """
        logger.info(f"✅ Validating research for {state['symbol']}")

        try:
            # Add technical analysis to research data if available
            research_data = state.get("research_data", {})
            if state.get("technical_analysis"):
                research_data["technical"] = {"summary": state["technical_analysis"]}

            validation = await self.validator.validate(
                research_summary=state.get("research_summary"),
                technical_analysis=state.get("technical_analysis"),
                market_data=state.get("market_data"),
                research_data=research_data
            )

            return {
                "messages": [{"role": "validator", "content": validation["summary"]}],
                "validation_score": validation["score"],
                "validation_passed": validation["passed"],
                "data_gaps": validation.get("gaps", []),
                "validation_checks": validation.get("checks", {})
            }

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                "messages": [{"role": "validator", "content": f"Validation failed: {e}"}],
                "validation_score": 0.0,
                "validation_passed": False,
                "data_gaps": [f"Validation error: {str(e)}"],
                "validation_checks": {}
            }

    async def _fundamental_node(self, state: AgentState) -> AgentState:
        """
        NEW: Fundamental analyzer node - analyzes project fundamentals
        Phase 3: Dexter-inspired deep fundamental analysis
        """
        logger.info(f"📊 Analyzing fundamentals for {state['symbol']}")

        try:
            # Perform fundamental analysis
            fundamental_analysis = await self.fundamental_analyzer.analyze(
                symbol=state["symbol"],
                market_data=state.get("market_data", {})
            )

            # Calculate financial ratios
            onchain_data = fundamental_analysis.get("onchain_fundamentals", {})
            token_economics = fundamental_analysis.get("token_economics", {})

            financial_ratios = self.financial_ratios_calc.calculate(
                symbol=state["symbol"].split('/')[0],  # Base symbol
                market_data=state.get("market_data", {}),
                onchain_data=onchain_data,
                fundamental_data=fundamental_analysis
            )

            # Generate summary
            summary = fundamental_analysis.get("summary", "No fundamental data available")
            ratios_summary = self.financial_ratios_calc.generate_summary(
                financial_ratios,
                state["symbol"].split('/')[0]
            )

            combined_summary = f"{summary}\nRatios: {ratios_summary}"

            return {
                "messages": [{"role": "fundamental", "content": combined_summary}],
                "fundamental_analysis": fundamental_analysis,
                "fundamental_score": fundamental_analysis.get("fundamental_score", 0.5),
                "financial_ratios": financial_ratios.to_dict()
            }

        except Exception as e:
            logger.error(f"Fundamental analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "messages": [{"role": "fundamental", "content": f"Fundamental analysis failed: {e}"}],
                "fundamental_analysis": {"error": str(e)},
                "fundamental_score": 0.5,  # Neutral on failure
                "financial_ratios": {}
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
            # Get current portfolio from execution module
            current_portfolio = await self.execution_module.get_portfolio()

            optimization = await self.optimizer.optimize(
                symbol=state["symbol"],
                bull_score=self._extract_score(state.get("bull_argument", "")),
                bear_score=self._extract_score(state.get("bear_argument", "")),
                risk_assessment=state.get("risk_assessment", {}),
                current_portfolio=current_portfolio
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

        # Store decision in history for explainability
        agent_debate = {
            "bull_argument": state.get("bull_argument", ""),
            "bear_argument": state.get("bear_argument", ""),
            "research_summary": state.get("research_summary", ""),
            "technical_analysis": state.get("technical_analysis", "")
        }
        self.decision_history.add_decision(
            symbol=state['symbol'],
            decision=decision,
            agent_debate=agent_debate
        )

        return {
            "messages": [{"role": "decision", "content": json.dumps(decision)}],
            "final_decision": decision,
            "iteration": state.get("iteration", 0) + 1
        }

    def _validation_router(self, state: AgentState) -> str:
        """
        NEW: Route based on validation results
        Implements Dexter-style iterative refinement
        """
        validation_passed = state.get("validation_passed", False)
        data_gaps = state.get("data_gaps", [])
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 3)  # Increased from 1

        # If validation passed OR max iterations reached, proceed
        if validation_passed:
            logger.info("✓ Validation passed - proceeding to debate")
            return "proceed"

        if iteration >= max_iterations:
            logger.warning(f"⚠ Max iterations ({max_iterations}) reached - proceeding anyway")
            return "proceed"

        # If data gaps exist and we have iterations left, re-research
        if data_gaps and iteration < max_iterations:
            logger.info(f"🔄 Data gaps detected ({len(data_gaps)}), re-researching...")
            for i, gap in enumerate(data_gaps[:3], 1):
                logger.info(f"   {i}. {gap}")
            return "re_research"

        # Default: proceed
        return "proceed"

    def _should_continue_enhanced(self, state: AgentState) -> str:
        """
        ENHANCED: Decide whether to continue iterating or end
        Now considers validation scores alongside confidence
        """
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", 3)  # Increased from 1
        confidence = state.get("confidence", 0.0)
        validation_score = state.get("validation_score", 0.0)

        # End conditions
        if iteration >= max_iterations:
            logger.info(f"📊 Max iterations ({max_iterations}) reached - ending")
            return "end"

        # High confidence AND high validation = end
        if confidence > 0.85 and validation_score > 0.8:
            logger.info(f"✅ High confidence ({confidence:.2%}) and quality ({validation_score:.2%}) - ending")
            return "end"

        # Low confidence = full iteration
        if confidence < 0.5:
            logger.info(f"🔄 Low confidence ({confidence:.2%}) - full iteration")
            return "iterate"

        # Low validation score = refine research
        if validation_score < 0.6:
            logger.info(f"🔄 Low validation score ({validation_score:.2%}) - refining research")
            return "refine_research"

        # Moderate confidence and validation = end
        logger.info(f"✓ Moderate confidence ({confidence:.2%}) and quality ({validation_score:.2%}) - ending")
        return "end"

    # Keep old function for backward compatibility
    def _should_continue(self, state: AgentState) -> str:
        """
        DEPRECATED: Use _should_continue_enhanced instead
        Kept for backward compatibility
        """
        return self._should_continue_enhanced(state)

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

        # Initial state (ENHANCED with planning + validation fields)
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
            "max_iterations": 3,  # INCREASED from 1 to 3 for iterative refinement
            # Phase 1: Validation fields
            "validation_score": 0.0,
            "validation_passed": False,
            "data_gaps": [],
            "validation_checks": {},
            "research_data": None,
            # Phase 2: Planning fields
            "research_plan": None,
            "planned_tasks": [],
            "completed_task_ids": [],
            "task_execution_results": {}
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

    async def analyze_symbol_detailed(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a full LangGraph analysis and return the final graph state.

        This is the preferred API for UIs and multi-channel adapters that need
        step artifacts (plan, research, validation, debate, risk, etc.).
        """
        if not self.app:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")

        if not market_data:
            market_data = await self.data_module.get_market_data(symbol)

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
            "max_iterations": 3,
            "validation_score": 0.0,
            "validation_passed": False,
            "data_gaps": [],
            "validation_checks": {},
            "research_data": None,
            "research_plan": None,
            "planned_tasks": [],
            "completed_task_ids": [],
            "task_execution_results": {},
        }

        config = {"configurable": {"thread_id": f"{symbol}_{datetime.now().timestamp()}"}}
        try:
            return await self.app.ainvoke(initial_state, config)
        except Exception as e:
            logger.error(f"Error in analyze_symbol_detailed: {e}", exc_info=True)
            return {
                **initial_state,
                "final_decision": {
                    "action": "hold",
                    "symbol": symbol,
                    "confidence": 0.0,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                },
            }

    async def stream_symbol_analysis(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream LangGraph execution updates as they complete.

        Yields dicts shaped like:
        {"type": "step", "step": "<node>", "update": {...}, "timestamp": "..."}
        and finally:
        {"type": "final", "state": {...}, "timestamp": "..."}
        """
        if not self.app:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")

        if not market_data:
            market_data = await self.data_module.get_market_data(symbol)

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
            "max_iterations": 3,
            "validation_score": 0.0,
            "validation_passed": False,
            "data_gaps": [],
            "validation_checks": {},
            "research_data": None,
            "research_plan": None,
            "planned_tasks": [],
            "completed_task_ids": [],
            "task_execution_results": {},
        }

        config = {"configurable": {"thread_id": f"{symbol}_{datetime.now().timestamp()}"}}

        # Prefer LangGraph streaming updates when available.
        if hasattr(self.app, "astream"):
            final_state: Dict[str, Any] = {}
            async for update in self.app.astream(initial_state, config, stream_mode="updates"):
                # update is typically: {node_name: partial_state_update}
                if isinstance(update, dict):
                    for node_name, partial in update.items():
                        if isinstance(partial, dict):
                            final_state.update(partial)
                        yield {
                            "type": "step",
                            "step": str(node_name),
                            "update": partial,
                            "timestamp": datetime.now().isoformat(),
                        }

            # Best effort final snapshot: run a full invoke if we didn't capture it.
            if not final_state or "final_decision" not in final_state:
                final_state = await self.analyze_symbol_detailed(symbol, market_data=market_data)
            yield {"type": "final", "state": final_state, "timestamp": datetime.now().isoformat()}
            return

        # Fallback: no streaming support
        state = await self.analyze_symbol_detailed(symbol, market_data=market_data)
        yield {"type": "final", "state": state, "timestamp": datetime.now().isoformat()}

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
        """Get orchestrator status (ENHANCED with planning, validation, and safety)"""
        return {
            "running": self.running,
            "paused": self.paused,
            "risk_profile": self.risk_profile,
            "agents": {
                "planner": "active",     # NEW: Phase 2
                "researcher": "active",
                "validator": "active",   # NEW: Phase 1
                "analyzer": "active",
                "optimizer": "active",
                "risk": "active",
                "privacy": "active"
            },
            "autonomous_engine": {
                "enabled": self.autonomous_engine is not None,
                "finrobot": self.autonomous_engine.finrobot.using_finrobot if self.autonomous_engine else False,
                "rdagent": self.autonomous_engine.rdagent.using_rdagent if self.autonomous_engine else False
            },
            # Phase 2: Planning status
            "planning": self.planner.get_config(),
            # Phase 1: Validation status
            "validation": self.validator.get_config(),
            # Phase 1: Research safety status
            "research_safety": self.research_safety.get_safety_status()
        }

    async def analyze_with_autonomous_engine(
        self,
        symbol: str,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced analysis using FinRobot + RD-Agent autonomous engine

        This provides:
        - Advanced market analysis (FinRobot)
        - Risk assessment (FinRobot)
        - Portfolio optimization (FinRobot)
        - Strategy evolution suggestions (RD-Agent)

        Args:
            symbol: Trading symbol
            portfolio: Current portfolio state
            market_data: Market data for analysis

        Returns:
            Enhanced analysis with recommendations
        """
        if not self.autonomous_engine:
            logger.warning("Autonomous engine not enabled, falling back to standard analysis")
            return await self.analyze_symbol(symbol, market_data)

        try:
            # Run autonomous analysis
            result = await self.autonomous_engine.analyze_and_decide(
                symbol=symbol,
                portfolio=portfolio,
                market_data=market_data
            )

            logger.info(f"✓ Autonomous engine analysis complete for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Autonomous engine error: {e}, falling back to standard analysis")
            return await self.analyze_symbol(symbol, market_data)

    async def evolve_strategy(
        self,
        current_strategy: Dict[str, Any],
        performance_history: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evolve trading strategy using RD-Agent

        Args:
            current_strategy: Current strategy configuration
            performance_history: Historical performance metrics
            market_data: Current market conditions

        Returns:
            Evolved strategy with evaluation
        """
        if not self.autonomous_engine:
            logger.warning("Autonomous engine not enabled, cannot evolve strategy")
            return current_strategy

        try:
            result = await self.autonomous_engine.evolve_and_improve(
                current_strategy=current_strategy,
                performance_history=performance_history,
                market_data=market_data
            )

            logger.info(f"✓ Strategy evolved to v{result['evolved_strategy'].get('version', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Strategy evolution error: {e}")
            return {"error": str(e), "strategy": current_strategy}
