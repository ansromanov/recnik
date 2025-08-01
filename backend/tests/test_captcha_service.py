"""
Tests for CAPTCHA service functionality
"""

import pytest
from unittest.mock import Mock, patch
import requests
from services.captcha_service import CaptchaService


class TestCaptchaService:
    """Test cases for CaptchaService"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch("services.captcha_service.RECAPTCHA_SECRET_KEY", "test-secret-key"):
            self.captcha_service = CaptchaService()
            self.captcha_service.secret_key = "test-secret-key"

    def test_verify_captcha_success(self):
        """Test successful CAPTCHA verification"""
        with patch("services.captcha_service.requests.post") as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.json.return_value = {
                "success": True,
                "score": 0.9,
                "action": "login",
                "hostname": "localhost",
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = self.captcha_service.verify_captcha("valid-token", "127.0.0.1")

            assert result["success"] is True
            assert result["score"] == 0.9
            assert result["action"] == "login"
            assert result["hostname"] == "localhost"

    def test_verify_captcha_failure(self):
        """Test failed CAPTCHA verification"""
        with patch("services.captcha_service.requests.post") as mock_post:
            # Mock failed response
            mock_response = Mock()
            mock_response.json.return_value = {
                "success": False,
                "error-codes": ["invalid-input-response"],
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = self.captcha_service.verify_captcha("invalid-token")

            assert result["success"] is False
            assert "CAPTCHA verification failed" in result["error"]
            assert result["error_codes"] == ["invalid-input-response"]

    def test_verify_captcha_missing_response(self):
        """Test CAPTCHA verification with missing response"""
        result = self.captcha_service.verify_captcha("")

        assert result["success"] is False
        assert result["error"] == "CAPTCHA response is required"

    def test_verify_captcha_missing_secret_key(self):
        """Test CAPTCHA verification with missing secret key"""
        captcha_service = CaptchaService()
        captcha_service.secret_key = None

        result = captcha_service.verify_captcha("some-token")

        assert result["success"] is False
        assert result["error"] == "reCAPTCHA not configured on server"

    def test_verify_captcha_network_error(self):
        """Test CAPTCHA verification with network error"""
        with patch("services.captcha_service.requests.post") as mock_post:
            mock_post.side_effect = requests.RequestException("Network error")

            result = self.captcha_service.verify_captcha("some-token")

            assert result["success"] is False
            assert result["error"] == "Failed to verify CAPTCHA"

    def test_get_error_message(self):
        """Test error message mapping"""
        # Test known error codes
        assert (
            self.captcha_service._get_error_message(["missing-input-response"])
            == "Please complete the CAPTCHA"
        )
        assert (
            self.captcha_service._get_error_message(["invalid-input-response"])
            == "CAPTCHA verification failed"
        )
        assert (
            self.captcha_service._get_error_message(["timeout-or-duplicate"])
            == "CAPTCHA expired or already used"
        )

        # Test unknown error code
        assert (
            self.captcha_service._get_error_message(["unknown-error"])
            == "CAPTCHA verification failed"
        )

        # Test empty error codes
        assert (
            self.captcha_service._get_error_message([]) == "CAPTCHA verification failed"
        )

    def test_verify_captcha_with_remote_ip(self):
        """Test CAPTCHA verification with remote IP"""
        with patch("services.captcha_service.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            self.captcha_service.verify_captcha("token", "192.168.1.1")

            # Verify that remote IP was included in the request
            call_args = mock_post.call_args
            assert call_args[1]["data"]["remoteip"] == "192.168.1.1"

    def test_verify_captcha_without_remote_ip(self):
        """Test CAPTCHA verification without remote IP"""
        with patch("services.captcha_service.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            self.captcha_service.verify_captcha("token")

            # Verify that remote IP was not included in the request
            call_args = mock_post.call_args
            assert "remoteip" not in call_args[1]["data"]
