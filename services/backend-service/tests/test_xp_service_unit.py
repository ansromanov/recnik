"""
Pure unit tests for XP Service functionality without database dependencies
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Achievement, UserXP
from services.xp_service import XPService


class TestXPServiceUnitTests:
    """Pure unit tests for XP service using mocks"""

    @pytest.fixture
    def xp_service(self):
        return XPService()

    def test_calculate_level_progression_edge_cases(self, xp_service):
        """Test level calculation with edge cases"""
        # Test level 0 and 1
        assert xp_service.calculate_xp_for_level(0) == 0
        assert xp_service.calculate_xp_for_level(1) == 0

        # Test level 2 (should be BASE_XP)
        assert xp_service.calculate_xp_for_level(2) == xp_service.BASE_XP

        # Test level 3 (should be BASE_XP + BASE_XP * 1.5)
        expected_level_3 = xp_service.BASE_XP + int(xp_service.BASE_XP * xp_service.XP_MULTIPLIER)
        assert xp_service.calculate_xp_for_level(3) == expected_level_3

    def test_calculate_level_from_xp_progression(self, xp_service):
        """Test level calculation from XP progression"""
        # Test XP below first level threshold
        level, xp_to_next = xp_service.calculate_level_from_xp(50)
        assert level == 1
        assert xp_to_next == 50  # 100 - 50

        # Test XP at exact level threshold
        level, xp_to_next = xp_service.calculate_level_from_xp(100)
        assert level == 2

        # Test high XP values should cap at level 100
        level, xp_to_next = xp_service.calculate_level_from_xp(999999)
        assert level <= 100

    @patch("models.UserVocabulary.query")
    def test_check_achievement_criteria_vocabulary_count_mock(self, mock_query, xp_service):
        """Test vocabulary count criteria with mocking"""
        # Mock the query chain
        mock_query.filter_by.return_value.count.return_value = 8

        achievement = Achievement(
            achievement_key="vocab_10", unlock_criteria={"type": "vocabulary_count", "target": 10}
        )

        # Should not meet criteria (8 < 10)
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is False

        # Mock meeting criteria
        mock_query.filter_by.return_value.count.return_value = 12
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is True

    @patch("models.UserXP.query")
    def test_check_achievement_criteria_level_reached_mock(self, mock_query, xp_service):
        """Test level reached criteria with mocking"""
        # Create mock UserXP
        mock_user_xp = UserXP(user_id=1, current_level=3)
        mock_query.filter_by.return_value.first.return_value = mock_user_xp

        achievement = Achievement(
            achievement_key="level_5", unlock_criteria={"type": "level_reached", "target": 5}
        )

        # Should not meet criteria (3 < 5)
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is False

        # Update mock to level 5
        mock_user_xp.current_level = 5
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is True

    def test_check_achievement_criteria_unknown_type_mock(self, xp_service):
        """Test achievement criteria with unknown type"""
        achievement = Achievement(
            achievement_key="unknown", unlock_criteria={"type": "unknown_type", "target": 1}
        )

        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is False

    def test_xp_values_constants(self, xp_service):
        """Test XP value constants are properly defined"""
        assert xp_service.XP_VALUES["vocabulary_added"] == 10
        assert xp_service.XP_VALUES["practice_correct"] == 5
        assert xp_service.XP_VALUES["practice_session_complete"] == 25
        assert xp_service.XP_VALUES["practice_perfect_session"] == 50
        assert xp_service.XP_VALUES["level_up"] == 100

        assert xp_service.BASE_XP == 100
        assert xp_service.XP_MULTIPLIER == 1.5

    @patch("models.PracticeSession.query")
    def test_check_achievement_criteria_session_count_mock(self, mock_query, xp_service):
        """Test session count criteria with mocking"""
        # Mock the query chain
        mock_query.filter.return_value.count.return_value = 15

        achievement = Achievement(
            achievement_key="sessions_20", unlock_criteria={"type": "session_count", "target": 20}
        )

        # Should not meet criteria (15 < 20)
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is False

        # Mock meeting criteria
        mock_query.filter.return_value.count.return_value = 25
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is True

    @patch("models.UserStreak.query")
    def test_check_achievement_criteria_streak_days_mock(self, mock_query, xp_service):
        """Test streak days criteria with mocking"""
        # Create mock UserStreak
        mock_streak = MagicMock()
        mock_streak.current_streak = 5
        mock_query.filter.return_value.first.return_value = mock_streak

        achievement = Achievement(
            achievement_key="streak_7", unlock_criteria={"type": "streak_days", "target": 7}
        )

        # Should not meet criteria (5 < 7)
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is False

        # Update mock to meet criteria
        mock_streak.current_streak = 10
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is True

    def test_check_achievement_criteria_speed_practice_mock(self, xp_service):
        """Test speed practice criteria (always returns False for now)"""
        achievement = Achievement(
            achievement_key="speed_master",
            unlock_criteria={"type": "speed_practice", "questions": 20, "max_time": 30},
        )

        # Should return False as this feature needs session timing data
        result = xp_service._check_achievement_criteria(1, achievement)
        assert result is False

    def test_service_initialization(self, xp_service):
        """Test XP service initialization"""
        assert isinstance(xp_service, XPService)
        assert hasattr(xp_service, "XP_VALUES")
        assert hasattr(xp_service, "BASE_XP")
        assert hasattr(xp_service, "XP_MULTIPLIER")

    def test_level_calculation_formula(self, xp_service):
        """Test level calculation formula consistency"""
        # Test multiple levels to ensure formula is consistent
        level_2_xp = xp_service.calculate_xp_for_level(2)
        level_3_xp = xp_service.calculate_xp_for_level(3)
        level_4_xp = xp_service.calculate_xp_for_level(4)

        # Each level should require more XP than the previous
        assert level_3_xp > level_2_xp
        assert level_4_xp > level_3_xp

        # Verify exponential growth
        level_2_requirement = level_2_xp
        level_3_requirement = level_3_xp - level_2_xp
        level_4_requirement = level_4_xp - level_3_xp

        assert level_3_requirement > level_2_requirement
        assert level_4_requirement > level_3_requirement

    def test_xp_calculation_edge_cases(self, xp_service):
        """Test XP calculation with edge case values"""
        # Test negative level
        assert xp_service.calculate_xp_for_level(-1) == 0

        # Test very high level (should not cause overflow)
        high_level_xp = xp_service.calculate_xp_for_level(50)
        assert isinstance(high_level_xp, int)
        assert high_level_xp > 0
