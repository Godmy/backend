#!/usr/bin/env python3
"""
МультиПУЛЬТ CLI Tool
Task: #49 - CLI Tool для Admin Tasks

A comprehensive command-line interface for managing the МультиПУЛЬТ backend.

Features:
- User management (create, assign roles)
- Data seeding
- Database backup and restore
- Configuration validation
- Interactive prompts with colored output

Usage:
    python cli.py --help
    python cli.py create-user --username admin --email admin@example.com
    python cli.py seed-data --dry-run
    python cli.py backup-db --output backup.sql
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from colorama import Fore, Style, init
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from auth.models.user import User
from auth.models.role import Role
from auth.services.user_service import UserService
from core.config import get_settings
from core.database import get_db
from core.init_db import init_database


# ==============================================================================
# CLI Utilities
# ==============================================================================

def success(message: str):
    """Print success message in green"""
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def error(message: str):
    """Print error message in red"""
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def warning(message: str):
    """Print warning message in yellow"""
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def info(message: str):
    """Print info message in cyan"""
    click.echo(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def header(message: str):
    """Print header message"""
    click.echo(f"\n{Fore.BLUE}{'='*80}")
    click.echo(f"{Fore.BLUE}{message.center(80)}")
    click.echo(f"{Fore.BLUE}{'='*80}{Style.RESET_ALL}\n")


# ==============================================================================
# CLI Group
# ==============================================================================

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    МультиПУЛЬТ CLI Tool - Administrative commands for backend management
    """
    pass


# ==============================================================================
# User Management Commands
# ==============================================================================

@cli.command()
@click.option("--username", prompt=True, help="Username for the new user")
@click.option("--email", prompt=True, help="Email address")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password")
@click.option("--role", default="user", help="Role name (default: user)")
@click.option("--verified", is_flag=True, help="Mark email as verified")
def create_user(username: str, email: str, password: str, role: str, verified: bool):
    """Create a new user"""
    header("Creating New User")

    try:
        # Load configuration
        settings = get_settings()

        # Create database session
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            # Check if user already exists
            existing = db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing:
                error(f"User with username '{username}' or email '{email}' already exists")
                return

            # Create user
            from auth.utils.password import hash_password

            user = User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
                is_verified=verified,
                is_active=True
            )
            db.add(user)
            db.flush()

            # Assign role
            role_obj = db.query(Role).filter(Role.name == role).first()
            if not role_obj:
                warning(f"Role '{role}' not found, using default 'user' role")
                role_obj = db.query(Role).filter(Role.name == "user").first()

            if role_obj:
                user.roles.append(role_obj)

            db.commit()

            success(f"User '{username}' created successfully!")
            info(f"  Email: {email}")
            info(f"  Role: {role_obj.name if role_obj else 'None'}")
            info(f"  Verified: {'Yes' if verified else 'No'}")
            info(f"  User ID: {user.id}")

        finally:
            db.close()

    except Exception as e:
        error(f"Failed to create user: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--user-id", type=int, prompt=True, help="User ID")
@click.option("--role", prompt=True, help="Role name to assign")
def assign_role(user_id: int, role: str):
    """Assign a role to a user"""
    header("Assigning Role to User")

    try:
        settings = get_settings()
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                error(f"User with ID {user_id} not found")
                return

            role_obj = db.query(Role).filter(Role.name == role).first()
            if not role_obj:
                error(f"Role '{role}' not found")
                return

            if role_obj in user.roles:
                warning(f"User '{user.username}' already has role '{role}'")
                return

            user.roles.append(role_obj)
            db.commit()

            success(f"Role '{role}' assigned to user '{user.username}'")

        finally:
            db.close()

    except Exception as e:
        error(f"Failed to assign role: {str(e)}")
        sys.exit(1)


# ==============================================================================
# Database Commands
# ==============================================================================

