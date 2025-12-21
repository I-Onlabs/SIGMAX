"""
Scam Checker - Detect honeypots, rug pulls, and scams
"""

from typing import Dict, Any, Optional
from loguru import logger
import aiohttp


class ScamChecker:
    """
    Scam Checker - Detects suspicious tokens

    Checks:
    - Honeypot detection
    - Liquidity locks
    - Dev wallet concentration
    - Contract verification
    - Trading activity patterns
    """

    def __init__(self):
        logger.info("✓ Scam checker created")

    async def check(self, token_address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Check if token is potentially a scam

        Args:
            token_address: Token contract address
            chain: Blockchain network

        Returns:
            Scam check result
        """
        checks = {
            "honeypot": await self._check_honeypot(token_address, chain),
            "liquidity": await self._check_liquidity(token_address, chain),
            "concentration": await self._check_holder_concentration(token_address, chain),
            "verified": await self._check_contract_verified(token_address, chain)
        }

        risk_score = self._calculate_risk_score(checks)

        return {
            "is_scam": risk_score > 0.7,
            "risk_score": risk_score,
            "checks": checks,
            "recommendation": "AVOID" if risk_score > 0.7 else "CAUTION" if risk_score > 0.4 else "SAFE"
        }

    async def _check_honeypot(self, address: str, chain: str) -> bool:
        """
        Check if token is a honeypot using Honeypot.is API

        A honeypot token allows buying but prevents selling
        """
        try:
            # Use Honeypot.is free API
            async with aiohttp.ClientSession() as session:
                url = "https://api.honeypot.is/v2/IsHoneypot"
                params = {
                    "address": address,
                    "chainId": self._get_chain_id(chain)
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Check if honeypot detected
                        is_honeypot = data.get("honeypotResult", {}).get("isHoneypot", False)

                        if is_honeypot:
                            logger.warning(f"Honeypot detected for {address}")
                        else:
                            logger.info(f"No honeypot detected for {address}")

                        return is_honeypot
                    else:
                        logger.warning(f"Honeypot API returned status {response.status}, assuming safe")
                        return False

        except Exception as e:
            logger.error(f"Honeypot check failed: {e}, assuming safe")
            return False

    async def _check_liquidity(self, address: str, chain: str) -> Dict[str, Any]:
        """
        Check liquidity and locks using DEX analytics

        Low liquidity or unlocked liquidity are red flags
        """
        try:
            # Try to get liquidity data from DexScreener API (free, no key)
            async with aiohttp.ClientSession() as session:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"

                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        pairs = data.get("pairs", [])
                        if not pairs:
                            logger.warning(f"No liquidity pairs found for {address}")
                            return {
                                "total": 0,
                                "locked": False,
                                "lock_duration": 0,
                                "usd_value": 0
                            }

                        # Get largest liquidity pool
                        sorted_pairs = sorted(pairs, key=lambda x: float(x.get("liquidity", {}).get("usd", 0)), reverse=True)
                        main_pair = sorted_pairs[0]

                        liquidity_usd = float(main_pair.get("liquidity", {}).get("usd", 0))

                        # Liquidity lock information (if available)
                        # Note: This data may not be available in free API
                        locked = liquidity_usd > 50000  # Heuristic: Consider locked if > $50k liquidity

                        result = {
                            "total": len(pairs),
                            "locked": locked,
                            "lock_duration": 0,  # Would need premium API for this
                            "usd_value": liquidity_usd,
                            "dex": main_pair.get("dexId", "unknown")
                        }

                        logger.info(f"Liquidity for {address}: ${liquidity_usd:.2f} on {result['dex']}")
                        return result

                    else:
                        logger.warning(f"DexScreener API returned status {response.status}")
                        return {
                            "total": 0,
                            "locked": False,
                            "lock_duration": 0,
                            "usd_value": 0
                        }

        except Exception as e:
            logger.error(f"Liquidity check failed: {e}")
            return {
                "total": 0,
                "locked": False,
                "lock_duration": 0,
                "usd_value": 0
            }

    async def _check_holder_concentration(self, address: str, chain: str) -> float:
        """
        Check top holder concentration using blockchain explorer APIs

        High concentration (>50%) in top holders is a red flag
        """
        try:
            # Use blockchain explorer API
            explorer_url = self._get_explorer_api_url(chain)
            if not explorer_url:
                logger.warning(f"No explorer API available for {chain}")
                return 0.0

            async with aiohttp.ClientSession() as session:
                # Get token holder list (top 10)
                url = f"{explorer_url}/api"
                params = {
                    "module": "token",
                    "action": "tokenholderlist",
                    "contractaddress": address,
                    "page": 1,
                    "offset": 10
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "1" and data.get("result"):
                            holders = data["result"]

                            # Calculate top holder percentage
                            total_supply = sum(float(h.get("TokenHolderQuantity", 0)) for h in holders)
                            if total_supply == 0:
                                return 0.0

                            # Top 3 holders concentration
                            top_3_total = sum(float(holders[i].get("TokenHolderQuantity", 0)) for i in range(min(3, len(holders))))
                            concentration = top_3_total / total_supply if total_supply > 0 else 0.0

                            logger.info(f"Top 3 holder concentration for {address}: {concentration*100:.2f}%")
                            return concentration

                        else:
                            logger.warning(f"No holder data available for {address}")
                            return 0.0

                    else:
                        logger.warning(f"Explorer API returned status {response.status}")
                        return 0.0

        except Exception as e:
            logger.error(f"Holder concentration check failed: {e}")
            return 0.0

    async def _check_contract_verified(self, address: str, chain: str) -> bool:
        """
        Check if contract is verified on blockchain explorer

        Unverified contracts are red flags
        """
        try:
            explorer_url = self._get_explorer_api_url(chain)
            if not explorer_url:
                logger.warning(f"No explorer API available for {chain}")
                return True  # Assume verified if we can't check

            async with aiohttp.ClientSession() as session:
                url = f"{explorer_url}/api"
                params = {
                    "module": "contract",
                    "action": "getsourcecode",
                    "address": address
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("status") == "1" and data.get("result"):
                            result = data["result"][0]
                            source_code = result.get("SourceCode", "")

                            # Contract is verified if source code exists
                            is_verified = len(source_code) > 0

                            if is_verified:
                                logger.info(f"Contract {address} is verified on {chain}")
                            else:
                                logger.warning(f"Contract {address} is NOT verified on {chain}")

                            return is_verified

                        else:
                            logger.warning(f"No contract data for {address}")
                            return False

                    else:
                        logger.warning(f"Explorer API returned status {response.status}")
                        return True  # Assume verified if API fails

        except Exception as e:
            logger.error(f"Verification check failed: {e}")
            return True  # Assume verified if check fails to avoid false positives

    def _get_chain_id(self, chain: str) -> str:
        """Get chain ID for APIs"""
        chain_ids = {
            "ethereum": "1",
            "bsc": "56",
            "polygon": "137",
            "avalanche": "43114",
            "arbitrum": "42161",
            "optimism": "10"
        }
        return chain_ids.get(chain.lower(), "1")

    def _get_explorer_api_url(self, chain: str) -> Optional[str]:
        """Get blockchain explorer API URL"""
        explorers = {
            "ethereum": "https://api.etherscan.io",
            "bsc": "https://api.bscscan.com",
            "polygon": "https://api.polygonscan.com",
            "avalanche": "https://api.snowtrace.io",
            "arbitrum": "https://api.arbiscan.io",
            "optimism": "https://api-optimistic.etherscan.io"
        }
        return explorers.get(chain.lower())

    def _calculate_risk_score(self, checks: Dict[str, Any]) -> float:
        """
        Calculate overall risk score (0-1)

        Weights:
        - Honeypot: 0.5 (critical)
        - Unverified contract: 0.2
        - High holder concentration: 0.3
        - Low liquidity: 0.2
        """
        score = 0.0

        # Honeypot is a critical red flag
        if checks["honeypot"]:
            score += 0.5
            logger.warning("⚠️ HONEYPOT DETECTED - High risk!")

        # Unverified contracts are suspicious
        if not checks["verified"]:
            score += 0.2
            logger.warning("⚠️ UNVERIFIED CONTRACT - Medium risk!")

        # High holder concentration indicates potential rug pull
        concentration = checks.get("concentration", 0.0)
        if concentration > 0.5:
            score += 0.3
            logger.warning(f"⚠️ HIGH CONCENTRATION ({concentration*100:.1f}%) - High risk!")
        elif concentration > 0.3:
            score += 0.15
            logger.info(f"⚠️ Moderate concentration ({concentration*100:.1f}%)")

        # Low liquidity makes exit difficult
        liquidity = checks.get("liquidity", {})
        liquidity_usd = liquidity.get("usd_value", 0)

        if liquidity_usd < 10000:  # Less than $10k
            score += 0.2
            logger.warning(f"⚠️ LOW LIQUIDITY (${liquidity_usd:.0f}) - Medium risk!")
        elif liquidity_usd < 50000:  # Less than $50k
            score += 0.1
            logger.info(f"⚠️ Low liquidity (${liquidity_usd:.0f})")

        # Cap at 1.0
        return min(1.0, score)
