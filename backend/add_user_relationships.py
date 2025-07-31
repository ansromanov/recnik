"""
Migration script to add user relationships to vocabulary and practice sessions
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)


def run_migration():
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            try:
                print("Starting migration to add user relationships...")

                # 1. Add user_id to user_vocabulary table
                print("Adding user_id to user_vocabulary table...")
                conn.execute(
                    text("""
                    ALTER TABLE user_vocabulary 
                    ADD COLUMN IF NOT EXISTS user_id INTEGER;
                """)
                )

                # 2. Add foreign key constraint for user_vocabulary
                print("Adding foreign key constraint for user_vocabulary...")
                try:
                    conn.execute(
                        text("""
                        ALTER TABLE user_vocabulary 
                        ADD CONSTRAINT fk_user_vocabulary_user 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                    """)
                    )
                except Exception as e:
                    if "already exists" in str(e):
                        print(
                            "Foreign key constraint for user_vocabulary already exists"
                        )
                    else:
                        raise

                # 3. Add user_id to practice_sessions table
                print("Adding user_id to practice_sessions table...")
                conn.execute(
                    text("""
                    ALTER TABLE practice_sessions 
                    ADD COLUMN IF NOT EXISTS user_id INTEGER;
                """)
                )

                # 4. Add foreign key constraint for practice_sessions
                print("Adding foreign key constraint for practice_sessions...")
                try:
                    conn.execute(
                        text("""
                        ALTER TABLE practice_sessions 
                        ADD CONSTRAINT fk_practice_sessions_user 
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                    """)
                    )
                except Exception as e:
                    if "already exists" in str(e):
                        print(
                            "Foreign key constraint for practice_sessions already exists"
                        )
                    else:
                        raise

                # 5. Create unique constraint on user_vocabulary for user_id and word_id
                print("Creating unique constraint on user_vocabulary...")
                # First drop the existing unique constraint on word_id
                try:
                    conn.execute(
                        text("""
                        ALTER TABLE user_vocabulary 
                        DROP CONSTRAINT user_vocabulary_word_id_key;
                    """)
                    )
                except Exception as e:
                    if "does not exist" in str(e):
                        print(
                            "Unique constraint on word_id doesn't exist, skipping drop"
                        )
                    else:
                        raise

                # Then create a composite unique constraint
                try:
                    conn.execute(
                        text("""
                        ALTER TABLE user_vocabulary 
                        ADD CONSTRAINT user_vocabulary_user_word_unique 
                        UNIQUE (user_id, word_id);
                    """)
                    )
                except Exception as e:
                    if "already exists" in str(e):
                        print("Composite unique constraint already exists")
                    else:
                        raise

                # 6. Create indexes for better performance
                print("Creating indexes...")
                conn.execute(
                    text("""
                    CREATE INDEX IF NOT EXISTS idx_user_vocabulary_user_id 
                    ON user_vocabulary(user_id);
                """)
                )

                conn.execute(
                    text("""
                    CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_id 
                    ON practice_sessions(user_id);
                """)
                )

                # Commit transaction
                trans.commit()
                print("Migration completed successfully!")

            except Exception as e:
                trans.rollback()
                print(f"Error during migration, rolling back: {e}")
                raise

    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
