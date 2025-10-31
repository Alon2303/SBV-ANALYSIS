#!/usr/bin/env python3
"""
Database Restore Script
Restores PostgreSQL database from backup file.

Usage:
    python scripts/restore_db.py backups/sbv_backup_20241031_120000.sql.gz
"""
import os
import sys
import subprocess
import gzip
import shutil
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sbv-pipeline"))

from src.config import settings


def parse_database_url(url: str) -> dict:
    """Parse DATABASE_URL into components."""
    parsed = urlparse(url)
    return {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": parsed.username,
        "password": parsed.password,
        "dbname": parsed.path[1:] if parsed.path else "postgres"
    }


def restore_sqlite(backup_file: Path) -> bool:
    """Restore SQLite database."""
    print(f"📦 Restoring SQLite database...")
    
    db_path = settings.data_dir / "sbv.db"
    
    # Backup existing database
    if db_path.exists():
        backup_existing = db_path.with_suffix(".db.bak")
        print(f"💾 Backing up existing database to {backup_existing}")
        shutil.copy(db_path, backup_existing)
    
    # Decompress and restore
    with gzip.open(backup_file, 'rb') as f_in:
        with open(db_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    print(f"✅ SQLite database restored: {db_path}")
    return True


def restore_postgresql(backup_file: Path) -> bool:
    """Restore PostgreSQL database using psql."""
    print(f"📦 Restoring PostgreSQL database...")
    
    db_url = os.getenv("DATABASE_URL") or settings.database_url
    
    if "sqlite" in db_url:
        return restore_sqlite(backup_file)
    
    db_config = parse_database_url(db_url)
    
    # Set password env var
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]
    
    # Decompress backup file
    temp_file = backup_file.with_suffix(".sql")
    print(f"🔓 Decompressing backup...")
    
    with gzip.open(backup_file, 'rb') as f_in:
        with open(temp_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    # Confirm restore (dangerous operation!)
    print("\n⚠️  WARNING: This will OVERWRITE the current database!")
    print(f"   Database: {db_config['dbname']} on {db_config['host']}")
    response = input("   Type 'yes' to continue: ")
    
    if response.lower() != 'yes':
        print("❌ Restore cancelled")
        temp_file.unlink()
        return False
    
    # Restore database
    cmd = [
        "psql",
        "-h", db_config["host"],
        "-p", str(db_config["port"]),
        "-U", db_config["user"],
        "-d", "postgres",  # Connect to postgres db first
        "-f", str(temp_file)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        # Remove temp file
        temp_file.unlink()
        
        if result.returncode != 0:
            print(f"❌ Restore failed: {result.stderr}")
            return False
        
        print(f"✅ PostgreSQL database restored successfully")
        return True
        
    except subprocess.TimeoutExpired:
        temp_file.unlink()
        print("❌ Restore timed out after 5 minutes")
        return False
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        print(f"❌ Restore failed: {e}")
        return False


def verify_backup_file(backup_file: Path) -> bool:
    """Verify backup file exists and is valid."""
    if not backup_file.exists():
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    # Check if it's a gzip file
    try:
        with gzip.open(backup_file, 'rb') as f:
            f.read(100)  # Read first 100 bytes
        return True
    except Exception as e:
        print(f"❌ Invalid backup file (not gzip): {e}")
        return False


def main():
    """Main restore function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore SBV database from backup")
    parser.add_argument("backup_file", help="Path to backup file (.sql.gz)")
    args = parser.parse_args()
    
    backup_file = Path(args.backup_file)
    
    print("=" * 60)
    print("🔄 SBV Database Restore")
    print("=" * 60)
    print(f"📁 Backup file: {backup_file}")
    print()
    
    # Verify backup file
    if not verify_backup_file(backup_file):
        sys.exit(1)
    
    file_size_mb = backup_file.stat().st_size / (1024 * 1024)
    print(f"📊 Backup size: {file_size_mb:.2f} MB")
    print()
    
    # Restore
    success = restore_postgresql(backup_file)
    
    if not success:
        print("\n❌ Restore failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Restore complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

