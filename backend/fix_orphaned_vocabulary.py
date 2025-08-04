"""
Script to fix orphaned vocabulary entries by assigning them to a specific user
"""

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)


def fix_orphaned_vocabulary(user_id):
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()

            try:
                # First, check how many orphaned entries exist
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) as count
                    FROM user_vocabulary
                    WHERE user_id IS NULL
                """
                    )
                )
                orphaned_count = result.scalar()
                print(f"Found {orphaned_count} orphaned vocabulary entries")

                if orphaned_count > 0:
                    # Update orphaned entries to belong to the specified user
                    conn.execute(
                        text(
                            """
                        UPDATE user_vocabulary
                        SET user_id = :user_id
                        WHERE user_id IS NULL
                    """
                        ),
                        {"user_id": user_id},
                    )
                    print(f"Assigned {orphaned_count} vocabulary entries to user {user_id}")

                # Verify the update
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) as count
                    FROM user_vocabulary
                    WHERE user_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )
                user_vocab_count = result.scalar()
                print(f"User {user_id} now has {user_vocab_count} vocabulary entries")

                # Commit transaction
                trans.commit()
                print("Successfully fixed orphaned vocabulary entries!")

            except Exception as e:
                trans.rollback()
                print(f"Error during fix, rolling back: {e}")
                raise

    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        # Default to user ID 1 if not specified
        user_id = 1
        print(f"No user ID specified, defaulting to user {user_id}")

    fix_orphaned_vocabulary(user_id)
