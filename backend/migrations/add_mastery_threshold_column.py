#!/usr/bin/env python3
"""
Migration script to add mastery_threshold column to settings table.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text


def add_mastery_threshold_column():
    with app.app_context():
        try:
            # Check if the column already exists
            result = db.session.execute(
                text(
                    """
                SELECT column_name FROM information_schema.columns
                WHERE table_name='settings' AND column_name='mastery_threshold'
            """
                )
            )
            if result.first():
                print("Column 'mastery_threshold' already exists in 'settings'. No action needed.")
                return

            print("Adding 'mastery_threshold' column to 'settings' table...")
            db.session.execute(
                text(
                    "ALTER TABLE settings ADD COLUMN mastery_threshold INTEGER NOT NULL DEFAULT 5;"
                )
            )
            db.session.commit()
            print("Successfully added 'mastery_threshold' column to 'settings'.")
        except Exception as e:
            print(f"Error adding column: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    add_mastery_threshold_column()
