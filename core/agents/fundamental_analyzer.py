"""
Fundamental Analyzer Agent - Phase 3
Analyzes crypto project fundamentals using on-chain and off-chain metrics

Inspired by Dexter's deep research approach, this agent provides fundamental
analysis for crypto assets including:
- On-chain fundamentals (TVL, revenue, treasury)
- Token economics (supply, distribution, utility)
- Financial ratios (P/F, MC/TVL, P/S)
- Project metrics (GitHub activity, community growth)
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger
import aiohttp
import os
import asyncio


class FundamentalAnalyzer:
    """
    Analyzes cryptocurrency project fundamentals

    Data Sources:
    - DefiLlama (TVL, revenue, fees)
    - CoinGecko (market data, token metrics)
    - Dune Analytics (on-chain metrics)
    - Token Terminal (financial metrics)
    - GitHub API (development activity)
    """

    def __init__(self, llm):
        self.llm = llm
        self.session: Optional[aiohttp.ClientSession] = None

        # API keys (optional)
        self.coingecko_key = os.getenv("COINGECKO_API_KEY", "")
        self.dune_key = os.getenv("DUNE_API_KEY", "")
        self.github_token = os.getenv("GITHUB_TOKEN", "")

        # Protocol mapping (symbol to protocol ID)
        self.protocol_map = {
            'BTC': {'defilama': None, 'github': 'bitcoin/bitcoin'},
            'ETH': {'defillama': 'ethereum', 'github': 'ethereum/go-ethereum'},
            'SOL': {'defillama': 'solana', 'github': 'solana-labs/solana'},
            'AVAX': {'defillama': 'avalanche', 'github': 'ava-labs/avalanchego'},
            'MATIC': {'defillama': 'polygon', 'github': 'maticnetwork/bor'},
            'ARB': {'defillama': 'arbitrum', 'github': 'offchainlabs/arbitrum'},
            'OP': {'defillama': 'optimism', 'github': 'ethereum-optimism/optimism'},
            'UNI': {'defillama': 'uniswap', 'github': 'Uniswap/v3-core'},
            'AAVE': {'defillama': 'aave', 'github': 'aave/aave-v3-core'},
            'LINK': {'defillama': 'chainlink', 'github': 'smartcontractkit/chainlink'},
        }

        logger.info("✓ Fundamental analyzer initialized")

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct fundamental analysis on a crypto asset

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            market_data: Current market data

        Returns:
            Fundamental analysis with metrics and ratios
        """
        logger.info(f"📊 Analyzing fundamentals for {symbol}...")

        # Extract base symbol (BTC from BTC/USDT)
        base_symbol = symbol.split('/')[0]

        try:
            # Gather fundamental data in parallel
            results = await asyncio.gather(
                self._get_onchain_fundamentals(base_symbol),
                self._get_token_economics(base_symbol, market_data),
                self._get_project_metrics(base_symbol),
                self._get_financial_ratios(base_symbol, market_data),
                return_exceptions=True
            )

            onchain, token_econ, project_metrics, fin_ratios = results

            # Calculate fundamental score
            fundamental_score = self._calculate_fundamental_score(
                onchain if not isinstance(onchain, Exception) else {},
                token_econ if not isinstance(token_econ, Exception) else {},
                project_metrics if not isinstance(project_metrics, Exception) else {},
                fin_ratios if not isinstance(fin_ratios, Exception) else {}
            )

            # Generate fundamental summary
            summary = await self._generate_summary(
                symbol=symbol,
                onchain=onchain if not isinstance(onchain, Exception) else {},
                token_econ=token_econ if not isinstance(token_econ, Exception) else {},
                project_metrics=project_metrics if not isinstance(project_metrics, Exception) else {},
                financial_ratios=fin_ratios if not isinstance(fin_ratios, Exception) else {},
                fundamental_score=fundamental_score
            )

            return {
                "summary": summary,
                "fundamental_score": fundamental_score,
                "onchain_fundamentals": onchain if not isinstance(onchain, Exception) else {},
                "token_economics": token_econ if not isinstance(token_econ, Exception) else {},
                "project_metrics": project_metrics if not isinstance(project_metrics, Exception) else {},
                "financial_ratios": fin_ratios if not isinstance(fin_ratios, Exception) else {},
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Fundamental analysis error: {e}")
            return {
                "summary": f"Fundamental analysis failed: {e}",
                "fundamental_score": 0.5,  # Neutral
                "onchain_fundamentals": {},
                "token_economics": {},
                "project_metrics": {},
                "financial_ratios": {},
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _get_onchain_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Get on-chain fundamental metrics
        - TVL (Total Value Locked)
        - Protocol revenue
        - Fees generated
        - Active addresses
        """
        logger.info(f"Fetching on-chain fundamentals for {symbol}")

        protocol_id = self.protocol_map.get(symbol, {}).get('defillama')

        if not protocol_id:
            # For non-DeFi assets like BTC/ETH, use alternative metrics
            return {
                'tvl': None,
                'revenue_24h': None,
                'fees_24h': None,
                'active_addresses': await self._get_active_addresses(symbol),
                'data_source': 'alternative'
            }

        try:
            await self._ensure_session()

            # Get TVL from DefiLlama
            url = f"https://api.llama.fi/protocol/{protocol_id}"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    tvl = data.get('tvl', [{}])[-1].get('totalLiquidityUSD', 0) if data.get('tvl') else 0

                    return {
                        'tvl': tvl,
                        'tvl_change_7d': data.get('change_7d', 0),
                        'tvl_change_30d': data.get('change_1m', 0),
                        'chain_tvls': data.get('chainTvls', {}),
                        'category': data.get('category', 'Unknown'),
                        'data_source': 'defillama'
                    }

        except Exception as e:
            logger.warning(f"DefiLlama error for {symbol}: {e}")

        # Fallback: Mock data for testing
        return self._mock_onchain_fundamentals(symbol)

    async def _get_token_economics(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze token economics
        - Circulating supply
        - Max supply
        - Supply inflation rate
        - Token distribution
        - Utility and use cases
        """
        logger.info(f"Analyzing token economics for {symbol}")

        try:
            await self._ensure_session()

            # Get from CoinGecko
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
            headers = {}
            if self.coingecko_key:
                headers['x-cg-pro-api-key'] = self.coingecko_key

            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    market_cap = data.get('market_data', {}).get('market_cap', {}).get('usd', 0)
                    circulating_supply = data.get('market_data', {}).get('circulating_supply', 0)
                    total_supply = data.get('market_data', {}).get('total_supply', 0)
                    max_supply = data.get('market_data', {}).get('max_supply')

                    # Calculate inflation rate
                    inflation_rate = 0
                    if max_supply and max_supply > 0:
                        inflation_rate = ((max_supply - circulating_supply) / circulating_supply) * 100

                    return {
                        'market_cap': market_cap,
                        'circulating_supply': circulating_supply,
                        'total_supply': total_supply,
                        'max_supply': max_supply,
                        'inflation_rate': inflation_rate,
                        'supply_pct_circulating': (circulating_supply / max_supply * 100) if max_supply else 100,
                        'fully_diluted_valuation': data.get('market_data', {}).get('fully_diluted_valuation', {}).get('usd', 0),
                        'data_source': 'coingecko'
                    }

        except Exception as e:
            logger.warning(f"CoinGecko error for {symbol}: {e}")

        # Fallback: Mock data
        return self._mock_token_economics(symbol, market_data)

    async def _get_project_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get project health metrics
        - GitHub activity (commits, contributors, stars)
        - Community growth (social metrics)
        - Development velocity
        """
        logger.info(f"Fetching project metrics for {symbol}")

        github_repo = self.protocol_map.get(symbol, {}).get('github')

        if not github_repo:
            return {
                'github_stars': None,
                'github_commits_30d': None,
                'github_contributors': None,
                'development_activity_score': None,
                'data_source': 'unavailable'
            }

        try:
            await self._ensure_session()

            # Get GitHub repo stats
            url = f"https://api.github.com/repos/{github_repo}"
            headers = {}
            if self.github_token:
                headers['Authorization'] = f"token {self.github_token}"

            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    # Get commit activity
                    commits_url = f"https://api.github.com/repos/{github_repo}/stats/participation"
                    async with self.session.get(commits_url, headers=headers, timeout=10) as commits_response:
                        commits_30d = 0
                        if commits_response.status == 200:
                            commits_data = await commits_response.json()
                            # Last 4 weeks
                            commits_30d = sum(commits_data.get('all', [])[-4:])

                    # Calculate development activity score (0-100)
                    stars = data.get('stargazers_count', 0)
                    forks = data.get('forks_count', 0)
                    watchers = data.get('watchers_count', 0)

                    # Weighted score
                    dev_score = min(100, (
                        (stars / 1000 * 40) +  # Max 40 points for stars
                        (commits_30d / 100 * 30) +  # Max 30 points for commits
                        (forks / 500 * 20) +  # Max 20 points for forks
                        (watchers / 500 * 10)  # Max 10 points for watchers
                    ))

                    return {
                        'github_stars': stars,
                        'github_forks': forks,
                        'github_watchers': watchers,
                        'github_commits_30d': commits_30d,
                        'last_updated': data.get('updated_at'),
                        'development_activity_score': round(dev_score, 1),
                        'data_source': 'github'
                    }

        except Exception as e:
            logger.warning(f"GitHub error for {symbol}: {e}")

        # Fallback: Mock data
        return self._mock_project_metrics(symbol)

    async def _get_financial_ratios(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate crypto-native financial ratios
        - P/F (Price to Fees)
        - P/S (Price to Sales/Revenue)
        - MC/TVL (Market Cap to TVL)
        - Token velocity
        """
        logger.info(f"Calculating financial ratios for {symbol}")

        # This would typically pull from Token Terminal API
        # For now, use mock calculations
        return self._mock_financial_ratios(symbol, market_data)

    async def _get_active_addresses(self, symbol: str) -> int:
        """Get active addresses for the network"""
        # This would typically use Dune Analytics or similar
        # For now, return mock data
        return {
            'BTC': 1000000,
            'ETH': 500000,
            'SOL': 200000,
        }.get(symbol, 10000)

    def _calculate_fundamental_score(
        self,
        onchain: Dict[str, Any],
        token_econ: Dict[str, Any],
        project: Dict[str, Any],
        ratios: Dict[str, Any]
    ) -> float:
        """
        Calculate aggregate fundamental score (0-1)

        Weighting:
        - On-chain health: 30%
        - Token economics: 25%
        - Project metrics: 25%
        - Financial ratios: 20%
        """
        score = 0.5  # Neutral baseline

        # On-chain health (30%)
        if onchain.get('tvl'):
            tvl_change = onchain.get('tvl_change_7d', 0)
            if tvl_change > 10:
                score += 0.15
            elif tvl_change > 0:
                score += 0.075
            elif tvl_change < -10:
                score -= 0.15
            else:
                score -= 0.075

        # Token economics (25%)
        inflation_rate = token_econ.get('inflation_rate', 0)
        if 0 < inflation_rate < 5:  # Healthy inflation
            score += 0.125
        elif inflation_rate > 20:  # High inflation (bad)
            score -= 0.125

        supply_pct = token_econ.get('supply_pct_circulating', 100)
        if supply_pct > 80:  # Most supply circulating (good)
            score += 0.125
        elif supply_pct < 50:  # Heavy unlocks ahead (risky)
            score -= 0.125

        # Project metrics (25%)
        dev_score = project.get('development_activity_score', 50)
        if dev_score > 75:
            score += 0.125
        elif dev_score > 50:
            score += 0.0625
        elif dev_score < 25:
            score -= 0.125

        commits = project.get('github_commits_30d', 0)
        if commits > 100:
            score += 0.125
        elif commits > 50:
            score += 0.0625
        elif commits < 10:
            score -= 0.125

        # Financial ratios (20%)
        pf_ratio = ratios.get('price_to_fees')
        if pf_ratio and pf_ratio < 50:  # Low P/F is good
            score += 0.10
        elif pf_ratio and pf_ratio > 200:  # High P/F is bad
            score -= 0.10

        mc_tvl = ratios.get('mc_to_tvl')
        if mc_tvl and mc_tvl < 2:  # Low MC/TVL is good
            score += 0.10
        elif mc_tvl and mc_tvl > 10:  # High MC/TVL is bad
            score -= 0.10

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))

    async def _generate_summary(
        self,
        symbol: str,
        onchain: Dict[str, Any],
        token_econ: Dict[str, Any],
        project_metrics: Dict[str, Any],
        financial_ratios: Dict[str, Any],
        fundamental_score: float
    ) -> str:
        """Generate natural language summary of fundamentals"""

        # Build summary components
        parts = [f"Fundamental Analysis for {symbol}:"]

        # On-chain metrics
        if onchain.get('tvl'):
            tvl = onchain['tvl']
            tvl_str = f"${tvl / 1e9:.2f}B" if tvl > 1e9 else f"${tvl / 1e6:.2f}M"
            parts.append(f"TVL: {tvl_str}")

        # Token economics
        if token_econ.get('market_cap'):
            mc = token_econ['market_cap']
            mc_str = f"${mc / 1e9:.2f}B" if mc > 1e9 else f"${mc / 1e6:.2f}M"
            parts.append(f"Market Cap: {mc_str}")

        inflation = token_econ.get('inflation_rate', 0)
        if inflation > 0:
            parts.append(f"Inflation: {inflation:.1f}%")

        # Project metrics
        if project_metrics.get('development_activity_score'):
            dev_score = project_metrics['development_activity_score']
            parts.append(f"Dev Activity: {dev_score:.0f}/100")

        # Overall assessment
        if fundamental_score > 0.7:
            assessment = "Strong fundamentals 📈"
        elif fundamental_score > 0.6:
            assessment = "Solid fundamentals ✓"
        elif fundamental_score > 0.4:
            assessment = "Mixed fundamentals ⚠️"
        else:
            assessment = "Weak fundamentals 📉"

        parts.append(assessment)

        return " | ".join(parts)

    # Mock data methods (fallbacks for when APIs are unavailable)

    def _mock_onchain_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Mock on-chain data for testing"""
        tvls = {
            'ETH': 50e9,  # $50B
            'SOL': 5e9,   # $5B
            'AVAX': 2e9,  # $2B
            'UNI': 4e9,   # $4B
            'AAVE': 6e9,  # $6B
        }
        return {
            'tvl': tvls.get(symbol, 1e9),
            'tvl_change_7d': 5.2,
            'tvl_change_30d': 12.8,
            'data_source': 'mock'
        }

    def _mock_token_economics(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock token economics for testing"""
        price = market_data.get('current_price', 1000)

        supplies = {
            'BTC': {'circ': 19.5e6, 'max': 21e6},
            'ETH': {'circ': 120e6, 'max': None},
            'SOL': {'circ': 400e6, 'max': None},
            'AVAX': {'circ': 350e6, 'max': 720e6},
        }

        supply_data = supplies.get(symbol, {'circ': 1e9, 'max': 2e9})
        circ = supply_data['circ']
        max_supply = supply_data['max']

        return {
            'market_cap': price * circ,
            'circulating_supply': circ,
            'max_supply': max_supply,
            'inflation_rate': ((max_supply - circ) / circ * 100) if max_supply else 0,
            'supply_pct_circulating': (circ / max_supply * 100) if max_supply else 100,
            'data_source': 'mock'
        }

    def _mock_project_metrics(self, symbol: str) -> Dict[str, Any]:
        """Mock project metrics for testing"""
        metrics = {
            'BTC': {'stars': 75000, 'commits': 150, 'score': 95},
            'ETH': {'stars': 45000, 'commits': 200, 'score': 92},
            'SOL': {'stars': 12000, 'commits': 300, 'score': 88},
            'AVAX': {'stars': 5000, 'commits': 80, 'score': 75},
        }

        data = metrics.get(symbol, {'stars': 1000, 'commits': 30, 'score': 60})

        return {
            'github_stars': data['stars'],
            'github_commits_30d': data['commits'],
            'development_activity_score': data['score'],
            'data_source': 'mock'
        }

    def _mock_financial_ratios(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock financial ratios for testing"""
        price = market_data.get('current_price', 1000)

        # Mock P/F and MC/TVL ratios
        ratios = {
            'UNI': {'pf': 45, 'mc_tvl': 1.8},
            'AAVE': {'pf': 35, 'mc_tvl': 1.2},
            'ETH': {'pf': None, 'mc_tvl': None},
            'SOL': {'pf': None, 'mc_tvl': None},
        }

        data = ratios.get(symbol, {'pf': 100, 'mc_tvl': 5.0})

        return {
            'price_to_fees': data['pf'],
            'mc_to_tvl': data['mc_tvl'],
            'data_source': 'mock'
        }
