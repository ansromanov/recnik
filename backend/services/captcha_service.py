"""
CAPTCHA verification service for reCAPTCHA integration
"""

import logging

import requests

from config import RECAPTCHA_SECRET_KEY, RECAPTCHA_VERIFY_URL

logger = logging.getLogger(__name__)


class CaptchaService:
    """Service for verifying reCAPTCHA responses"""

    def __init__(self):
        self.secret_key = RECAPTCHA_SECRET_KEY
        self.verify_url = RECAPTCHA_VERIFY_URL

    def verify_captcha(self, captcha_response, remote_ip=None):
        """
        Verify reCAPTCHA response with Google's API

        Args:
            captcha_response (str): The reCAPTCHA response token from the frontend
            remote_ip (str, optional): The user's IP address

        Returns:
            dict: Verification result with success status and details
        """
        if not self.secret_key:
            logger.warning("reCAPTCHA secret key not configured")
            return {"success": False, "error": "reCAPTCHA not configured on server"}

        if not captcha_response:
            return {"success": False, "error": "CAPTCHA response is required"}

        try:
            # Prepare verification data
            verify_data = {"secret": self.secret_key, "response": captcha_response}

            if remote_ip:
                verify_data["remoteip"] = remote_ip

            # Send verification request to Google
            response = requests.post(self.verify_url, data=verify_data, timeout=10)

            response.raise_for_status()
            result = response.json()

            logger.info(f"reCAPTCHA verification result: {result}")

            if result.get("success"):
                return {
                    "success": True,
                    "score": result.get("score"),  # For v3 captcha
                    "action": result.get("action"),  # For v3 captcha
                    "hostname": result.get("hostname"),
                }
            else:
                error_codes = result.get("error-codes", [])
                error_message = self._get_error_message(error_codes)

                return {
                    "success": False,
                    "error": error_message,
                    "error_codes": error_codes,
                }

        except requests.RequestException as e:
            logger.error(f"Error verifying reCAPTCHA: {e}")
            return {"success": False, "error": "Failed to verify CAPTCHA"}
        except Exception as e:
            logger.error(f"Unexpected error in CAPTCHA verification: {e}")
            return {"success": False, "error": "CAPTCHA verification failed"}

    def _get_error_message(self, error_codes):
        """
        Convert reCAPTCHA error codes to user-friendly messages

        Args:
            error_codes (list): List of error codes from reCAPTCHA API

        Returns:
            str: User-friendly error message
        """
        error_messages = {
            "missing-input-secret": "Server configuration error",
            "invalid-input-secret": "Server configuration error",
            "missing-input-response": "Please complete the CAPTCHA",
            "invalid-input-response": "CAPTCHA verification failed",
            "bad-request": "Invalid CAPTCHA request",
            "timeout-or-duplicate": "CAPTCHA expired or already used",
        }

        if not error_codes:
            return "CAPTCHA verification failed"

        # Return the first recognizable error message
        for code in error_codes:
            if code in error_messages:
                return error_messages[code]

        return "CAPTCHA verification failed"


# Create a global instance
captcha_service = CaptchaService()
