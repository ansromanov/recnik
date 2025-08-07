"""
Migration to add XP system and achievement badges to the database.
This includes user XP tracking, levels, and achievement badges.
"""

from datetime import datetime, timezone
from models import db
from sqlalchemy import text


def add_xp_achievement_system():
    """Add XP system and achievement tables"""

    # Create UserXP table for tracking experience points and levels
    db.session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS user_xp (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            current_xp INTEGER NOT NULL DEFAULT 0,
            total_xp INTEGER NOT NULL DEFAULT 0,
            current_level INTEGER NOT NULL DEFAULT 1,
            xp_to_next_level INTEGER NOT NULL DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        );
    """
        )
    )

    # Create XPActivity table for tracking XP-earning activities
    db.session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS xp_activities (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activity_type VARCHAR(50) NOT NULL,
            xp_earned INTEGER NOT NULL DEFAULT 0,
            activity_date DATE NOT NULL DEFAULT CURRENT_DATE,
            activity_details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
        )
    )

    # Create Achievement definitions table
    db.session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS achievements (
            id SERIAL PRIMARY KEY,
            achievement_key VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            badge_icon VARCHAR(10),
            badge_color VARCHAR(20) DEFAULT '#3498db',
            category VARCHAR(50) DEFAULT 'general',
            xp_reward INTEGER DEFAULT 0,
            unlock_criteria JSONB NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
        )
    )

    # Create UserAchievements table for tracking earned achievements
    db.session.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS user_achievements (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            achievement_id INTEGER NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress_data JSONB,
            UNIQUE(user_id, achievement_id)
        );
    """
        )
    )

    # Create indexes for performance
    db.session.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_user_xp_user_id ON user_xp(user_id);
        CREATE INDEX IF NOT EXISTS idx_xp_activities_user_date ON xp_activities(user_id, activity_date);
        CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
        CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category);
        CREATE INDEX IF NOT EXISTS idx_achievements_active ON achievements(is_active);
    """
        )
    )

    # Insert predefined achievements
    achievements_data = [
        # Vocabulary achievements
        {
            "achievement_key": "first_100_words",
            "name": "First 100 Words",
            "description": "Add your first 100 words to vocabulary",
            "badge_icon": "📚",
            "badge_color": "#e74c3c",
            "category": "vocabulary",
            "xp_reward": 500,
            "unlock_criteria": '{"type": "vocabulary_count", "target": 100}',
        },
        {
            "achievement_key": "vocabulary_master_500",
            "name": "Vocabulary Master",
            "description": "Add 500 words to your vocabulary",
            "badge_icon": "🎓",
            "badge_color": "#9b59b6",
            "category": "vocabulary",
            "xp_reward": 1000,
            "unlock_criteria": '{"type": "vocabulary_count", "target": 500}',
        },
        {
            "achievement_key": "vocabulary_expert_1000",
            "name": "Vocabulary Expert",
            "description": "Add 1000 words to your vocabulary",
            "badge_icon": "👑",
            "badge_color": "#f39c12",
            "category": "vocabulary",
            "xp_reward": 2000,
            "unlock_criteria": '{"type": "vocabulary_count", "target": 1000}',
        },
        # Practice achievements
        {
            "achievement_key": "perfect_practice",
            "name": "Perfect Practice",
            "description": "Complete a practice session with 100% accuracy",
            "badge_icon": "💯",
            "badge_color": "#27ae60",
            "category": "practice",
            "xp_reward": 200,
            "unlock_criteria": '{"type": "perfect_session", "accuracy": 100}',
        },
        {
            "achievement_key": "practice_warrior_100",
            "name": "Practice Warrior",
            "description": "Complete 100 practice sessions",
            "badge_icon": "⚔️",
            "badge_color": "#e67e22",
            "category": "practice",
            "xp_reward": 800,
            "unlock_criteria": '{"type": "session_count", "target": 100}',
        },
        {
            "achievement_key": "quick_learner",
            "name": "Quick Learner",
            "description": "Answer 20 questions correctly in under 30 seconds total",
            "badge_icon": "⚡",
            "badge_color": "#f1c40f",
            "category": "practice",
            "xp_reward": 300,
            "unlock_criteria": '{"type": "speed_practice", "questions": 20, "max_time": 30}',
        },
        # Grammar achievements
        {
            "achievement_key": "grammar_master",
            "name": "Grammar Master",
            "description": "Master words from 5 different categories",
            "badge_icon": "📝",
            "badge_color": "#3498db",
            "category": "grammar",
            "xp_reward": 600,
            "unlock_criteria": '{"type": "categories_mastered", "target": 5, "mastery_threshold": 80}',
        },
        {
            "achievement_key": "top_100_champion",
            "name": "Top 100 Champion",
            "description": "Master all top 100 words",
            "badge_icon": "🏆",
            "badge_color": "#f39c12",
            "category": "grammar",
            "xp_reward": 1500,
            "unlock_criteria": '{"type": "top_100_mastery", "mastery_threshold": 80}',
        },
        # Streak achievements
        {
            "achievement_key": "week_warrior",
            "name": "Week Warrior",
            "description": "Maintain a 7-day learning streak",
            "badge_icon": "🔥",
            "badge_color": "#e74c3c",
            "category": "streak",
            "xp_reward": 300,
            "unlock_criteria": '{"type": "streak_days", "target": 7}',
        },
        {
            "achievement_key": "month_master",
            "name": "Month Master",
            "description": "Maintain a 30-day learning streak",
            "badge_icon": "🌟",
            "badge_color": "#f39c12",
            "category": "streak",
            "xp_reward": 1000,
            "unlock_criteria": '{"type": "streak_days", "target": 30}',
        },
        {
            "achievement_key": "year_legend",
            "name": "Year Legend",
            "description": "Maintain a 365-day learning streak",
            "badge_icon": "👑",
            "badge_color": "#9b59b6",
            "category": "streak",
            "xp_reward": 5000,
            "unlock_criteria": '{"type": "streak_days", "target": 365}',
        },
        # Milestone achievements
        {
            "achievement_key": "first_steps",
            "name": "First Steps",
            "description": "Complete your first practice session",
            "badge_icon": "👶",
            "badge_color": "#1abc9c",
            "category": "milestone",
            "xp_reward": 50,
            "unlock_criteria": '{"type": "session_count", "target": 1}',
        },
        {
            "achievement_key": "level_10_hero",
            "name": "Level 10 Hero",
            "description": "Reach level 10",
            "badge_icon": "🦸",
            "badge_color": "#e74c3c",
            "category": "milestone",
            "xp_reward": 500,
            "unlock_criteria": '{"type": "level_reached", "target": 10}',
        },
        {
            "achievement_key": "level_25_legend",
            "name": "Level 25 Legend",
            "description": "Reach level 25",
            "badge_icon": "🌟",
            "badge_color": "#f39c12",
            "category": "milestone",
            "xp_reward": 1000,
            "unlock_criteria": '{"type": "level_reached", "target": 25}',
        },
        {
            "achievement_key": "level_50_master",
            "name": "Level 50 Master",
            "description": "Reach level 50",
            "badge_icon": "👑",
            "badge_color": "#9b59b6",
            "category": "milestone",
            "xp_reward": 2500,
            "unlock_criteria": '{"type": "level_reached", "target": 50}',
        },
    ]

    # Insert achievements
    for achievement in achievements_data:
        db.session.execute(
            text(
                """
            INSERT INTO achievements (achievement_key, name, description, badge_icon, badge_color, category, xp_reward, unlock_criteria)
            VALUES (:achievement_key, :name, :description, :badge_icon, :badge_color, :category, :xp_reward, :unlock_criteria)
            ON CONFLICT (achievement_key) DO NOTHING
        """
            ),
            achievement,
        )

    db.session.commit()
    print("XP system and achievement tables created successfully!")


if __name__ == "__main__":
    from app import app

    with app.app_context():
        add_xp_achievement_system()
