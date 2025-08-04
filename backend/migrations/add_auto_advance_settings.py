"""
Migration script to add auto-advance settings to the settings table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the parent directory to the path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    import config
except ImportError:
    print(
        "Error: Could not import config module. Make sure you're running from the backend directory."
    )
    sys.exit(1)


def run_migration():
    """Run the migration to add auto-advance settings columns"""
    try:
        # Create database connection
        engine = create_engine(config.DATABASE_URL)

        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()

            try:
                # Check if columns already exist
                result = conn.execute(
                    text(
                        """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'settings'
                    AND column_name IN ('auto_advance_enabled', 'auto_advance_timeout')
                """
                    )
                )

                existing_columns = [row[0] for row in result]

                # Add auto_advance_enabled column if it doesn't exist
                if "auto_advance_enabled" not in existing_columns:
                    print("Adding auto_advance_enabled column...")
                    conn.execute(
                        text(
                            """
                        ALTER TABLE settings
                        ADD COLUMN auto_advance_enabled BOOLEAN NOT NULL DEFAULT FALSE
                    """
                        )
                    )
                    print("✓ Added auto_advance_enabled column")
                else:
                    print("✓ auto_advance_enabled column already exists")

                # Add auto_advance_timeout column if it doesn't exist
                if "auto_advance_timeout" not in existing_columns:
                    print("Adding auto_advance_timeout column...")
                    conn.execute(
                        text(
                            """
                        ALTER TABLE settings
                        ADD COLUMN auto_advance_timeout INTEGER NOT NULL DEFAULT 3
                    """
                        )
                    )
                    print("✓ Added auto_advance_timeout column")
                else:
                    print("✓ auto_advance_timeout column already exists")

                # Commit the transaction
                trans.commit()
                print("✅ Migration completed successfully!")

            except Exception as e:
                # Rollback on error
                trans.rollback()
                raise e

    except SQLAlchemyError as e:
        print(f"❌ Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False

    return True


def check_migration_status():
    """Check if the migration has already been applied"""
    try:
        engine = create_engine(config.DATABASE_URL)

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'settings'
                AND column_name IN ('auto_advance_enabled', 'auto_advance_timeout')
            """
                )
            )

            existing_columns = [row[0] for row in result]

            print(f"Existing auto-advance columns: {existing_columns}")
            return len(existing_columns) == 2

    except Exception as e:
        print(f"Error checking migration status: {e}")
        return False


if __name__ == "__main__":
    print("🔄 Starting auto-advance settings migration...")
    print("=" * 50)

    # Check current status
    print("Checking current migration status...")
    if check_migration_status():
        print("✅ Migration already applied - no action needed")
    else:
        print("📋 Migration needed - applying changes...")
        if run_migration():
            print("🎉 Migration completed successfully!")
        else:
            print("❌ Migration failed!")
            sys.exit(1)

    print("=" * 50)
    print("✅ Auto-advance settings migration completed")
