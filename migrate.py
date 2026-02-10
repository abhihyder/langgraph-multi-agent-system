#!/usr/bin/env python
"""
Laravel-style migration commands for Multi-Agent AI System.

Commands:
    python migrate.py          - Run pending migrations
    python migrate.py fresh    - Drop all tables and re-run migrations
    python migrate.py rollback - Rollback last migration
    python migrate.py status   - Show migration status
    python migrate.py reset    - Rollback all migrations
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database import engine
from app.models.base import Base

# Import all models to ensure they're registered with Base
from app.models import user, persona, conversation, feedback


def run_command(cmd: list, description: str):
    """Run a shell command and print output."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=project_root)
    if result.returncode != 0:
        print(f"\n❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    print(f"\n✅ {description} completed successfully!\n")


def migrate_fresh():
    """Drop all tables and re-run all migrations (like php artisan migrate:fresh)."""
    print("\n⚠️  WARNING: This will DROP ALL TABLES and data!")
    confirm = input("Are you sure? Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("❌ Aborted.")
        return
    
    # Drop all tables with CASCADE to handle foreign key dependencies
    print("\n🗑️  Dropping all tables...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Drop PGVector tables first (they have foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS memories CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS global_knowledge CASCADE"))
            conn.commit()
    except Exception as e:
        print(f"⚠️  Note: {e}")
    
    # Now drop all remaining tables
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped")
    
    # Reset alembic version
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            conn.commit()
        print("✅ Alembic version table reset")
    except Exception as e:
        print(f"⚠️  Note: {e}")
    
    # Run all migrations
    run_command(
        ["alembic", "upgrade", "head"],
        "Running all migrations"
    )


def migrate():
    """Run pending migrations (like php artisan migrate)."""
    # Check if there are pending migrations
    result = subprocess.run(
        ["alembic", "current"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # Check head version
    head_result = subprocess.run(
        ["alembic", "heads"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    current_version = result.stdout.strip()
    head_version = head_result.stdout.strip().split()[0] if head_result.stdout.strip() else ""
    
    # If current matches head, nothing to migrate
    if current_version and head_version in current_version:
        print("\n" + "="*60)
        print("  ✅ Nothing to migrate")
        print("="*60)
        print(f"\nDatabase is already up to date at revision: {head_version}\n")
        return
    
    run_command(
        ["alembic", "upgrade", "head"],
        "Running pending migrations"
    )


def migrate_rollback():
    """Rollback last migration (like php artisan migrate:rollback)."""
    run_command(
        ["alembic", "downgrade", "-1"],
        "Rolling back last migration"
    )


def migrate_reset():
    """Rollback all migrations (like php artisan migrate:reset)."""
    print("\n⚠️  WARNING: This will rollback ALL migrations!")
    confirm = input("Are you sure? Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("❌ Aborted.")
        return
    
    run_command(
        ["alembic", "downgrade", "base"],
        "Rolling back all migrations"
    )


def migrate_status():
    """Show migration status (like php artisan migrate:status)."""
    print("\n" + "="*60)
    print("  Migration Status")
    print("="*60 + "\n")
    
    subprocess.run(["alembic", "current"], cwd=project_root)
    print()
    subprocess.run(["alembic", "history", "--verbose"], cwd=project_root)


def show_help():
    """Show help message."""
    print(__doc__)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "migrate"
    
    commands = {
        "fresh": migrate_fresh,
        "migrate": migrate,
        "rollback": migrate_rollback,
        "reset": migrate_reset,
        "status": migrate_status,
        "help": show_help,
    }
    
    if command not in commands:
        print(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)
    
    commands[command]()
