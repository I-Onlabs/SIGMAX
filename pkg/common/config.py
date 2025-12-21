"""
Configuration management for SIGMAX.

Supports:
- YAML configuration files
- Environment variable overrides
- Profile-based configs (A/B)
- Secrets management via SOPS/keyring
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from pathlib import Path


@dataclass
class ExchangeConfig:
    """Exchange-specific configuration"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    rate_limit: int = 1200  # requests per minute
    enable_websocket: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration"""
    postgres_url: str = "postgresql://sigmax:sigmax@localhost:5432/sigmax"
    clickhouse_url: str = "clickhouse://localhost:9000/sigmax"
    use_sqlite: bool = False
    sqlite_path: str = "./data/sigmax.db"


@dataclass
class IPCConfig:
    """Inter-process communication configuration"""
    transport: str = "zmq"  # "zmq" or "aeron"
    zmq_base_port: int = 5555
    aeron_dir: str = "/dev/shm/aeron"


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_usd: float = 10000.0
    max_order_usd: float = 1000.0
    max_leverage: float = 1.0
    price_band_pct: float = 5.0  # Max price deviation from mid
    rate_limit_per_sec: int = 10
    cooldown_ms: int = 100


@dataclass
class DecisionConfig:
    """Decision layer configuration"""
    enabled_layers: List[int] = field(default_factory=lambda: [0, 1, 2])
    enable_ml: bool = True
    enable_llm: bool = False
    llm_provider: str = "anthropic"
    llm_model: str = "claude-3-5-sonnet-20241022"
    llm_temperature: float = 0.1


@dataclass
class ObservabilityConfig:
    """Observability configuration"""
    prometheus_port: int = 9090
    enable_ebpf: bool = False
    log_level: str = "INFO"
    log_path: str = "./logs"


@dataclass
class Config:
    """Main configuration"""
    profile: str = "a"  # "a" or "b"
    environment: str = "development"  # "development", "staging", "production"
    
    exchanges: Dict[str, ExchangeConfig] = field(default_factory=dict)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ipc: IPCConfig = field(default_factory=IPCConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    decision: DecisionConfig = field(default_factory=DecisionConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    
    # Symbols to trade
    symbols: List[str] = field(default_factory=lambda: ["BTC/USDT", "ETH/USDT"])
    
    @classmethod
    def from_yaml(cls, path: str) -> 'Config':
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse exchanges
        exchanges = {}
        for name, ex_config in data.get('exchanges', {}).items():
            exchanges[name] = ExchangeConfig(name=name, **ex_config)
        
        # Parse other sections
        config = cls(
            profile=data.get('profile', 'a'),
            environment=data.get('environment', 'development'),
            exchanges=exchanges,
            database=DatabaseConfig(**data.get('database', {})),
            ipc=IPCConfig(**data.get('ipc', {})),
            risk=RiskConfig(**data.get('risk', {})),
            decision=DecisionConfig(**data.get('decision', {})),
            observability=ObservabilityConfig(**data.get('observability', {})),
            symbols=data.get('symbols', ["BTC/USDT", "ETH/USDT"])
        )
        
        # Override with environment variables
        config._apply_env_overrides()
        
        return config
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Environment
        if env := os.getenv('SIGMAX_ENV'):
            self.environment = env
        
        # Profile
        if profile := os.getenv('SIGMAX_PROFILE'):
            self.profile = profile
        
        # Database
        if db_url := os.getenv('POSTGRES_URL'):
            self.database.postgres_url = db_url
        
        if ch_url := os.getenv('CLICKHOUSE_URL'):
            self.database.clickhouse_url = ch_url
        
        # Exchange API keys (from environment for security)
        for exchange_name in self.exchanges:
            key_var = f'{exchange_name.upper()}_API_KEY'
            secret_var = f'{exchange_name.upper()}_API_SECRET'
            
            if api_key := os.getenv(key_var):
                self.exchanges[exchange_name].api_key = api_key
            
            if api_secret := os.getenv(secret_var):
                self.exchanges[exchange_name].api_secret = api_secret
    
    def get_exchange(self, name: str) -> Optional[ExchangeConfig]:
        """Get exchange configuration by name"""
        return self.exchanges.get(name.lower())
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    def is_profile_a(self) -> bool:
        """Check if using Profile A (simple)"""
        return self.profile.lower() == "a"
    
    def is_profile_b(self) -> bool:
        """Check if using Profile B (performance)"""
        return self.profile.lower() == "b"


def load_config(profile: str = "a", config_path: Optional[str] = None) -> Config:
    """
    Load configuration for the specified profile.
    
    Args:
        profile: Profile to load ("a" or "b")
        config_path: Custom config path (optional)
    
    Returns:
        Loaded configuration
    """
    if config_path is None:
        # Default to profile-specific config
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "profiles" / f"profile_{profile}.yaml"
    
    if not os.path.exists(config_path):
        # Return default config if file doesn't exist
        return Config(profile=profile)
    
    return Config.from_yaml(str(config_path))
