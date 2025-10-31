#!/usr/bin/env python3
"""
Database Backup Script
Backs up PostgreSQL database and optionally emails it.

Usage:
    python scripts/backup_db.py --email  # Backup and email
    python scripts/backup_db.py          # Just create backup file
"""
import os
import sys
import subprocess
import gzip
import shutil
from datetime import datetime
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


def backup_sqlite(output_file: Path) -> bool:
    """Backup SQLite database."""
    print(f"📦 Backing up SQLite database...")
    
    db_path = settings.data_dir / "sbv.db"
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Copy and compress
    with open(db_path, 'rb') as f_in:
        with gzip.open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    print(f"✅ SQLite backup created: {output_file}")
    return True


def backup_postgresql(output_file: Path) -> bool:
    """Backup PostgreSQL database using pg_dump."""
    print(f"📦 Backing up PostgreSQL database...")
    
    db_url = os.getenv("DATABASE_URL") or settings.database_url
    
    if "sqlite" in db_url:
        return backup_sqlite(output_file)
    
    db_config = parse_database_url(db_url)
    
    # Set password env var
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]
    
    # Create uncompressed backup first
    temp_file = output_file.with_suffix(".sql")
    
    cmd = [
        "pg_dump",
        "-h", db_config["host"],
        "-p", str(db_config["port"]),
        "-U", db_config["user"],
        "-d", db_config["dbname"],
        "--clean",           # Include DROP statements
        "--if-exists",       # Don't error if objects don't exist
        "--create",          # Include CREATE DATABASE
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
        
        if result.returncode != 0:
            print(f"❌ pg_dump failed: {result.stderr}")
            return False
        
        # Compress the backup
        with open(temp_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        temp_file.unlink()
        
        file_size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"✅ PostgreSQL backup created: {output_file} ({file_size_mb:.2f} MB)")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Backup timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def send_email_backup(backup_file: Path) -> bool:
    """Send backup file via email."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders
    
    print(f"📧 Sending backup to {settings.backup_email}...")
    
    # Get email settings
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    backup_email = os.getenv("BACKUP_EMAIL", "alonof27@gmail.com")
    
    if not smtp_user or not smtp_password:
        print("❌ Email credentials not configured (SMTP_USERNAME, SMTP_PASSWORD)")
        return False
    
    # Check file size (Gmail limit: 25MB)
    file_size_mb = backup_file.stat().st_size / (1024 * 1024)
    if file_size_mb > 24:
        print(f"⚠️  Backup too large ({file_size_mb:.1f} MB). Gmail limit is 25 MB.")
        print("    Consider using GitHub or S3 for large backups.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = backup_email
        msg['Subject'] = f"SBV Database Backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        body = f"""
Automated SBV Database Backup

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
File: {backup_file.name}
Size: {file_size_mb:.2f} MB

This backup was generated automatically by the SBV Pipeline.

To restore:
1. Save the attached file
2. Run: python scripts/restore_db.py <backup_file>

-- 
SBV Analysis Pipeline
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach backup file
        with open(backup_file, 'rb') as f:
            part = MIMEBase('application', 'gzip')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {backup_file.name}'
            )
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Backup emailed successfully to {backup_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        return False


def main():
    """Main backup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup SBV database")
    parser.add_argument("--email", action="store_true", help="Email backup after creation")
    parser.add_argument("--output-dir", default="backups", help="Output directory")
    args = parser.parse_args()
    
    # Create backup directory
    backup_dir = Path(args.output_dir)
    backup_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"sbv_backup_{timestamp}.sql.gz"
    
    print("=" * 60)
    print("🗄️  SBV Database Backup")
    print("=" * 60)
    
    # Create backup
    success = backup_postgresql(backup_file)
    
    if not success:
        print("\n❌ Backup failed!")
        sys.exit(1)
    
    # Email if requested
    if args.email:
        send_email_backup(backup_file)
    
    print("\n" + "=" * 60)
    print("✅ Backup complete!")
    print(f"📁 Location: {backup_file.absolute()}")
    print("=" * 60)
    
    # Cleanup old backups (keep last 7)
    backups = sorted(backup_dir.glob("sbv_backup_*.sql.gz"))
    if len(backups) > 7:
        print("\n🧹 Cleaning up old backups (keeping last 7)...")
        for old_backup in backups[:-7]:
            print(f"   Deleting: {old_backup.name}")
            old_backup.unlink()


if __name__ == "__main__":
    main()

