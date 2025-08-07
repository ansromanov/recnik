#!/usr/bin/env python3
"""
Migration: Add sounds_enabled column to settings table

This migration adds the sounds_enabled column to the settings table
to support enabling/disabling practice sounds.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import db
import config
from flask import Flask


def run_migration():
    """Add sounds_enabled column to settings table"""

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
                AND column_name = 'sounds_enabled'
            """
                )
            )

            if result.fetchone():
                print("✓ sounds_enabled column already exists")
                return True

            # Add the sounds_enabled column
            print("Adding sounds_enabled column to settings table...")
            db.session.execute(
                text(
                    """
                ALTER TABLE settings
                ADD COLUMN sounds_enabled BOOLEAN NOT NULL DEFAULT TRUE
            """
                )
            )

            # Update existing settings to have the default value
            print("Setting default values for existing settings...")
            db.session.execute(
                text(
                    """
                UPDATE settings
                SET sounds_enabled = TRUE
                WHERE sounds_enabled IS NULL
            """
                )
            )

            db.session.commit()
            print("✓ Successfully added sounds_enabled column")
            return True

        except Exception as e:
            print(f"✗ Error adding sounds_enabled column: {e}")
            db.session.rollback()
            return False


if __name__ == "__main__":
    print("Running migration: Add sounds_enabled column")
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        sys.exit(1)
