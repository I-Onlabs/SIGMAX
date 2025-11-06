"""
Structured logging for SIGMAX.

Uses structlog for structured logging with JSON output.
Includes nanosecond timestamp precision for latency tracking.
"""

import sys
import logging
import structlog
from pathlib import Path
from typing import Optional

from .timing import get_timestamp_ns, format_timestamp


def setup_logging(
    level: str = "INFO",
    log_path: Optional[str] = None,
    json_logs: bool = True
) -> None:
    """
    Setup structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_path: Path to log file (optional)
        json_logs: Use JSON formatting (default True for production)
    """
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper())
    )
    
    # Add timestamp processor
    def add_timestamp(logger, method_name, event_dict):
        event_dict['timestamp_ns'] = get_timestamp_ns()
        event_dict['timestamp'] = format_timestamp(event_dict['timestamp_ns'], include_ns=False)
        return event_dict
    
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        add_timestamp,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON or console renderer
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup file logging if path provided
    if log_path:
        log_dir = Path(log_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "sigmax.log")
        file_handler.setFormatter(
            logging.Formatter('%(message)s')
        )
        logging.root.addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Structured logger
    """
    return structlog.get_logger(name)


class LogLatency:
    """
    Context manager for logging latency.
    
    Example:
        with LogLatency(logger, "process_tick"):
            process_tick(tick)
    """
    
    def __init__(self, logger: structlog.BoundLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_ns = 0
    
    def __enter__(self):
        self.start_ns = get_timestamp_ns()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_ns = get_timestamp_ns()
        latency_us = (end_ns - self.start_ns) / 1000.0
        
        self.logger.debug(
            "operation_latency",
            operation=self.operation,
            latency_us=latency_us,
            start_ns=self.start_ns,
            end_ns=end_ns
        )
        
        return False  # Don't suppress exceptions
