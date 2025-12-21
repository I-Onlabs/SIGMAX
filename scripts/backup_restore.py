#!/usr/bin/env python3
"""
SIGMAX Backup and Restore Script

Handles database backups and restoration for SIGMAX system.
Supports PostgreSQL, Redis, and ClickHouse databases.

Usage:
    # Backup
    python scripts/backup_restore.py backup --all
    python scripts/backup_restore.py backup --postgres
    python scripts/backup_restore.py backup --tag daily

    # Restore
    python scripts/backup_restore.py restore --file backups/sigmax_20251109.tar.gz
    python scripts/backup_restore.py restore --latest --postgres

    # List backups
    python scripts/backup_restore.py list
"""

import argparse
import sys
import subprocess
import tarfile
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class BackupManager:
    """Manages database backups and restoration"""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.project_root = Path(__file__).parent.parent
        self.backup_dir = backup_dir or (self.project_root / "backups")
        self.backup_dir.mkdir(exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        color_codes = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        color = color_codes.get(level, "")
        reset = color_codes["RESET"]
        print(f"{color}[{timestamp}] [{level}] {message}{reset}")

    def run_command(self, cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command"""
        self.log(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if check and result.returncode != 0:
            self.log(f"Command failed: {result.stderr}", "ERROR")
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")

        return result

    def backup_postgres(self, timestamp: str) -> Path:
        """Backup PostgreSQL database"""
        self.log("Backing up PostgreSQL...")

        backup_file = self.backup_dir / f"postgres_{timestamp}.sql"

        try:
            # Create dump inside container
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'pg_dump', '-U', 'sigmax', '-d', 'sigmax',
                '-f', f'/tmp/backup_{timestamp}.sql'
            ])

            # Copy dump out
            self.run_command([
                'docker', 'cp',
                f'sigmax-postgres:/tmp/backup_{timestamp}.sql',
                str(backup_file)
            ])

            # Cleanup temp file in container
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'rm', f'/tmp/backup_{timestamp}.sql'
            ], check=False)

            file_size = backup_file.stat().st_size / (1024 * 1024)
            self.log(f"✓ PostgreSQL backup: {backup_file} ({file_size:.2f} MB)", "SUCCESS")

            return backup_file

        except Exception as e:
            self.log(f"PostgreSQL backup failed: {e}", "ERROR")
            raise

    def backup_redis(self, timestamp: str) -> Path:
        """Backup Redis database"""
        self.log("Backing up Redis...")

        backup_file = self.backup_dir / f"redis_{timestamp}.rdb"

        try:
            # Trigger Redis save
            self.run_command([
                'docker', 'exec', 'sigmax-redis',
                'redis-cli', 'SAVE'
            ])

            # Copy RDB file out
            self.run_command([
                'docker', 'cp',
                'sigmax-redis:/data/dump.rdb',
                str(backup_file)
            ])

            file_size = backup_file.stat().st_size / (1024 * 1024)
            self.log(f"✓ Redis backup: {backup_file} ({file_size:.2f} MB)", "SUCCESS")

            return backup_file

        except Exception as e:
            self.log(f"Redis backup failed: {e}", "ERROR")
            raise

    def backup_clickhouse(self, timestamp: str) -> Path:
        """Backup ClickHouse database"""
        self.log("Backing up ClickHouse...")

        backup_file = self.backup_dir / f"clickhouse_{timestamp}.sql"

        try:
            # Create backup
            result = self.run_command([
                'docker', 'exec', 'sigmax-clickhouse',
                'clickhouse-client',
                '--query', 'SHOW CREATE DATABASE sigmax'
            ])

            with open(backup_file, 'w') as f:
                f.write(result.stdout)

                # Get all tables
                result = self.run_command([
                    'docker', 'exec', 'sigmax-clickhouse',
                    'clickhouse-client',
                    '--query', 'SHOW TABLES FROM sigmax'
                ])

                tables = result.stdout.strip().split('\n')

                for table in tables:
                    if table:
                        # Table schema
                        result = self.run_command([
                            'docker', 'exec', 'sigmax-clickhouse',
                            'clickhouse-client',
                            '--query', f'SHOW CREATE TABLE sigmax.{table}'
                        ])
                        f.write(f"\n-- Table: {table}\n")
                        f.write(result.stdout)

            file_size = backup_file.stat().st_size / 1024
            self.log(f"✓ ClickHouse backup: {backup_file} ({file_size:.2f} KB)", "SUCCESS")

            return backup_file

        except Exception as e:
            self.log(f"ClickHouse backup failed: {e}", "ERROR")
            raise

    def create_archive(self, files: List[Path], timestamp: str, tag: Optional[str] = None) -> Path:
        """Create compressed archive of backup files"""
        self.log("Creating backup archive...")

        tag_str = f"_{tag}" if tag else ""
        archive_name = f"sigmax_backup_{timestamp}{tag_str}.tar.gz"
        archive_path = self.backup_dir / archive_name

        with tarfile.open(archive_path, 'w:gz') as tar:
            for file in files:
                if file.exists():
                    tar.add(file, arcname=file.name)
                    self.log(f"  Added: {file.name}")

        # Remove individual files
        for file in files:
            if file.exists():
                file.unlink()

        file_size = archive_path.stat().st_size / (1024 * 1024)
        self.log(f"✓ Backup archive: {archive_path} ({file_size:.2f} MB)", "SUCCESS")

        return archive_path

    def backup_all(self, tag: Optional[str] = None):
        """Create full backup of all databases"""
        self.log("\n" + "="*70)
        self.log("Starting SIGMAX Full Backup")
        self.log("="*70 + "\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_files = []

        try:
            # Backup each database
            backup_files.append(self.backup_postgres(timestamp))
            backup_files.append(self.backup_redis(timestamp))
            backup_files.append(self.backup_clickhouse(timestamp))

            # Create archive
            archive = self.create_archive(backup_files, timestamp, tag)

            self.log("\n" + "="*70)
            self.log("Backup completed successfully!", "SUCCESS")
            self.log(f"Archive: {archive}")
            self.log("="*70 + "\n")

            return archive

        except Exception as e:
            self.log(f"Backup failed: {e}", "ERROR")
            raise

    def restore_postgres(self, backup_file: Path):
        """Restore PostgreSQL database"""
        self.log(f"Restoring PostgreSQL from {backup_file}...")

        try:
            # Copy file into container
            self.run_command([
                'docker', 'cp',
                str(backup_file),
                'sigmax-postgres:/tmp/restore.sql'
            ])

            # Drop existing database
            self.log("  Dropping existing database...")
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'psql', '-U', 'sigmax', '-d', 'postgres',
                '-c', 'DROP DATABASE IF EXISTS sigmax'
            ])

            # Recreate database
            self.log("  Creating fresh database...")
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'psql', '-U', 'sigmax', '-d', 'postgres',
                '-c', 'CREATE DATABASE sigmax'
            ])

            # Restore dump
            self.log("  Restoring data...")
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'psql', '-U', 'sigmax', '-d', 'sigmax',
                '-f', '/tmp/restore.sql'
            ])

            # Cleanup
            self.run_command([
                'docker', 'exec', 'sigmax-postgres',
                'rm', '/tmp/restore.sql'
            ], check=False)

            self.log("✓ PostgreSQL restored successfully", "SUCCESS")

        except Exception as e:
            self.log(f"PostgreSQL restore failed: {e}", "ERROR")
            raise

    def restore_redis(self, backup_file: Path):
        """Restore Redis database"""
        self.log(f"Restoring Redis from {backup_file}...")

        try:
            # Stop Redis
            self.log("  Stopping Redis...")
            self.run_command(['docker', 'stop', 'sigmax-redis'])

            # Copy backup file
            self.log("  Copying backup...")
            self.run_command([
                'docker', 'cp',
                str(backup_file),
                'sigmax-redis:/data/dump.rdb'
            ])

            # Start Redis
            self.log("  Starting Redis...")
            self.run_command(['docker', 'start', 'sigmax-redis'])

            # Wait for Redis to be ready
            time.sleep(2)

            self.log("✓ Redis restored successfully", "SUCCESS")

        except Exception as e:
            self.log(f"Redis restore failed: {e}", "ERROR")
            raise

    def restore_clickhouse(self, backup_file: Path):
        """Restore ClickHouse database"""
        self.log(f"Restoring ClickHouse from {backup_file}...")

        try:
            # Copy file into container
            self.run_command([
                'docker', 'cp',
                str(backup_file),
                'sigmax-clickhouse:/tmp/restore.sql'
            ])

            # Execute restore
            self.log("  Restoring schema...")
            self.run_command([
                'docker', 'exec', 'sigmax-clickhouse',
                'clickhouse-client',
                '--queries-file', '/tmp/restore.sql'
            ])

            # Cleanup
            self.run_command([
                'docker', 'exec', 'sigmax-clickhouse',
                'rm', '/tmp/restore.sql'
            ], check=False)

            self.log("✓ ClickHouse restored successfully", "SUCCESS")

        except Exception as e:
            self.log(f"ClickHouse restore failed: {e}", "ERROR")
            raise

    def restore_from_archive(self, archive_path: Path):
        """Restore from backup archive"""
        self.log("\n" + "="*70)
        self.log("Starting SIGMAX Restore")
        self.log("="*70 + "\n")

        self.log(f"Archive: {archive_path}")

        try:
            # Extract archive
            self.log("Extracting archive...")
            extract_dir = self.backup_dir / "temp_restore"
            extract_dir.mkdir(exist_ok=True)

            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_dir)

            # Find backup files
            postgres_file = next(extract_dir.glob("postgres_*.sql"), None)
            redis_file = next(extract_dir.glob("redis_*.rdb"), None)
            clickhouse_file = next(extract_dir.glob("clickhouse_*.sql"), None)

            # Restore each database
            if postgres_file:
                self.restore_postgres(postgres_file)

            if redis_file:
                self.restore_redis(redis_file)

            if clickhouse_file:
                self.restore_clickhouse(clickhouse_file)

            # Cleanup
            import shutil
            shutil.rmtree(extract_dir)

            self.log("\n" + "="*70)
            self.log("Restore completed successfully!", "SUCCESS")
            self.log("="*70 + "\n")

        except Exception as e:
            self.log(f"Restore failed: {e}", "ERROR")
            raise

    def list_backups(self):
        """List all available backups"""
        self.log("Available backups:\n")

        backups = sorted(self.backup_dir.glob("sigmax_backup_*.tar.gz"), reverse=True)

        if not backups:
            self.log("No backups found", "WARNING")
            return

        for backup in backups:
            size = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {backup.name}")
            print(f"    Size: {size:.2f} MB")
            print(f"    Date: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="SIGMAX Backup and Restore Script"
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    backup_parser.add_argument('--all', action='store_true', help='Backup all databases')
    backup_parser.add_argument('--postgres', action='store_true', help='Backup PostgreSQL only')
    backup_parser.add_argument('--redis', action='store_true', help='Backup Redis only')
    backup_parser.add_argument('--clickhouse', action='store_true', help='Backup ClickHouse only')
    backup_parser.add_argument('--tag', type=str, help='Tag for backup (e.g., daily, pre-deploy)')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('--file', type=str, help='Backup file to restore')
    restore_parser.add_argument('--latest', action='store_true', help='Restore from latest backup')

    # List command
    subparsers.add_parser('list', help='List available backups')

    args = parser.parse_args()

    manager = BackupManager()

    if args.command == 'backup':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if args.all or (not args.postgres and not args.redis and not args.clickhouse):
            manager.backup_all(tag=args.tag)
        else:
            files = []
            if args.postgres:
                files.append(manager.backup_postgres(timestamp))
            if args.redis:
                files.append(manager.backup_redis(timestamp))
            if args.clickhouse:
                files.append(manager.backup_clickhouse(timestamp))

            if files:
                manager.create_archive(files, timestamp, args.tag)

    elif args.command == 'restore':
        if args.latest:
            backups = sorted(manager.backup_dir.glob("sigmax_backup_*.tar.gz"), reverse=True)
            if backups:
                manager.restore_from_archive(backups[0])
            else:
                manager.log("No backups found", "ERROR")
                sys.exit(1)
        elif args.file:
            backup_path = Path(args.file)
            if not backup_path.exists():
                manager.log(f"Backup file not found: {backup_path}", "ERROR")
                sys.exit(1)
            manager.restore_from_archive(backup_path)
        else:
            parser.error("Must specify --file or --latest")

    elif args.command == 'list':
        manager.list_backups()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
