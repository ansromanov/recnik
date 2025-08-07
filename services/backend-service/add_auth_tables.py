#!/usr/bin/env python3
"""
Add authentication tables migration script
"""

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment variables")
    sys.exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# SQL for creating new tables
CREATE_TABLES_SQL = """
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    openai_api_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add an update trigger for settings.updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_settings_updated_at ON settings;
CREATE TRIGGER update_settings_updated_at
    BEFORE UPDATE ON settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id);
"""


def run_migration():
    """Run the migration to add authentication tables"""
    try:
        with engine.connect() as conn:
            # Execute the migration
            print("Creating authentication tables...")
            conn.execute(text(CREATE_TABLES_SQL))
            conn.commit()

            print("✓ Successfully created users and settings tables")

            # Verify tables were created
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('users', 'settings')
                ORDER BY table_name;
            """
                )
            )

            created_tables = [row[0] for row in result]
            print(f"\nCreated tables: {', '.join(created_tables)}")

    except Exception as e:
        print(f"✗ Error running migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("Authentication Tables Migration")
    print("=" * 50)
    run_migration()
