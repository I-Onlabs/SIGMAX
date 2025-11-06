"""
Database Initialization Script

Initializes Postgres and ClickHouse databases with schema and seed data.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import psycopg2
from clickhouse_driver import Client
from pkg.common import setup_logging, get_logger, load_config


class DatabaseInitializer:
    """Initialize databases"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        
    def init_postgres(self):
        """Initialize Postgres database"""
        self.logger.info("initializing_postgres")
        
        try:
            # Parse connection URL
            # Format: postgresql://user:pass@host:port/database
            url = self.config.database.postgres_url
            
            # Connect to postgres
            conn = psycopg2.connect(url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Read and execute migration
            migration_file = project_root / "db" / "migrations" / "postgres" / "001_init_schema.sql"
            
            if migration_file.exists():
                with open(migration_file, 'r') as f:
                    sql = f.read()
                    cursor.execute(sql)
                
                self.logger.info("postgres_schema_created")
            else:
                self.logger.warning("postgres_migration_not_found", file=str(migration_file))
            
            cursor.close()
            conn.close()
            
            self.logger.info("postgres_initialized")
            
        except Exception as e:
            self.logger.error("postgres_init_error", error=str(e), exc_info=True)
            raise
    
    def init_clickhouse(self):
        """Initialize ClickHouse database"""
        self.logger.info("initializing_clickhouse")
        
        try:
            # Parse connection URL
            # Format: clickhouse://host:port/database
            url = self.config.database.clickhouse_url
            parts = url.replace("clickhouse://", "").split("/")
            host_port = parts[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 9000
            database = parts[1] if len(parts) > 1 else "sigmax"
            
            # Connect to ClickHouse
            client = Client(host=host, port=port)
            
            # Create database
            client.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            
            # Switch to database
            client = Client(host=host, port=port, database=database)
            
            # Read and execute migration
            migration_file = project_root / "db" / "migrations" / "clickhouse" / "001_init_schema.sql"
            
            if migration_file.exists():
                with open(migration_file, 'r') as f:
                    sql = f.read()
                    
                    # Execute each statement separately
                    for statement in sql.split(';'):
                        statement = statement.strip()
                        if statement:
                            try:
                                client.execute(statement)
                            except Exception as e:
                                # Ignore "already exists" errors
                                if "already exists" not in str(e).lower():
                                    raise
                
                self.logger.info("clickhouse_schema_created")
            else:
                self.logger.warning("clickhouse_migration_not_found", file=str(migration_file))
            
            self.logger.info("clickhouse_initialized")
            
        except Exception as e:
            self.logger.error("clickhouse_init_error", error=str(e), exc_info=True)
            raise
    
    def load_symbols(self):
        """Load initial symbols"""
        self.logger.info("loading_symbols")
        
        try:
            url = self.config.database.postgres_url
            conn = psycopg2.connect(url)
            cursor = conn.cursor()
            
            # Check if symbols already loaded
            cursor.execute("SELECT COUNT(*) FROM symbols")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Insert symbols
                symbols = [
                    ('binance', 'BTC', 'USDT', 'BTC/USDT'),
                    ('binance', 'ETH', 'USDT', 'ETH/USDT'),
                    ('binance', 'SOL', 'USDT', 'SOL/USDT'),
                    ('binance', 'BNB', 'USDT', 'BNB/USDT'),
                    ('binance', 'XRP', 'USDT', 'XRP/USDT'),
                ]
                
                for exchange, base, quote, pair in symbols:
                    cursor.execute(
                        "INSERT INTO symbols (exchange, base, quote, pair) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                        (exchange, base, quote, pair)
                    )
                
                conn.commit()
                self.logger.info("symbols_loaded", count=len(symbols))
            else:
                self.logger.info("symbols_already_loaded", count=count)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error("load_symbols_error", error=str(e), exc_info=True)
            raise
    
    def run(self):
        """Run all initialization"""
        self.logger.info("starting_database_initialization")
        
        self.init_postgres()
        self.init_clickhouse()
        self.load_symbols()
        
        self.logger.info("database_initialization_complete")


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="Initialize SIGMAX Databases")
    parser.add_argument("--profile", default="a", choices=["a", "b"])
    parser.add_argument("--config", help="Config file path")
    args = parser.parse_args()
    
    # Load config
    config = load_config(profile=args.profile, config_path=args.config)
    
    # Setup logging
    setup_logging(
        level="INFO",
        log_path=config.observability.log_path,
        json_logs=False
    )
    
    logger = get_logger(__name__)
    logger.info("sigmax_database_init_starting")
    
    # Initialize databases
    try:
        initializer = DatabaseInitializer(config)
        initializer.run()
        logger.info("sigmax_database_init_complete")
    except Exception as e:
        logger.error("database_init_failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
