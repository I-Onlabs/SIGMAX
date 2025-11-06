"""
High-precision timing utilities.

Provides nanosecond-precision timestamps for latency tracking across the pipeline.
Uses time.time_ns() as the base, with future integration for ntpd-rs or PTP.
"""

import time
from datetime import datetime
from typing import Optional


class Clock:
    """
    Centralized clock for the trading system.
    
    All timestamps should use this clock to ensure consistency
    and enable replay/backtesting.
    """
    
    _instance: Optional['Clock'] = None
    _offset_ns: int = 0
    _use_simulated: bool = False
    _simulated_time_ns: int = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_time_ns(cls) -> int:
        """Get current time in nanoseconds"""
        if cls._use_simulated:
            return cls._simulated_time_ns
        return time.time_ns() + cls._offset_ns
    
    @classmethod
    def set_offset(cls, offset_ns: int):
        """Set clock offset (for NTP/PTP sync)"""
        cls._offset_ns = offset_ns
    
    @classmethod
    def enable_simulation(cls, start_time_ns: int):
        """Enable simulated time for replay/backtesting"""
        cls._use_simulated = True
        cls._simulated_time_ns = start_time_ns
    
    @classmethod
    def disable_simulation(cls):
        """Disable simulated time"""
        cls._use_simulated = False
    
    @classmethod
    def advance_time(cls, delta_ns: int):
        """Advance simulated time"""
        if cls._use_simulated:
            cls._simulated_time_ns += delta_ns
    
    @classmethod
    def set_time(cls, time_ns: int):
        """Set simulated time to specific value"""
        if cls._use_simulated:
            cls._simulated_time_ns = time_ns


def get_timestamp_ns() -> int:
    """Get current timestamp in nanoseconds"""
    return Clock.get_time_ns()


def get_timestamp_us() -> int:
    """Get current timestamp in microseconds"""
    return Clock.get_time_ns() // 1000


def get_timestamp_ms() -> int:
    """Get current timestamp in milliseconds"""
    return Clock.get_time_ns() // 1_000_000


def format_timestamp(ts_ns: int, include_ns: bool = True) -> str:
    """
    Format timestamp for human readability.
    
    Args:
        ts_ns: Timestamp in nanoseconds
        include_ns: Include nanosecond precision
    
    Returns:
        Formatted timestamp string
    """
    ts_s = ts_ns / 1_000_000_000
    dt = datetime.fromtimestamp(ts_s)
    
    if include_ns:
        ns = ts_ns % 1_000_000_000
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')}.{ns:09d}"
    else:
        return dt.strftime('%Y-%m-%d %H:%M:%S')


def calculate_latency_ns(start_ns: int, end_ns: int) -> int:
    """Calculate latency in nanoseconds"""
    return end_ns - start_ns


def calculate_latency_us(start_ns: int, end_ns: int) -> float:
    """Calculate latency in microseconds"""
    return (end_ns - start_ns) / 1000.0


def calculate_latency_ms(start_ns: int, end_ns: int) -> float:
    """Calculate latency in milliseconds"""
    return (end_ns - start_ns) / 1_000_000.0


class LatencyTracker:
    """Track latency through pipeline stages"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.checkpoints: dict[str, int] = {}
        self.start_ns = get_timestamp_ns()
    
    def checkpoint(self, stage: str):
        """Record a checkpoint"""
        self.checkpoints[stage] = get_timestamp_ns()
    
    def get_latency_us(self, from_stage: Optional[str] = None, 
                       to_stage: Optional[str] = None) -> float:
        """Get latency between stages in microseconds"""
        start = self.checkpoints.get(from_stage, self.start_ns) if from_stage else self.start_ns
        end = self.checkpoints.get(to_stage, get_timestamp_ns()) if to_stage else get_timestamp_ns()
        return calculate_latency_us(start, end)
    
    def get_all_latencies(self) -> dict[str, float]:
        """Get all stage latencies in microseconds"""
        latencies = {}
        prev_ts = self.start_ns
        prev_name = "start"
        
        for stage, ts in sorted(self.checkpoints.items(), key=lambda x: x[1]):
            latencies[f"{prev_name}→{stage}"] = calculate_latency_us(prev_ts, ts)
            prev_ts = ts
            prev_name = stage
        
        return latencies
    
    def __str__(self) -> str:
        """String representation with all latencies"""
        latencies = self.get_all_latencies()
        lines = [f"LatencyTracker({self.name}):"]
        for stage, lat_us in latencies.items():
            lines.append(f"  {stage}: {lat_us:.2f}µs")
        total_us = self.get_latency_us()
        lines.append(f"  TOTAL: {total_us:.2f}µs")
        return "\n".join(lines)
