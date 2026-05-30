"""
Script to add flag_url column to languages table without using Alembic migrations.
Run this script to update the database schema.
"""

from sqlalchemy import text
from core.platform.db.database import engine
from core.platform.logging.structured_logging import get_logger

logger = get_logger(__name__)


def add_flag_url_column():
    """Add flag_url column to languages table"""
    try:
        with engine.connect() as connection:
            # Check if column already exists
            result = connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='languages' AND column_name='flag_url'
                    """
                )
            )

            if result.fetchone():
                logger.info("Column 'flag_url' already exists in 'languages' table")
                return

            # Add the column
            connection.execute(
                text(
                    """
                    ALTER TABLE languages
                    ADD COLUMN flag_url VARCHAR(255) NULL
                    """
                )
            )

            # Add comment to the column (PostgreSQL syntax)
            connection.execute(
                text(
                    """
                    COMMENT ON COLUMN languages.flag_url IS 'URL флага языка (emoji или изображение)'
                    """
                )
            )
            connection.commit()
            logger.info("Successfully added 'flag_url' column to 'languages' table")

    except Exception as e:
        logger.error(f"Error adding flag_url column: {e}")
        raise


if __name__ == "__main__":
    print("Adding flag_url column to languages table...")
    add_flag_url_column()
    print("Done!")
