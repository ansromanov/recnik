"""
Database migration utility for SQLAlchemy models.
This script helps manage database schema changes.
"""

import os
import sys

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import text

from models import Category, PracticeResult, PracticeSession, UserVocabulary, Word, db

# Load environment variables
load_dotenv()

# Create Flask app for database context
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)


def create_tables():
    """Create all tables defined in models"""
    with app.app_context():
        db.create_all()
        print("All tables created successfully!")


def drop_tables():
    """Drop all tables (WARNING: This will delete all data!)"""
    response = input("WARNING: This will delete all data! Are you sure? (yes/no): ")
    if response.lower() == "yes":
        with app.app_context():
            db.drop_all()
            print("All tables dropped!")
    else:
        print("Operation cancelled.")


def seed_categories():
    """Seed default categories if they don't exist"""
    with app.app_context():
        existing_categories = Category.query.count()
        if existing_categories > 0:
            print(f"Categories already exist ({existing_categories} found). Skipping seed.")
            return

        default_categories = [
            ("Common Words", "Frequently used everyday words"),
            ("Verbs", "Action words"),
            ("Nouns", "People, places, things"),
            ("Adjectives", "Descriptive words"),
            ("Food & Drink", "Food and beverage related vocabulary"),
            ("Numbers", "Numbers and counting"),
            ("Time", "Time-related expressions"),
            ("Family", "Family and relationships"),
            ("Colors", "Color vocabulary"),
            ("Greetings", "Common greetings and phrases"),
        ]

        for name, description in default_categories:
            category = Category(name=name, description=description)
            db.session.add(category)

        db.session.commit()
        print(f"Seeded {len(default_categories)} categories!")


def show_stats():
    """Show database statistics"""
    with app.app_context():
        stats = {
            "Categories": Category.query.count(),
            "Words": Word.query.count(),
            "User Vocabulary": UserVocabulary.query.count(),
            "Practice Sessions": PracticeSession.query.count(),
            "Practice Results": PracticeResult.query.count(),
        }

        print("\nDatabase Statistics:")
        print("-" * 30)
        for table, count in stats.items():
            print(f"{table}: {count}")
        print("-" * 30)


def check_connection():
    """Check database connection"""
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
            print("Database connection successful!")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False


def main():
    """Main migration menu"""
    if not check_connection():
        sys.exit(1)

    while True:
        print("\n=== Database Migration Utility ===")
        print("1. Create all tables")
        print("2. Drop all tables (WARNING: Deletes all data!)")
        print("3. Seed default categories")
        print("4. Show database statistics")
        print("5. Exit")

        choice = input("\nSelect an option (1-5): ")

        if choice == "1":
            create_tables()
        elif choice == "2":
            drop_tables()
        elif choice == "3":
            seed_categories()
        elif choice == "4":
            show_stats()
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
