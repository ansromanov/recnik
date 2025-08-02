"""
Migration script to add streak models for gamification features.
Creates UserStreak and StreakActivity tables for tracking daily/weekly/monthly streaks.
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Date,
    inspect,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Add the parent directory to Python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import config

    DATABASE_URL = config.DATABASE_URL
except ImportError:
    # Fallback to environment variable if config import fails
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://vocab_user:vocab_pass@localhost:5432/vocab_db"
    )


def run_migration():
    """Add streak tracking tables"""
    engine = create_engine(DATABASE_URL)

    # Create the tables using raw SQL to avoid metadata issues
    with engine.connect() as conn:
        # Check if tables already exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # Create user_streaks table
        if "user_streaks" not in existing_tables:
            conn.execute(
                text("""
                CREATE TABLE user_streaks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    streak_type VARCHAR(20) NOT NULL,
                    current_streak INTEGER NOT NULL DEFAULT 0,
                    longest_streak INTEGER NOT NULL DEFAULT 0,
                    last_activity_date DATE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            )
            print("✅ Created user_streaks table")
        else:
            print("ℹ️  user_streaks table already exists")

        # Create streak_activities table
        if "streak_activities" not in existing_tables:
            conn.execute(
                text("""
                CREATE TABLE streak_activities (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    activity_date DATE NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    activity_count INTEGER NOT NULL DEFAULT 1,
                    streak_qualifying BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            )
            print("✅ Created streak_activities table")
        else:
            print("ℹ️  streak_activities table already exists")

        # Add unique constraint for user_id + streak_type combination
        try:
            conn.execute(
                text("""
                ALTER TABLE user_streaks 
                ADD CONSTRAINT user_streaks_user_type_unique 
                UNIQUE (user_id, streak_type)
            """)
            )
            print("✅ Added unique constraint to user_streaks")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Unique constraint already exists on user_streaks")
            else:
                print(f"⚠️  Could not add constraint: {e}")

        # Add unique constraint for user_id + activity_date combination
        try:
            conn.execute(
                text("""
                ALTER TABLE streak_activities 
                ADD CONSTRAINT streak_activities_user_date_unique 
                UNIQUE (user_id, activity_date)
            """)
            )
            print("✅ Added unique constraint to streak_activities")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Unique constraint already exists on streak_activities")
            else:
                print(f"⚠️  Could not add constraint: {e}")

        # Add indexes for better performance
        try:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_streaks_user_id ON user_streaks(user_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_streaks_type ON user_streaks(streak_type)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_streak_activities_user_id ON streak_activities(user_id)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_streak_activities_date ON streak_activities(activity_date)"
                )
            )
            print("✅ Added performance indexes")
        except Exception as e:
            print(f"⚠️  Could not add indexes: {e}")

        conn.commit()


if __name__ == "__main__":
    try:
        run_migration()
        print("\n🎉 Streak models migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
