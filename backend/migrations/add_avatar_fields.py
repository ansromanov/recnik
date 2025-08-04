#!/usr/bin/env python3
"""
Migration: Add avatar fields to users table
This migration adds avatar_url, avatar_type, and avatar_seed columns to the users table.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to Python path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def run_migration():
    """Add avatar fields to users table"""
    engine = create_engine(config.DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            try:
                print("Adding avatar fields to users table...")

                # Add avatar_url column
                conn.execute(
                    text(
                        """
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)
                """
                    )
                )

                # Add avatar_type column with default value
                conn.execute(
                    text(
                        """
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS avatar_type VARCHAR(20) DEFAULT 'ai_generated'
                """
                    )
                )

                # Add avatar_seed column
                conn.execute(
                    text(
                        """
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS avatar_seed VARCHAR(100)
                """
                    )
                )

                # Commit transaction
                trans.commit()
                print("✓ Successfully added avatar fields to users table")

            except Exception as e:
                trans.rollback()
                raise e

    except SQLAlchemyError as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
