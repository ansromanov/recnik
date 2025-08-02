"""
Tests for XP Service functionality
"""

import pytest
import sys
import os
from datetime import date, timedelta
from unittest.mock import patch, Mock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.xp_service import XPService
from models import (
    db,
    UserXP,
    XPActivity,
    Achievement,
    UserAchievement,
    User,
    UserVocabulary,
    PracticeSession,
)


class TestXPService:
    """Test XP service core functionality"""

    @pytest.fixture
    def xp_service(self):
        """Create XP service instance"""
        return XPService()

    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(username="xpuser")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()
        return user

    def test_get_or_create_user_xp(self, xp_service, test_user, db_session):
        """Test getting or creating UserXP record"""
        # Test creation of new UserXP
        user_xp = xp_service.get_or_create_user_xp(test_user.id)

        assert user_xp is not None
        assert user_xp.user_id == test_user.id
        assert user_xp.current_xp == 0
        assert user_xp.total_xp == 0
        assert user_xp.current_level == 1

        # Test getting existing UserXP
        existing_user_xp = xp_service.get_or_create_user_xp(test_user.id)
        assert existing_user_xp.id == user_xp.id

    def test_calculate_level_progression(self, xp_service):
        """Test level calculation from XP"""
        # Test level 1 (starting level)
        level, xp_to_next = xp_service.calculate_level_from_xp(0)
        assert level == 1
        assert xp_to_next == 100  # BASE_XP

        # Test level 2
        level, xp_to_next = xp_service.calculate_level_from_xp(100)
        assert level == 2
        assert xp_to_next == 150  # 250 - 100 (need 150 more XP to reach level 3)

        # Test higher level
        level, xp_to_next = xp_service.calculate_level_from_xp(500)
        assert level >= 3

    def test_award_xp_basic(self, xp_service, test_user, db_session):
        """Test basic XP awarding"""
        result = xp_service.award_xp(
            user_id=test_user.id, activity_type="vocabulary_added", xp_amount=50
        )

        assert result["success"] is True
        assert result["xp_awarded"] == 50
        assert result["new_level"] >= 1

        # Check database record
        user_xp = UserXP.query.filter_by(user_id=test_user.id).first()
        assert user_xp.total_xp == 50
        assert user_xp.current_xp == 50

        # Check XP activity record
        activity = XPActivity.query.filter_by(user_id=test_user.id).first()
        assert activity is not None
        assert activity.activity_type == "vocabulary_added"
        assert activity.xp_earned == 50

    def test_level_up_detection(self, xp_service, test_user, db_session):
        """Test level up detection and bonus XP"""
        # Award enough XP to level up
        result = xp_service.award_xp(
            user_id=test_user.id,
            activity_type="practice_session_complete",
            xp_amount=150,  # Should trigger level up
        )

        assert result["success"] is True
        assert result["level_up_occurred"] is True
        assert result["new_level"] > result["old_level"]
        assert result["level_up_bonus"] > 0

    def test_practice_session_xp_integration(self, xp_service, test_user, db_session):
        """Test XP calculation for practice sessions"""
        result = xp_service.record_practice_session_xp(
            user_id=test_user.id,
            total_questions=10,
            correct_answers=8,
            session_duration=120,
        )

        assert result["success"] is True
        assert result["xp_awarded"] > 0

        # Should include session completion XP + correct answer XP
        expected_base = 25  # practice_session_complete
        expected_correct = 8 * 5  # 8 correct * 5 XP each
        assert result["xp_awarded"] == expected_base + expected_correct

        # Test perfect session bonus
        perfect_result = xp_service.record_practice_session_xp(
            user_id=test_user.id,
            total_questions=10,
            correct_answers=10,  # Perfect score
        )

        assert perfect_result["success"] is True
        # Should include perfect session bonus
        expected_perfect = 25 + (10 * 5) + 50  # base + correct + perfect bonus
        assert perfect_result["xp_awarded"] == expected_perfect

    def test_vocabulary_addition_xp(self, xp_service, test_user, db_session):
        """Test XP for adding vocabulary words"""
        result = xp_service.record_vocabulary_addition_xp(
            user_id=test_user.id, words_added=5
        )

        assert result["success"] is True
        expected_xp = 5 * 10  # 5 words * 10 XP each
        assert result["xp_awarded"] == expected_xp

    def test_get_user_xp_info(self, xp_service, test_user, db_session):
        """Test comprehensive XP info retrieval"""
        # Award some XP first
        xp_service.award_xp(test_user.id, "vocabulary_added", 100)

        xp_info = xp_service.get_user_xp_info(test_user.id)

        assert "user_xp" in xp_info
        assert "level_progress" in xp_info
        assert "recent_activities" in xp_info
        assert "daily_xp" in xp_info

        level_progress = xp_info["level_progress"]
        assert "current_level" in level_progress
        assert "level_progress_percentage" in level_progress
        assert "xp_to_next_level" in level_progress


