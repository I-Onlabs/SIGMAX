"""
JSONL Logger - Research-friendly decision logging format
Inspired by AI-Trader's unified logging approach

Provides JSONL export alongside PostgreSQL for:
- Reproducible research
- Easy data sharing
- Lightweight backtesting
- Agent training datasets
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
import gzip
import shutil


class JSONLLogger:
    """
    Unified JSONL logging for trading decisions and agent debates.

    Standard format compatible with AI-Trader benchmarking:
    {
        "date": "2024-12-27T10:30:00",
        "symbol": "BTC/USDT",
        "action": "buy",
        "amount": 0.1,
        "reasoning": "...",
        "confidence": 0.85,
        "positions": {...}
    }
    """

    def __init__(
        self,
        base_path: str = "./data/agent_data",
        agent_signature: str = "sigmax",
        compress_old: bool = True,
        max_file_size_mb: int = 100
    ):
        """
        Initialize JSONL Logger.

        Args:
            base_path: Base directory for JSONL files
            agent_signature: Agent identifier for file naming
            compress_old: Whether to compress old log files
            max_file_size_mb: Max size before rotation
        """
        self.base_path = Path(base_path)
        self.agent_signature = agent_signature
        self.compress_old = compress_old
        self.max_file_size_mb = max_file_size_mb

        # Create directory structure
        self.agent_path = self.base_path / agent_signature
        self.position_path = self.agent_path / "position"
        self.log_path = self.agent_path / "log"
        self.debates_path = self.agent_path / "debates"

        for path in [self.position_path, self.log_path, self.debates_path]:
            path.mkdir(parents=True, exist_ok=True)

        # File paths
        self.position_file = self.position_path / "position.jsonl"
        self.decisions_file = self.log_path / "decisions.jsonl"
        self.debates_file = self.debates_path / "debates.jsonl"

        logger.info(f"JSONL Logger initialized: {self.agent_path}")

    def log_decision(
        self,
        symbol: str,
        action: str,
        amount: float,
        price: float,
        confidence: float,
        reasoning: str,
        positions: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log a trading decision in AI-Trader compatible format.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            action: Trade action ("buy", "sell", "hold")
            amount: Trade amount
            price: Execution price
            confidence: Decision confidence (0-1)
            reasoning: Decision reasoning text
            positions: Current positions dict
            metadata: Additional metadata

        Returns:
            The logged record
        """
        record = {
            "date": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "action": action,
            "amount": amount,
            "price": price,
            "confidence": confidence,
            "reasoning": reasoning[:500] if reasoning else "",
            "positions": positions,
            "agent": self.agent_signature
        }

        if metadata:
            record["metadata"] = metadata

        # Append to decisions file
        self._append_jsonl(self.decisions_file, record)

        # Also update position file
        self._log_position(symbol, action, amount, positions)

        logger.debug(f"Logged decision: {symbol} {action} {amount}")
        return record

    def log_debate(
        self,
        symbol: str,
        bull_argument: str,
        bear_argument: str,
        research_summary: str,
        final_decision: str,
        confidence: float,
        agent_scores: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log an agent debate in structured format.

        Args:
            symbol: Trading pair
            bull_argument: Bull agent's argument
            bear_argument: Bear agent's argument
            research_summary: Researcher's summary
            final_decision: Final decision (buy/sell/hold)
            confidence: Decision confidence
            agent_scores: Individual agent scores
            metadata: Additional metadata

        Returns:
            The logged debate record
        """
        record = {
            "date": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "debate": {
                "bull": bull_argument[:1000] if bull_argument else "",
                "bear": bear_argument[:1000] if bear_argument else "",
                "research": research_summary[:1000] if research_summary else ""
            },
            "outcome": {
                "decision": final_decision,
                "confidence": confidence,
                "agent_scores": agent_scores
            },
            "agent": self.agent_signature
        }

        if metadata:
            record["metadata"] = metadata

        self._append_jsonl(self.debates_file, record)

        logger.debug(f"Logged debate for {symbol}: {final_decision}")
        return record

    def _log_position(
        self,
        symbol: str,
        action: str,
        amount: float,
        positions: Dict[str, float]
    ):
        """Log position update."""
        # Get last position ID
        last_id = self._get_last_position_id()

        record = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "id": last_id + 1,
            "this_action": {
                "action": action,
                "symbol": symbol,
                "amount": amount
            },
            "positions": positions
        }

        self._append_jsonl(self.position_file, record)

    def _get_last_position_id(self) -> int:
        """Get the last position ID from file."""
        if not self.position_file.exists():
            return 0

        last_id = 0
        try:
            with open(self.position_file, 'r') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        last_id = record.get("id", last_id)
        except Exception:
            pass

        return last_id

    def _append_jsonl(self, filepath: Path, record: Dict[str, Any]):
        """Append a record to JSONL file with rotation."""
        # Check file size and rotate if needed
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                self._rotate_file(filepath)

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')

    def _rotate_file(self, filepath: Path):
        """Rotate and optionally compress old log file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        rotated_path = filepath.with_suffix(f".{timestamp}.jsonl")

        shutil.move(filepath, rotated_path)

        if self.compress_old:
            with open(rotated_path, 'rb') as f_in:
                with gzip.open(f"{rotated_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            rotated_path.unlink()
            logger.info(f"Rotated and compressed: {rotated_path}.gz")
        else:
            logger.info(f"Rotated: {rotated_path}")

    def get_decisions(
        self,
        symbol: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Read decisions from JSONL file with filtering.

        Args:
            symbol: Filter by symbol
            since: Filter by start date
            until: Filter by end date
            limit: Max records to return

        Returns:
            List of decision records
        """
        decisions = []

        if not self.decisions_file.exists():
            return decisions

        with open(self.decisions_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)

                    # Apply filters
                    if symbol and record.get("symbol") != symbol:
                        continue

                    record_date = datetime.fromisoformat(record["date"].replace('Z', '+00:00'))

                    if since and record_date < since:
                        continue

                    if until and record_date > until:
                        continue

                    decisions.append(record)

                    if len(decisions) >= limit:
                        break

                except json.JSONDecodeError:
                    continue

        return decisions

    def get_positions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Read position history from JSONL file."""
        positions = []

        if not self.position_file.exists():
            return positions

        with open(self.position_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        positions.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return positions[-limit:]

    def get_debates(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Read debate history from JSONL file."""
        debates = []

        if not self.debates_file.exists():
            return debates

        with open(self.debates_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    if symbol and record.get("symbol") != symbol:
                        continue
                    debates.append(record)
                except json.JSONDecodeError:
                    continue

        return debates[-limit:]

    def export_for_research(
        self,
        output_path: str,
        include_debates: bool = True
    ) -> str:
        """
        Export all data in a single research-ready JSONL file.

        Args:
            output_path: Output file path
            include_debates: Whether to include debate records

        Returns:
            Path to exported file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w', encoding='utf-8') as f:
            # Write decisions
            for decision in self.get_decisions(limit=10000):
                decision["record_type"] = "decision"
                f.write(json.dumps(decision, ensure_ascii=False, default=str) + '\n')

            # Write debates if requested
            if include_debates:
                for debate in self.get_debates(limit=10000):
                    debate["record_type"] = "debate"
                    f.write(json.dumps(debate, ensure_ascii=False, default=str) + '\n')

        logger.info(f"Exported research data to: {output}")
        return str(output)

    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            "agent": self.agent_signature,
            "decisions_count": 0,
            "debates_count": 0,
            "positions_count": 0,
            "unique_symbols": set(),
            "date_range": {"start": None, "end": None}
        }

        # Count decisions
        decisions = self.get_decisions(limit=100000)
        stats["decisions_count"] = len(decisions)

        for d in decisions:
            stats["unique_symbols"].add(d.get("symbol"))
            date = d.get("date")
            if date:
                if not stats["date_range"]["start"] or date < stats["date_range"]["start"]:
                    stats["date_range"]["start"] = date
                if not stats["date_range"]["end"] or date > stats["date_range"]["end"]:
                    stats["date_range"]["end"] = date

        stats["unique_symbols"] = list(stats["unique_symbols"])
        stats["debates_count"] = len(self.get_debates(limit=100000))
        stats["positions_count"] = len(self.get_positions(limit=100000))

        return stats
