"""
SIGMAX CrewAI Agent System - 17 Specialized Agents
Migrated from LangGraph to CrewAI for enhanced multi-agent orchestration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import os

# Try to import CrewAI
CREWAI_AVAILABLE = False
try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import tool
    CREWAI_AVAILABLE = True
    logger.info("✓ CrewAI framework loaded")
except ImportError as e:
    logger.warning(f"CrewAI not available: {e}")
    # Provide fallback classes
    class Agent:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Task:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Crew:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Process:
        sequential = "sequential"
        hierarchical = "hierarchical"


class SIGMAXCrewAIAgents:
    """
    17-Agent System for SIGMAX Trading Platform

    Agent Categories:
    - Market Intelligence (4 agents)
    - Risk & Compliance (3 agents)
    - Strategy & Execution (4 agents)
    - Advanced Analytics (3 agents)
    - Monitoring & Control (3 agents)
    """

    def __init__(self, llm=None, data_module=None):
        """
        Initialize 17 specialized agents

        Args:
            llm: Language model for agent reasoning
            data_module: Data module for market data access
        """
        self.llm = llm
        self.data_module = data_module
        self.agents = {}
        self.crews = {}

        if CREWAI_AVAILABLE:
            self._initialize_agents()
            self._setup_crews()
            logger.info("✓ 17 CrewAI agents initialized")
        else:
            logger.warning("CrewAI not available, using fallback mode")

    def _initialize_agents(self):
        """Initialize all 17 specialized agents"""

        # ================================================================
        # MARKET INTELLIGENCE (4 agents)
        # ================================================================

        self.agents['market_researcher'] = Agent(
            role='Market Researcher',
            goal='Gather and synthesize comprehensive market intelligence',
            backstory="""You are an expert market researcher with 15 years of experience
            in financial markets. You excel at gathering news, identifying trends,
            and understanding macro-economic factors that drive markets.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['technical_analyst'] = Agent(
            role='Technical Analyst',
            goal='Analyze charts, patterns, and technical indicators',
            backstory="""You are a certified technical analyst (CMT) who specializes
            in chart pattern recognition, trend analysis, and technical indicators.
            You can identify support/resistance levels and predict price movements.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['sentiment_analyst'] = Agent(
            role='Sentiment Analyst',
            goal='Analyze social media sentiment and market psychology',
            backstory="""You are a behavioral finance expert who understands market
            psychology. You analyze social media trends, news sentiment, and crowd
            behavior to gauge market emotions.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['onchain_analyst'] = Agent(
            role='On-Chain Analyst',
            goal='Analyze blockchain metrics and on-chain data',
            backstory="""You are a blockchain data scientist who specializes in
            on-chain analytics. You track wallet movements, exchange flows, and
            network activity to predict market moves.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # ================================================================
        # RISK & COMPLIANCE (3 agents)
        # ================================================================

        self.agents['risk_manager'] = Agent(
            role='Risk Manager',
            goal='Assess and manage trading risks',
            backstory="""You are a quantitative risk manager with expertise in
            Value-at-Risk, position sizing, and drawdown management. You ensure
            trades stay within risk parameters.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['compliance_officer'] = Agent(
            role='Compliance Officer',
            goal='Ensure regulatory compliance and legal requirements',
            backstory="""You are a financial compliance expert who ensures all
            trading activities meet regulatory requirements. You monitor for
            suspicious patterns and maintain audit trails.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['privacy_guard'] = Agent(
            role='Privacy Guard',
            goal='Detect and prevent PII leaks and collusion',
            backstory="""You are a privacy and security expert who monitors for
            personally identifiable information (PII) leaks and detects potential
            market manipulation or collusion patterns.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # ================================================================
        # STRATEGY & EXECUTION (4 agents)
        # ================================================================

        self.agents['strategy_coordinator'] = Agent(
            role='Strategy Coordinator',
            goal='Coordinate overall trading strategy',
            backstory="""You are a senior portfolio manager who coordinates all
            trading activities. You synthesize insights from multiple agents and
            create cohesive trading strategies.""",
            verbose=True,
            allow_delegation=True,  # Can delegate to other agents
            llm=self.llm
        )

        self.agents['portfolio_manager'] = Agent(
            role='Portfolio Manager',
            goal='Optimize portfolio allocation and rebalancing',
            backstory="""You are a quantitative portfolio manager who specializes
            in modern portfolio theory. You optimize asset allocation to maximize
            risk-adjusted returns.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['execution_specialist'] = Agent(
            role='Execution Specialist',
            goal='Execute trades with minimal slippage and optimal routing',
            backstory="""You are an algorithmic trading expert who specializes in
            order execution. You route orders efficiently to minimize slippage
            and transaction costs.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['arbitrage_hunter'] = Agent(
            role='Arbitrage Hunter',
            goal='Identify and execute arbitrage opportunities',
            backstory="""You are an arbitrage specialist who constantly scans
            multiple exchanges for price discrepancies. You identify triangular
            arbitrage, funding rate arbitrage, and cross-exchange opportunities.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # ================================================================
        # ADVANCED ANALYTICS (3 agents)
        # ================================================================

        self.agents['quantum_optimizer'] = Agent(
            role='Quantum Optimizer',
            goal='Apply quantum computing to portfolio optimization',
            backstory="""You are a quantum computing expert who uses VQE and QAOA
            algorithms to solve complex portfolio optimization problems that are
            intractable for classical computers.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['ml_predictor'] = Agent(
            role='ML Predictor',
            goal='Generate machine learning predictions',
            backstory="""You are a machine learning engineer who builds predictive
            models using deep learning, gradient boosting, and ensemble methods.
            You forecast price movements and market regimes.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['rl_agent'] = Agent(
            role='Reinforcement Learning Agent',
            goal='Adapt strategies through reinforcement learning',
            backstory="""You are an RL researcher who trains agents to make optimal
            trading decisions through trial and error. You use PPO, DQN, and other
            RL algorithms to continuously improve strategies.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        # ================================================================
        # MONITORING & CONTROL (3 agents)
        # ================================================================

        self.agents['performance_monitor'] = Agent(
            role='Performance Monitor',
            goal='Track performance metrics and generate alerts',
            backstory="""You are a quantitative analyst who monitors trading
            performance in real-time. You track Sharpe ratio, drawdown, win rate,
            and generate alerts when thresholds are breached.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['safety_enforcer'] = Agent(
            role='Safety Enforcer',
            goal='Enforce safety rules and trigger auto-pause when needed',
            backstory="""You are a risk control specialist who enforces safety
            rules. You monitor for consecutive losses, API errors, and other
            issues that require automatic pause of trading.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

        self.agents['decision_coordinator'] = Agent(
            role='Decision Coordinator',
            goal='Synthesize all agent inputs and make final trading decisions',
            backstory="""You are the chief trading officer who makes final decisions
            based on inputs from all specialized agents. You weigh conflicting
            opinions and ensure decisions align with overall strategy.""",
            verbose=True,
            allow_delegation=True,  # Can query other agents
            llm=self.llm
        )

        logger.info(f"✓ Initialized {len(self.agents)} specialized agents")

    def _setup_crews(self):
        """Setup specialized crews for different workflows"""

        # ================================================================
        # ANALYSIS CREW - Market Analysis
        # ================================================================

        self.crews['analysis'] = {
            'agents': [
                self.agents['market_researcher'],
                self.agents['technical_analyst'],
                self.agents['sentiment_analyst'],
                self.agents['onchain_analyst']
            ],
            'description': 'Market intelligence and analysis'
        }

        # ================================================================
        # RISK CREW - Risk Assessment
        # ================================================================

        self.crews['risk'] = {
            'agents': [
                self.agents['risk_manager'],
                self.agents['compliance_officer'],
                self.agents['privacy_guard']
            ],
            'description': 'Risk management and compliance'
        }

        # ================================================================
        # STRATEGY CREW - Strategy Development
        # ================================================================

        self.crews['strategy'] = {
            'agents': [
                self.agents['strategy_coordinator'],
                self.agents['portfolio_manager'],
                self.agents['arbitrage_hunter']
            ],
            'description': 'Strategy coordination and portfolio management'
        }

        # ================================================================
        # ADVANCED CREW - Advanced Analytics
        # ================================================================

        self.crews['advanced'] = {
            'agents': [
                self.agents['quantum_optimizer'],
                self.agents['ml_predictor'],
                self.agents['rl_agent']
            ],
            'description': 'Advanced analytics and optimization'
        }

        # ================================================================
        # EXECUTION CREW - Trade Execution
        # ================================================================

        self.crews['execution'] = {
            'agents': [
                self.agents['execution_specialist'],
                self.agents['safety_enforcer']
            ],
            'description': 'Trade execution and safety'
        }

        # ================================================================
        # MONITORING CREW - Performance Monitoring
        # ================================================================

        self.crews['monitoring'] = {
            'agents': [
                self.agents['performance_monitor'],
                self.agents['decision_coordinator']
            ],
            'description': 'Performance monitoring and decision making'
        }

        logger.info(f"✓ Configured {len(self.crews)} specialized crews")

    def create_analysis_crew(self, symbol: str, market_data: Dict[str, Any]) -> Optional[Any]:
        """
        Create analysis crew for market intelligence

        Args:
            symbol: Trading symbol
            market_data: Current market data

        Returns:
            Crew object if CrewAI available, None otherwise
        """
        if not CREWAI_AVAILABLE:
            return None

        # Create tasks for analysis crew
        tasks = [
            Task(
                description=f"Research market conditions for {symbol}",
                agent=self.agents['market_researcher'],
                expected_output="Market research summary with key findings"
            ),
            Task(
                description=f"Perform technical analysis on {symbol}",
                agent=self.agents['technical_analyst'],
                expected_output="Technical analysis with indicators and patterns"
            ),
            Task(
                description=f"Analyze sentiment for {symbol}",
                agent=self.agents['sentiment_analyst'],
                expected_output="Sentiment analysis with score"
            ),
            Task(
                description=f"Analyze on-chain metrics for {symbol}",
                agent=self.agents['onchain_analyst'],
                expected_output="On-chain analysis with key metrics"
            )
        ]

        crew = Crew(
            agents=self.crews['analysis']['agents'],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        return crew

    def create_decision_crew(
        self,
        symbol: str,
        analysis_results: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Create decision crew for final trading decision

        Args:
            symbol: Trading symbol
            analysis_results: Results from analysis crew
            risk_assessment: Risk assessment results

        Returns:
            Crew object if CrewAI available, None otherwise
        """
        if not CREWAI_AVAILABLE:
            return None

        tasks = [
            Task(
                description=f"Coordinate strategy for {symbol} based on analysis",
                agent=self.agents['strategy_coordinator'],
                expected_output="Strategic recommendation"
            ),
            Task(
                description=f"Validate risk parameters for {symbol}",
                agent=self.agents['risk_manager'],
                expected_output="Risk validation report"
            ),
            Task(
                description=f"Make final decision for {symbol}",
                agent=self.agents['decision_coordinator'],
                expected_output="Final trading decision with confidence score"
            )
        ]

        crew = Crew(
            agents=[
                self.agents['strategy_coordinator'],
                self.agents['risk_manager'],
                self.agents['decision_coordinator']
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )

        return crew

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """Get specific agent by name"""
        return self.agents.get(agent_name)

    def get_crew(self, crew_name: str) -> Optional[Dict]:
        """Get specific crew configuration"""
        return self.crews.get(crew_name)

    def list_agents(self) -> List[str]:
        """List all available agents"""
        return list(self.agents.keys())

    def list_crews(self) -> List[str]:
        """List all available crews"""
        return list(self.crews.keys())

    def get_status(self) -> Dict[str, Any]:
        """Get status of agent system"""
        return {
            "crewai_available": CREWAI_AVAILABLE,
            "total_agents": len(self.agents),
            "total_crews": len(self.crews),
            "agents": self.list_agents(),
            "crews": list(self.crews.keys())
        }


# Convenience function to create agent system
def create_sigmax_agents(llm=None, data_module=None) -> SIGMAXCrewAIAgents:
    """
    Create SIGMAX 17-agent system

    Args:
        llm: Language model for agents
        data_module: Data module for market access

    Returns:
        Configured agent system
    """
    return SIGMAXCrewAIAgents(llm=llm, data_module=data_module)