class TestXPAchievements:
    """Test achievement system integration"""

    @pytest.fixture
    def xp_service(self):
        return XPService()

    @pytest.fixture
    def test_user(self, db_session):
        # Check if user already exists
        existing = User.query.filter_by(username="achievementuser").first()
        if existing:
            return existing

        user = User(username="achievementuser")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_achievement(self, db_session):
        """Create sample achievement"""
        # Check if achievement already exists
        existing = Achievement.query.filter_by(
            achievement_key="vocab_collector"
        ).first()
        if existing:
            return existing

        achievement = Achievement(
            achievement_key="vocab_collector",
            name="Vocabulary Collector",
            description="Add 10 words to vocabulary",
            category="vocabulary",
            unlock_criteria={"type": "vocabulary_count", "target": 10},
            xp_reward=100,
            is_active=True,
        )
        db_session.add(achievement)
        db_session.commit()
        return achievement

    def test_achievement_criteria_checking(
        self, xp_service, test_user, sample_achievement, db_session
    ):
        """Test achievement criteria evaluation"""
        # Initially shouldn't qualify
        qualifies = xp_service._check_achievement_criteria(
            test_user.id, sample_achievement
        )
        assert qualifies is False

        # Add vocabulary words to meet criteria
        from models import Word, UserVocabulary

        for i in range(10):
            word = Word(
                serbian_word=f"testword{i}",
                english_translation=f"testword{i}",
                category_id=1,
            )
            db_session.add(word)
            db_session.flush()

            user_vocab = UserVocabulary(user_id=test_user.id, word_id=word.id)
            db_session.add(user_vocab)

        db_session.commit()

        # Now should qualify
        qualifies = xp_service._check_achievement_criteria(
            test_user.id, sample_achievement
        )
        assert qualifies is True

    def test_achievement_unlocking(
        self, xp_service, test_user, sample_achievement, db_session
    ):
        """Test automatic achievement unlocking"""
        # Create vocabulary to trigger achievement
        from models import Word, UserVocabulary

        for i in range(10):
            word = Word(
                serbian_word=f"unlockword{i}",
                english_translation=f"unlockword{i}",
                category_id=1,
            )
            db_session.add(word)
            db_session.flush()

            user_vocab = UserVocabulary(user_id=test_user.id, word_id=word.id)
            db_session.add(user_vocab)

        db_session.commit()

        # Check achievements
        new_achievements = xp_service.check_and_unlock_achievements(test_user.id)

        assert len(new_achievements) == 1
        assert (
            new_achievements[0]["achievement"]["achievement_key"] == "vocab_collector"
        )

        # Verify UserAchievement was created
        user_achievement = UserAchievement.query.filter_by(
            user_id=test_user.id, achievement_id=sample_achievement.id
        ).first()
        assert user_achievement is not None

    def test_achievement_progress_tracking(
        self, xp_service, test_user, sample_achievement, db_session
    ):
        """Test progress tracking towards achievements"""
        # Add some vocabulary (less than required)
        from models import Word, UserVocabulary

        for i in range(5):
            word = Word(
                serbian_word=f"progressword{i}",
                english_translation=f"progressword{i}",
                category_id=1,
            )
            db_session.add(word)
            db_session.flush()

            user_vocab = UserVocabulary(user_id=test_user.id, word_id=word.id)
            db_session.add(user_vocab)

        db_session.commit()

        progress = xp_service._get_achievement_progress(
            test_user.id, sample_achievement
        )

        assert progress["current"] == 5
        assert progress["target"] == 10
        assert progress["percentage"] == 50
        assert "vocabulary" in progress["description"]


class TestXPLeaderboard:
    """Test XP leaderboard functionality"""

    @pytest.fixture
    def xp_service(self):
        return XPService()

    def test_xp_leaderboard_ranking(self, xp_service, db_session):
        """Test XP leaderboard generation"""
        # Create users with different XP amounts
        users = []
        xp_amounts = [500, 300, 800, 100, 600]

        for i, xp in enumerate(xp_amounts):
            user = User(username=f"leaderuser{i}")
            user.set_password("password")
            db_session.add(user)
            db_session.flush()
            users.append(user)

            # Create UserXP record
            user_xp = UserXP(
                user_id=user.id, total_xp=xp, current_xp=xp, current_level=xp // 100 + 1
            )
            db_session.add(user_xp)

        db_session.commit()

        # Get leaderboard
        leaderboard = xp_service.get_xp_leaderboard(limit=5)

        assert len(leaderboard) == 5

        # Should be sorted by total_xp descending
        assert leaderboard[0]["total_xp"] == 800
        assert leaderboard[1]["total_xp"] == 600
        assert leaderboard[2]["total_xp"] == 500

        # Check rank assignment
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[1]["rank"] == 2
        assert leaderboard[2]["rank"] == 3

    def test_empty_leaderboard(self, xp_service, db_session):
        """Test leaderboard with no users"""
        leaderboard = xp_service.get_xp_leaderboard()
        assert leaderboard == []
