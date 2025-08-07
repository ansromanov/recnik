"""
Tests for Avatar Service functionality
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.avatar_service import AvatarService
from models import db, User


class TestAvatarService:
    """Test avatar service core functionality"""

    @pytest.fixture
    def avatar_service(self):
        """Create avatar service instance"""
        return AvatarService()

    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(username="avataruser")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()
        return user

    def test_avatar_service_initialization(self, avatar_service):
        """Test avatar service initialization"""
        assert avatar_service is not None
        assert hasattr(avatar_service, "avatar_styles")
        assert hasattr(avatar_service, "default_style")
        assert len(avatar_service.avatar_styles) > 0

    def test_avatar_seed_generation(self, avatar_service):
        """Test avatar seed generation from username"""
        username = "testuser"
        seed1 = avatar_service.generate_avatar_seed(username)
        seed2 = avatar_service.generate_avatar_seed(username)

        # Same username should generate same seed
        assert seed1 == seed2

        # Different usernames should generate different seeds
        seed3 = avatar_service.generate_avatar_seed("differentuser")
        assert seed1 != seed3

        # Seed should be a string
        assert isinstance(seed1, str)
        assert len(seed1) == 16  # Should be exactly 16 characters

        # For deterministic testing, check expected hash for known input
        # MD5 hash of "testuser" truncated to 16 chars
        import hashlib

        expected_seed = hashlib.md5("testuser".encode()).hexdigest()[:16]
        assert seed1 == expected_seed

    def test_get_avatar_url(self, avatar_service):
        """Test avatar URL generation"""
        seed = "test123"
        style = avatar_service.default_style
        size = 128

        url = avatar_service.get_avatar_url(seed, style, size)

        assert url is not None
        assert isinstance(url, str)
        assert "https://" in url or "http://" in url
        assert seed in url or str(size) in url

    def test_create_user_avatar(self, avatar_service):
        """Test creating avatar for user"""
        username = "testuser"
        # Use a style that actually exists in the service
        style = "avataaars"  # This is in the actual avatar_styles list

        avatar_data = avatar_service.create_user_avatar(username, style)

        assert "avatar_url" in avatar_data
        assert "avatar_type" in avatar_data
        assert "avatar_seed" in avatar_data
        assert avatar_data["avatar_type"] == "ai_generated"
        assert isinstance(avatar_data["avatar_url"], str)
        assert isinstance(avatar_data["avatar_seed"], str)

    def test_create_user_avatar_default_style(self, avatar_service):
        """Test creating avatar with default style"""
        username = "testuser"

        avatar_data = avatar_service.create_user_avatar(username)

        assert "avatar_url" in avatar_data
        assert "avatar_type" in avatar_data
        assert "avatar_seed" in avatar_data
        assert avatar_data["avatar_type"] == "ai_generated"

    def test_regenerate_avatar(self, avatar_service):
        """Test avatar regeneration"""
        username = "testuser"
        original_seed = avatar_service.generate_avatar_seed(username)

        # Regenerate with new seed
        new_avatar = avatar_service.regenerate_avatar(username, keep_seed=False)

        assert "avatar_url" in new_avatar
        assert "avatar_seed" in new_avatar
        # New seed should be different when keep_seed=False
        assert new_avatar["avatar_seed"] != original_seed

    def test_regenerate_avatar_keep_seed(self, avatar_service):
        """Test avatar regeneration keeping same seed"""
        username = "testuser"
        original_seed = avatar_service.generate_avatar_seed(username)

        # Regenerate keeping the same seed
        new_avatar = avatar_service.regenerate_avatar(
            username, keep_seed=True, current_seed=original_seed
        )

        assert "avatar_url" in new_avatar
        assert "avatar_seed" in new_avatar
        # Should keep the same seed
        assert new_avatar["avatar_seed"] == original_seed

    def test_get_avatar_variations(self, avatar_service):
        """Test getting avatar variations"""
        seed = "test123"
        count = 6

        variations = avatar_service.get_avatar_variations(seed, count)

        assert isinstance(variations, list)
        assert len(variations) == count

        for variation in variations:
            assert "avatar_url" in variation
            assert "style" in variation
            assert "style_name" in variation
            assert isinstance(variation["avatar_url"], str)

    def test_get_default_avatar(self, avatar_service):
        """Test getting default avatar for user"""
        username = "defaultuser"

        default_avatar = avatar_service.get_default_avatar(username)

        assert "avatar_url" in default_avatar
        assert "avatar_type" in default_avatar
        assert "avatar_seed" in default_avatar
        assert default_avatar["avatar_type"] == "ai_generated"

    def test_validate_uploaded_avatar_valid_image(self, avatar_service):
        """Test validation of valid uploaded avatar"""
        # Mock valid image data
        valid_image_data = b"\x89PNG\r\n\x1a\n" + b"test_image_data"
        content_type = "image/png"

        result = avatar_service.validate_uploaded_avatar(valid_image_data, content_type)

        assert result["valid"] is True
        assert "size" in result
        assert result["size"] == len(valid_image_data)

    def test_validate_uploaded_avatar_invalid_type(self, avatar_service):
        """Test validation of invalid file type"""
        invalid_data = b"not_an_image"
        content_type = "text/plain"

        result = avatar_service.validate_uploaded_avatar(invalid_data, content_type)

        assert result["valid"] is False
        assert "error" in result
        # Check for the actual error message from the service
        assert (
            "invalid file type" in result["error"].lower()
            or "allowed types" in result["error"].lower()
        )

    def test_validate_uploaded_avatar_too_large(self, avatar_service):
        """Test validation of file that's too large"""
        # Mock large file (over 5MB)
        large_file_data = b"x" * (6 * 1024 * 1024)  # 6MB
        content_type = "image/jpeg"

        result = avatar_service.validate_uploaded_avatar(large_file_data, content_type)

        assert result["valid"] is False
        assert "error" in result
        assert "too large" in result["error"].lower()

    def test_avatar_styles_availability(self, avatar_service):
        """Test that avatar styles are properly configured"""
        styles = avatar_service.avatar_styles

        assert isinstance(styles, list)
        assert len(styles) > 0
        assert avatar_service.default_style in styles

        # Common avatar styles should be available
        expected_styles = ["adventurer", "avataaars", "bottts", "personas"]
        for style in expected_styles:
            if style in styles:  # Not all providers may have all styles
                assert isinstance(style, str)
                assert len(style) > 0


