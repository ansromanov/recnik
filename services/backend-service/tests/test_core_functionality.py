"""
Core functionality tests - simplified and focused
"""

import os
import sys

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.avatar_service import AvatarService
from services.streak_service import StreakService
from services.xp_service import XPService


class TestAvatarServiceCore:
    """Test core avatar functionality only"""

    def test_avatar_seed_generation(self):
        """Test avatar seed generation"""
        service = AvatarService()
        seed1 = service.generate_avatar_seed("testuser")
        seed2 = service.generate_avatar_seed("testuser")

        assert seed1 == seed2
        assert isinstance(seed1, str)
        assert len(seed1) == 16

    def test_avatar_url_generation(self):
        """Test avatar URL generation"""
        service = AvatarService()
        url = service.get_avatar_url("test123", "avataaars", 128)

        assert isinstance(url, str)
        assert "dicebear.com" in url
        assert "test123" in url

    def test_create_user_avatar(self):
        """Test creating user avatar"""
        service = AvatarService()
        avatar_data = service.create_user_avatar("testuser")

        assert "avatar_url" in avatar_data
        assert "avatar_type" in avatar_data
        assert "avatar_seed" in avatar_data
        assert avatar_data["avatar_type"] == "ai_generated"


class TestStreakServiceCore:
    """Test core streak functionality only"""

    def test_streak_service_initialization(self):
        """Test streak service initialization"""
        service = StreakService()
        assert service is not None
        assert hasattr(service, "STREAK_TYPES")
        assert hasattr(service, "MIN_PRACTICE_QUESTIONS")

    def test_qualifying_activity_check(self):
        """Test activity qualification logic"""
        service = StreakService()

        # Practice session - qualifying
        assert service._is_qualifying_activity("practice_session", 10) is True
        # Practice session - not qualifying
        assert service._is_qualifying_activity("practice_session", 3) is False

        # Vocabulary addition - qualifying
        assert service._is_qualifying_activity("vocabulary_added", 5) is True
        # Vocabulary addition - not qualifying
        assert service._is_qualifying_activity("vocabulary_added", 1) is False

    def test_progress_calculation(self):
        """Test progress percentage calculation"""
        service = StreakService()

        # Test progress towards first milestone
        progress = service._calculate_progress_percentage(3)
        assert isinstance(progress, int)
        assert 0 <= progress <= 100


class TestXPServiceCore:
    """Test core XP functionality only"""

    def test_xp_service_initialization(self):
        """Test XP service initialization"""
        service = XPService()
        assert service is not None
        assert hasattr(service, "XP_VALUES")
        assert hasattr(service, "BASE_XP")

    def test_level_calculation(self):
        """Test XP to level calculation"""
        service = XPService()

        level, xp_to_next = service.calculate_level_from_xp(0)
        assert level == 1
        assert xp_to_next > 0

        level, xp_to_next = service.calculate_level_from_xp(100)
        assert level >= 2


if __name__ == "__main__":
    pytest.main([__file__])
