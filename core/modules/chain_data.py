"""
Chain Data Module - Optional on-chain RPC sampling for multi-chain support.

This module is intentionally minimal and only used when CHAINS is configured.
It does not change default behavior and fails safely if not configured.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import asyncio
import json
import os
import time
import urllib.request


@dataclass
class ChainStatus:
    chain: str
    latest_block: Optional[int] = None
    latest_slot: Optional[int] = None
    base_fee_wei: Optional[int] = None
    block_age_sec: Optional[int] = None
    rpc_latency_ms: Optional[float] = None
    timestamp: str = ""


class ChainDataModule:
    """
    On-chain data sampler for configured chains.

    Supported chains:
    - evm (Ethereum-compatible JSON-RPC)
    - solana (Solana JSON-RPC)
    """

    def __init__(self, chains: Optional[List[str]] = None):
        self.chains = [c.lower() for c in (chains or [])]
        self.rpc_endpoints: Dict[str, str] = {
            "evm": os.getenv("CHAIN_RPC_EVM", ""),
            "solana": os.getenv("CHAIN_RPC_SOLANA", "")
        }
        logger.info("✓ Chain data module created")

    async def initialize(self) -> None:
        """Validate chain configuration."""
        if not self.chains:
            logger.info("Chain data module disabled (no CHAINS configured)")
            return

        for chain in self.chains:
            if chain not in self.rpc_endpoints or not self.rpc_endpoints[chain]:
                logger.warning(f"Chain RPC missing for '{chain}'. Set CHAIN_RPC_{chain.upper()}.")
            else:
                logger.info(f"✓ Chain RPC configured: {chain}")

    async def get_onchain_snapshot(self) -> Dict[str, Any]:
        """Get latest chain status for configured chains."""
        if not self.chains:
            return {}

        snapshot: Dict[str, Any] = {}
        for chain in self.chains:
            status = await self.get_chain_status(chain)
            if status:
                snapshot[chain] = status
        return snapshot

    async def get_chain_status(self, chain: str) -> Optional[Dict[str, Any]]:
        """Fetch status for a single chain."""
        chain = chain.lower()
        rpc = self.rpc_endpoints.get(chain)
        if not rpc:
            return None

        if chain == "evm":
            return await self._fetch_evm_status(rpc)
        if chain == "solana":
            return await self._fetch_solana_status(rpc)

        return None

    async def _fetch_evm_status(self, rpc_url: str) -> Optional[Dict[str, Any]]:
        payload = {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": ["latest", False], "id": 1}
        start = time.monotonic()
        try:
            data = await asyncio.to_thread(self._post_json, rpc_url, payload)
            latency_ms = (time.monotonic() - start) * 1000
            block = data.get("result") or {}
            block_hex = block.get("number")
            latest_block = int(block_hex, 16) if block_hex else None
            base_fee_hex = block.get("baseFeePerGas")
            base_fee_wei = int(base_fee_hex, 16) if base_fee_hex else None
            timestamp_hex = block.get("timestamp")
            block_age_sec = None
            if timestamp_hex:
                block_ts = int(timestamp_hex, 16)
                block_age_sec = max(0, int(time.time()) - block_ts)
            status = ChainStatus(
                chain="evm",
                latest_block=latest_block,
                base_fee_wei=base_fee_wei,
                block_age_sec=block_age_sec,
                rpc_latency_ms=latency_ms,
                timestamp=datetime.utcnow().isoformat()
            )
            return status.__dict__
        except Exception as e:
            logger.warning(f"EVM RPC error: {e}")
            return None

    async def _fetch_solana_status(self, rpc_url: str) -> Optional[Dict[str, Any]]:
        payload = {"jsonrpc": "2.0", "method": "getSlot", "params": [], "id": 1}
        start = time.monotonic()
        try:
            data = await asyncio.to_thread(self._post_json, rpc_url, payload)
            latency_ms = (time.monotonic() - start) * 1000
            latest_slot = data.get("result")
            status = ChainStatus(
                chain="solana",
                latest_slot=latest_slot,
                rpc_latency_ms=latency_ms,
                timestamp=datetime.utcnow().isoformat()
            )
            return status.__dict__
        except Exception as e:
            logger.warning(f"Solana RPC error: {e}")
            return None

    def _post_json(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8")
        return json.loads(body) if body else {}
