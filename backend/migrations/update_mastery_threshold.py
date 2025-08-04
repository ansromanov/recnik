#!/usr/bin/env python3
"""
Migration script to update mastery threshold from 10 to 5 for existing users.
This ensures all users have the new default threshold.
"""

import sys
import os

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Settings


def update_mastery_threshold():
    """Update mastery threshold from 10 to 5 for existing users"""
    with app.app_context():
        try:
            # Find all users with mastery_threshold = 10
            old_settings = Settings.query.filter_by(mastery_threshold=10).all()

            if old_settings:
                print(f"Found {len(old_settings)} users with old mastery threshold of 10")

                for setting in old_settings:
                    setting.mastery_threshold = 5
                    print(f"Updated user {setting.user_id} mastery threshold from 10 to 5")

                db.session.commit()
                print(f"Successfully updated {len(old_settings)} users")
            else:
                print("No users found with old mastery threshold of 10")

            # Also update any users with mastery_threshold > 10 (edge case)
            high_threshold_settings = Settings.query.filter(Settings.mastery_threshold > 10).all()

            if high_threshold_settings:
                print(f"Found {len(high_threshold_settings)} users with mastery threshold > 10")

                for setting in high_threshold_settings:
                    setting.mastery_threshold = 5
                    print(
                        f"Updated user {setting.user_id} mastery threshold from {setting.mastery_threshold} to 5"
                    )

                db.session.commit()
                print(
                    f"Successfully updated {len(high_threshold_settings)} users with high thresholds"
                )

            print("Mastery threshold migration completed successfully!")

        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    update_mastery_threshold()