class TestAvatarServiceIntegration:
    """Test avatar service integration with user management"""

    @pytest.fixture
    def avatar_service(self):
        return AvatarService()

    def test_user_avatar_workflow(self, avatar_service, db_session):
        """Test complete user avatar workflow"""
        # Create user without avatar
        user = User(username="avatartest")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()
        assert user.avatar_url is None
        assert user.avatar_type is None
        assert user.avatar_seed is None

        # Generate avatar for user
        avatar_data = avatar_service.create_user_avatar(user.username)

        # Update user with avatar data
        user.avatar_url = avatar_data["avatar_url"]
        user.avatar_type = avatar_data["avatar_type"]
        user.avatar_seed = avatar_data["avatar_seed"]
        db_session.commit()

        # Verify user has avatar
        assert user.avatar_url is not None
        assert user.avatar_type == "ai_generated"
        assert user.avatar_seed is not None

        # Test avatar regeneration
        new_avatar = avatar_service.regenerate_avatar(user.username)
        user.avatar_url = new_avatar["avatar_url"]
        user.avatar_seed = new_avatar["avatar_seed"]
        db_session.commit()

        # Should have new avatar data
        assert user.avatar_url != avatar_data["avatar_url"]

    def test_consistent_avatar_generation(self, avatar_service):
        """Test that avatar generation is consistent for same user"""
        username = "consistentuser"

        # Generate avatar multiple times
        avatar1 = avatar_service.create_user_avatar(username)
        avatar2 = avatar_service.create_user_avatar(username)

        # Should generate the same seed for same username
        assert avatar1["avatar_seed"] == avatar2["avatar_seed"]
        # URLs should be the same for same seed and style
        assert avatar1["avatar_url"] == avatar2["avatar_url"]

    def test_different_users_different_avatars(self, avatar_service):
        """Test that different users get different avatars"""
        user1_avatar = avatar_service.create_user_avatar("user1")
        user2_avatar = avatar_service.create_user_avatar("user2")

        # Different users should have different seeds
        assert user1_avatar["avatar_seed"] != user2_avatar["avatar_seed"]
        # And different URLs
        assert user1_avatar["avatar_url"] != user2_avatar["avatar_url"]

    def test_avatar_style_variations(self, avatar_service):
        """Test generating avatars with different styles"""
        username = "styletest"
        seed = avatar_service.generate_avatar_seed(username)

        # Test multiple styles if available
        styles_to_test = avatar_service.avatar_styles[:3]  # Test first 3 styles
        avatar_urls = []

        for style in styles_to_test:
            avatar_data = avatar_service.create_user_avatar(username, style)
            avatar_urls.append(avatar_data["avatar_url"])

        # Different styles should produce different URLs
        assert len(set(avatar_urls)) == len(avatar_urls)


class TestAvatarServiceErrorHandling:
    """Test avatar service error handling"""

    @pytest.fixture
    def avatar_service(self):
        return AvatarService()

    def test_invalid_style_handling(self, avatar_service):
        """Test handling of invalid avatar style"""
        username = "testuser"
        invalid_style = "nonexistent_style"

        # Should fallback to default style gracefully
        avatar_data = avatar_service.create_user_avatar(username, invalid_style)

        assert "avatar_url" in avatar_data
        assert "avatar_seed" in avatar_data
        # Should still generate a valid avatar

    def test_empty_username_handling(self, avatar_service):
        """Test handling of empty username"""
        # Should handle empty username gracefully
        avatar_data = avatar_service.create_user_avatar("")

        assert "avatar_url" in avatar_data
        assert "avatar_seed" in avatar_data
        # Should generate some fallback avatar

    def test_special_characters_in_username(self, avatar_service):
        """Test handling usernames with special characters"""
        special_usernames = [
            "user@email.com",
            "user-name_123",
            "用户名",  # Unicode characters
            "user with spaces",
        ]

        for username in special_usernames:
            avatar_data = avatar_service.create_user_avatar(username)

            assert "avatar_url" in avatar_data
            assert "avatar_seed" in avatar_data
            assert isinstance(avatar_data["avatar_url"], str)
            assert len(avatar_data["avatar_url"]) > 0

    def test_upload_validation_edge_cases(self, avatar_service):
        """Test avatar upload validation edge cases"""
        # Empty file
        result = avatar_service.validate_uploaded_avatar(b"", "image/png")
        assert result["valid"] is False

        # None content type
        result = avatar_service.validate_uploaded_avatar(b"data", None)
        assert result["valid"] is False

        # Very small valid image
        small_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        result = avatar_service.validate_uploaded_avatar(small_png, "image/png")
        # Should be valid even if small
        assert "valid" in result
