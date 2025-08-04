#!/usr/bin/env python3
"""
Migration: Add practice_round_count column to settings table

This migration adds the practice_round_count column to the settings table
to support configurable practice session lengths.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import db
import config
from flask import Flask


def run_migration():
    """Add practice_round_count column to settings table"""

    # Create Flask app for database context
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(
                text(
                    """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'settings'
                AND column_name = 'practice_round_count'
            """
                )
            )

            if result.fetchone():
                print("✓ practice_round_count column already exists")
                return True

            # Add the practice_round_count column
            print("Adding practice_round_count column to settings table...")
            db.session.execute(
                text(
                    """
                ALTER TABLE settings
                ADD COLUMN practice_round_count INTEGER NOT NULL DEFAULT 10
            """
                )
            )

            # Update existing settings to have the default value
            print("Setting default values for existing settings...")
            db.session.execute(
                text(
                    """
                UPDATE settings
                SET practice_round_count = 10
                WHERE practice_round_count IS NULL
            """
                )
            )

            db.session.commit()
            print("✓ Successfully added practice_round_count column")
            return True

        except Exception as e:
            print(f"✗ Error adding practice_round_count column: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    print("Running migration: Add practice_round_count column")
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)