@cli.command()
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def seed_data(dry_run: bool):
    """Seed database with initial data"""
    header("Seeding Database")

    if dry_run:
        warning("DRY RUN MODE - No changes will be made")

    try:
        settings = get_settings()

        if dry_run:
            info("Would create:")
            info("  - 8 languages (English, Russian, Spanish, etc.)")
            info("  - 5 roles (admin, moderator, editor, user, guest)")
            info("  - 5 test users with different roles")
            info("  - ~11,000-15,000 domain concepts")
            info("  - ~200 UI translations")
            success("Dry run completed")
            return

        # Use the existing seed_data.main() function
        from scripts.seed_data import main as seed_main

        info("Starting database seeding...")
        seed_main()

        success("Database seeded successfully!")
        info("Check the database for new records")

    except Exception as e:
        error(f"Failed to seed database: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--output", default=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql", help="Output file path")
def backup_db(output: str):
    """Backup database to SQL file"""
    header("Backing Up Database")

    try:
        settings = get_settings()

        # Use pg_dump for PostgreSQL backup
        command = (
            f"pg_dump -h {settings.DB_HOST} -p {settings.DB_PORT} "
            f"-U {settings.DB_USER} -d {settings.DB_NAME} -F p -f {output}"
        )

        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DB_PASSWORD

        info(f"Creating backup: {output}")

        import subprocess
        result = subprocess.run(command, shell=True, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            success(f"Database backed up to: {output}")

            # Get file size
            size = os.path.getsize(output)
            size_mb = size / (1024 * 1024)
            info(f"Backup size: {size_mb:.2f} MB")
        else:
            error(f"Backup failed: {result.stderr}")
            sys.exit(1)

    except Exception as e:
        error(f"Failed to backup database: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--input", prompt=True, help="Input SQL file path")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def restore_db(input: str, confirm: bool):
    """Restore database from SQL file"""
    header("Restoring Database")

    # Check if file exists
    if not os.path.exists(input):
        error(f"File not found: {input}")
        sys.exit(1)

    # Confirmation prompt
    if not confirm:
        warning("This will REPLACE all data in the database!")
        if not click.confirm("Are you sure you want to continue?"):
            info("Restore cancelled")
            return

    try:
        settings = get_settings()

        # Use psql for PostgreSQL restore
        command = (
            f"psql -h {settings.DB_HOST} -p {settings.DB_PORT} "
            f"-U {settings.DB_USER} -d {settings.DB_NAME} -f {input}"
        )

        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DB_PASSWORD

        info(f"Restoring from: {input}")

        import subprocess
        result = subprocess.run(command, shell=True, env=env, capture_output=True, text=True)

        if result.returncode == 0:
            success("Database restored successfully!")
        else:
            error(f"Restore failed: {result.stderr}")
            sys.exit(1)

    except Exception as e:
        error(f"Failed to restore database: {str(e)}")
        sys.exit(1)


# ==============================================================================
# Configuration Commands
# ==============================================================================

@cli.command()
def validate_config():
    """Validate environment configuration"""
    header("Validating Configuration")

    try:
        settings = get_settings()

        success("Configuration is valid!")
        info(f"Environment: {settings.ENVIRONMENT}")
        info(f"Debug mode: {settings.DEBUG}")
        info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        info(f"Frontend URL: {settings.FRONTEND_URL}")
        info(f"SMTP: {settings.SMTP_HOST}:{settings.SMTP_PORT}")

        # Warnings for production
        if settings.ENVIRONMENT == "production":
            if settings.DEBUG:
                warning("DEBUG is enabled in production!")
            if settings.SEED_DATABASE:
                warning("SEED_DATABASE is enabled in production!")
            if not settings.REDIS_PASSWORD:
                warning("REDIS_PASSWORD is not set!")

    except SystemExit:
        error("Configuration validation failed!")
        info("Check .env file and fix errors")
        sys.exit(1)
    except Exception as e:
        error(f"Failed to validate configuration: {str(e)}")
        sys.exit(1)


@cli.command()
def show_config():
    """Show current configuration (with secrets masked)"""
    header("Current Configuration")

    try:
        settings = get_settings()

        def mask_secret(value: str) -> str:
            """Mask sensitive values"""
            if not value or len(value) < 4:
                return "****"
            return f"{value[:4]}{'*' * (len(value) - 4)}"

        config = {
            "Environment": {
                "ENVIRONMENT": settings.ENVIRONMENT,
                "DEBUG": settings.DEBUG,
                "APP_HOST": settings.APP_HOST,
                "APP_PORT": settings.APP_PORT,
            },
            "Database": {
                "DB_HOST": settings.DB_HOST,
                "DB_PORT": settings.DB_PORT,
                "DB_NAME": settings.DB_NAME,
                "DB_USER": settings.DB_USER,
                "DB_PASSWORD": mask_secret(settings.DB_PASSWORD),
            },
            "Redis": {
                "REDIS_HOST": settings.REDIS_HOST,
                "REDIS_PORT": settings.REDIS_PORT,
                "REDIS_DB": settings.REDIS_DB,
                "REDIS_PASSWORD": mask_secret(settings.REDIS_PASSWORD) if settings.REDIS_PASSWORD else "None",
            },
            "JWT": {
                "JWT_SECRET_KEY": mask_secret(settings.JWT_SECRET_KEY),
                "JWT_ALGORITHM": settings.JWT_ALGORITHM,
                "ACCESS_TOKEN_EXPIRE_MINUTES": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
                "REFRESH_TOKEN_EXPIRE_DAYS": settings.REFRESH_TOKEN_EXPIRE_DAYS,
            },
            "Email": {
                "SMTP_HOST": settings.SMTP_HOST,
                "SMTP_PORT": settings.SMTP_PORT,
                "SMTP_USE_TLS": settings.SMTP_USE_TLS,
                "FROM_EMAIL": settings.FROM_EMAIL,
            },
        }

        # Print formatted config
        click.echo(json.dumps(config, indent=2))

    except Exception as e:
        error(f"Failed to show configuration: {str(e)}")
        sys.exit(1)


# ==============================================================================
# System Commands
# ==============================================================================

@cli.command()
def health_check():
    """Check system health (database, redis)"""
    header("System Health Check")

    try:
        settings = get_settings()

        # Check database
        try:
            engine = create_engine(settings.database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            success("Database: OK")
        except Exception as e:
            error(f"Database: FAILED - {str(e)}")

        # Check Redis
        try:
            import redis
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                socket_connect_timeout=5
            )
            r.ping()
            success("Redis: OK")
        except Exception as e:
            error(f"Redis: FAILED - {str(e)}")

        success("Health check completed")

    except Exception as e:
        error(f"Health check failed: {str(e)}")
        sys.exit(1)


@cli.command()
def stats():
    """Show database statistics"""
    header("Database Statistics")

    try:
        settings = get_settings()
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            # User stats
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            verified_users = db.query(User).filter(User.is_verified == True).count()

            info(f"Users:")
            info(f"  Total: {total_users}")
            info(f"  Active: {active_users}")
            info(f"  Verified: {verified_users}")

            # Role stats
            total_roles = db.query(Role).count()
            info(f"\nRoles:")
            info(f"  Total: {total_roles}")

            # List all roles with user count
            roles = db.query(Role).all()
            for role in roles:
                user_count = len(role.users)
                info(f"  - {role.name}: {user_count} users")

            success("\nStatistics retrieved successfully")

        finally:
            db.close()

    except Exception as e:
        error(f"Failed to retrieve statistics: {str(e)}")
        sys.exit(1)


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    cli()
