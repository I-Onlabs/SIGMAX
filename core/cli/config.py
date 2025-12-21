"""
SIGMAX CLI - Configuration management.

Stores user configuration in ~/.sigmax/config.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path.home() / ".sigmax"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000",
    "api_key": None,
    "default_risk_profile": "conservative",
    "default_mode": "paper",
    "default_format": "text",
}


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    ensure_config_dir()

    if not CONFIG_FILE.exists():
        # Create default config
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Merge with defaults (for new keys)
            return {**DEFAULT_CONFIG, **config}
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]):
    """Save configuration to file."""
    ensure_config_dir()

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return load_config()


def set_config(key: str, value: Any):
    """Set a configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)


def list_config() -> Dict[str, Any]:
    """List all configuration values."""
    return load_config()


def reset_config():
    """Reset configuration to defaults."""
    save_config(DEFAULT_CONFIG)
