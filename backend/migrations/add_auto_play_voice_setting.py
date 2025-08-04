#!/usr/bin/env python3
"""
Migration: Add auto_play_voice column to settings table
This migration adds the auto_play_voice boolean field to the settings table
with a default value of True.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Settings
from app import app


def upgrade():
    """Add auto_play_voice column to settings table"""
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col["name"] for col in inspector.get_columns("settings")]

            if "auto_play_voice" not in columns:
                print("Adding auto_play_voice column to settings table...")

                # Add the column with default value True
                with db.engine.connect() as connection:
                    connection.execute(
                        db.text(
                            """
                        ALTER TABLE settings
                        ADD COLUMN auto_play_voice BOOLEAN NOT NULL DEFAULT TRUE
                    """
                        )
                    )
                    connection.commit()

                print("✅ Successfully added auto_play_voice column")
            else:
                print("⚠️ auto_play_voice column already exists, skipping...")

        except Exception as e:
            print(f"❌ Error during migration: {e}")
            raise


def downgrade():
    """Remove auto_play_voice column from settings table"""
    with app.app_context():
        try:
            # Check if column exists
            inspector = db.inspect(db.engine)
            columns = [col["name"] for col in inspector.get_columns("settings")]

            if "auto_play_voice" in columns:
                print("Removing auto_play_voice column from settings table...")

                # Remove the column
                db.engine.execute("ALTER TABLE settings DROP COLUMN auto_play_voice")

                print("✅ Successfully removed auto_play_voice column")
            else:
                print("⚠️ auto_play_voice column doesn't exist, skipping...")

        except Exception as e:
            print(f"❌ Error during rollback: {e}")
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add auto_play_voice setting migration")
    parser.add_argument(
        "action", choices=["upgrade", "downgrade"], help="Migration action to perform"
    )

    args = parser.parse_args()

    if args.action == "upgrade":
        upgrade()
    elif args.action == "downgrade":
        downgrade()
