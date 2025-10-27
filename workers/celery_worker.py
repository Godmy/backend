"""
Celery worker entry point

This module starts Celery worker process with proper configuration.
Run with: celery -A workers.celery_worker worker --loglevel=info
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.celery_app import celery_app
from core.structured_logging import setup_logging, get_logger

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Import all task modules to ensure they're registered
import tasks.email_tasks
import tasks.file_tasks
import tasks.periodic_tasks

logger.info("Celery worker starting...")
logger.info(f"Registered tasks: {list(celery_app.tasks.keys())}")

# Export celery_app for Celery CLI
app = celery_app

if __name__ == "__main__":
    logger.info("Starting Celery worker via Python...")
    celery_app.start()
