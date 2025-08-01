#!/usr/bin/env python3
"""
Database migration to add excluded_words table
This allows users to exclude words from lessons and practice
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()


def migrate():
    """Run the migration"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False

    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            # Create excluded_words table
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS excluded_words (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
                    reason VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT excluded_words_user_word_unique UNIQUE (user_id, word_id)
                );
            """)
            )

            # Create indexes for performance
            conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_excluded_words_user_id ON excluded_words(user_id);
            """)
            )

            conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_excluded_words_word_id ON excluded_words(word_id);
            """)
            )

            conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS idx_excluded_words_created_at ON excluded_words(created_at);
            """)
            )

            conn.commit()
            print("✅ Successfully created excluded_words table and indexes")
            return True

    except Exception as e:
        print(f"❌ Error creating excluded_words table: {e}")
        return False


def rollback():
    """Rollback the migration"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False

    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS excluded_words CASCADE;"))
            conn.commit()
            print("✅ Successfully dropped excluded_words table")
            return True

    except Exception as e:
        print(f"❌ Error dropping excluded_words table: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add excluded_words table migration")
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback the migration"
    )
    args = parser.parse_args()

    if args.rollback:
        rollback()
    else:
        migrate()
