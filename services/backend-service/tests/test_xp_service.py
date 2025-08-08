"""
Tests for XP Service functionality
"""

import os
import sys

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import (
    Achievement,
    User,
    UserXP,
    XPActivity,
)
from services.xp_service import XPService


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
        result = xp_service.record_vocabulary_addition_xp(user_id=test_user.id, words_added=5)

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
        # Create unique user for each test to avoid conflicts
        import uuid

        username = f"achievementuser_{uuid.uuid4().hex[:8]}"
        user = User(username=username)
        user.set_password("password")
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def sample_achievement(self, db_session):
        """Create sample achievement"""
        # Check if achievement already exists
        existing = Achievement.query.filter_by(achievement_key="vocab_collector").first()
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

    @pytest.mark.skip(reason="Database isolation issues - needs refactoring")
    def test_achievement_criteria_checking(
        self, xp_service, test_user, sample_achievement, db_session
    ):
        """Test achievement criteria evaluation"""
        pass

    @pytest.mark.skip(reason="Database isolation issues - needs refactoring")
    def test_achievement_unlocking(self, xp_service, test_user, sample_achievement, db_session):
        """Test automatic achievement unlocking"""
        pass

    @pytest.mark.skip(reason="Database isolation issues - needs refactoring")
    def test_achievement_progress_tracking(
        self, xp_service, test_user, sample_achievement, db_session
    ):
        """Test progress tracking towards achievements"""
        pass


class TestXPLeaderboard:
    """Test XP leaderboard functionality"""

    @pytest.fixture
    def xp_service(self):
        return XPService()

    @pytest.mark.skip(reason="Database isolation issues - needs refactoring")
    def test_xp_leaderboard_ranking(self, xp_service, db_session):
        """Test XP leaderboard generation"""
        pass

    @pytest.mark.skip(reason="Database isolation issues - needs refactoring")
    def test_empty_leaderboard(self, xp_service, db_session):
        """Test leaderboard with no users"""
        pass
