"""
Authentication controller
Handles business logic for user authentication and settings
"""

import uuid
from flask import jsonify
from flask_jwt_extended import create_access_token
from models.user import User, Settings
from models.database import db


class AuthController:
    def __init__(self, logger):
        self.logger = logger

    def register(self, request):
        """Handle user registration"""
        request_id = str(uuid.uuid4())

        try:
            data = request.get_json()
            username = data.get("username", "").strip()
            password = data.get("password", "")

            self.logger.info(
                "Processing registration",
                extra={
                    "request_id": request_id,
                    "username": username,
                    "ip": request.remote_addr,
                },
            )

            if not username or not password:
                self.logger.warning(
                    "Registration failed - missing credentials",
                    extra={"request_id": request_id, "username": username},
                )
                return jsonify({"error": "Username and password are required"}), 400

            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                self.logger.warning(
                    "Registration failed - user exists",
                    extra={"request_id": request_id, "username": username},
                )
                return jsonify({"error": "Username already exists"}), 409

            # Create new user
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Create default settings for the user
            settings = Settings(user_id=user.id)
            db.session.add(settings)
            db.session.commit()

            # Create access token
            access_token = create_access_token(identity=str(user.id))

            self.logger.info(
                "User registered successfully",
                extra={
                    "request_id": request_id,
                    "user_id": user.id,
                    "username": username,
                },
            )

            return jsonify(
                {
                    "message": "User registered successfully",
                    "access_token": access_token,
                    "user": user.to_dict(),
                }
            ), 201

        except Exception as e:
            db.session.rollback()
            self.logger.error(
                "Registration error",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "username": username if "username" in locals() else None,
                },
                exc_info=True,
            )
            return jsonify({"error": "Failed to register user"}), 500

    def login(self, request):
        """Handle user login"""
        request_id = str(uuid.uuid4())

        try:
            data = request.get_json()
            username = data.get("username", "").strip()
            password = data.get("password", "")

            self.logger.info(
                "Processing login",
                extra={
                    "request_id": request_id,
                    "username": username,
                    "ip": request.remote_addr,
                },
            )

            if not username or not password:
                self.logger.warning(
                    "Login failed - missing credentials",
                    extra={"request_id": request_id, "username": username},
                )
                return jsonify({"error": "Username and password are required"}), 400

            # Find user
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                self.logger.warning(
                    "Login failed - invalid credentials",
                    extra={
                        "request_id": request_id,
                        "username": username,
                        "user_found": user is not None,
                    },
                )
                return jsonify({"error": "Invalid username or password"}), 401

            # Create access token
            access_token = create_access_token(identity=str(user.id))

            self.logger.info(
                "User logged in successfully",
                extra={
                    "request_id": request_id,
                    "user_id": user.id,
                    "username": username,
                },
            )

            return jsonify({"access_token": access_token, "user": user.to_dict()})

        except Exception as e:
            self.logger.error(
                "Login error",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "username": username if "username" in locals() else None,
                },
                exc_info=True,
            )
            return jsonify({"error": "Failed to login"}), 500

    def get_current_user(self, user_id):
        """Get current user information"""
        request_id = str(uuid.uuid4())

        try:
            self.logger.info(
                "Getting current user",
                extra={"request_id": request_id, "user_id": user_id},
            )

            user = User.query.get(int(user_id))
            if not user:
                self.logger.warning(
                    "User not found",
                    extra={"request_id": request_id, "user_id": user_id},
                )
                return jsonify({"error": "User not found"}), 404

            return jsonify({"user": user.to_dict()})

        except Exception as e:
            self.logger.error(
                "Get current user error",
                extra={"request_id": request_id, "user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            return jsonify({"error": "Failed to get user info"}), 500

    def get_settings(self, user_id):
        """Get user settings"""
        request_id = str(uuid.uuid4())

        try:
            self.logger.info(
                "Getting user settings",
                extra={"request_id": request_id, "user_id": user_id},
            )

            user = User.query.get(int(user_id))
            if not user or not user.settings:
                self.logger.warning(
                    "Settings not found",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "user_found": user is not None,
                    },
                )
                return jsonify({"error": "Settings not found"}), 404

            return jsonify({"settings": user.settings.to_dict(include_sensitive=True)})

        except Exception as e:
            self.logger.error(
                "Get settings error",
                extra={"request_id": request_id, "user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            return jsonify({"error": "Failed to get settings"}), 500

    def update_settings(self, user_id, request):
        """Update user settings"""
        request_id = str(uuid.uuid4())

        try:
            data = request.get_json()

            self.logger.info(
                "Updating user settings",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "settings_keys": list(data.keys()) if data else [],
                },
            )

            user = User.query.get(int(user_id))
            if not user:
                self.logger.warning(
                    "User not found for settings update",
                    extra={"request_id": request_id, "user_id": user_id},
                )
                return jsonify({"error": "User not found"}), 404

            # Create settings if they don't exist
            if not user.settings:
                user.settings = Settings(user_id=user.id)
                db.session.add(user.settings)

            # Update OpenAI API key if provided
            if "openai_api_key" in data:
                old_key_exists = bool(user.settings.openai_api_key)
                user.settings.openai_api_key = data["openai_api_key"]

                self.logger.info(
                    "Updated OpenAI API key",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "had_key_before": old_key_exists,
                        "has_key_now": bool(data["openai_api_key"]),
                    },
                )

            db.session.commit()

            self.logger.info(
                "Settings updated successfully",
                extra={"request_id": request_id, "user_id": user_id},
            )

            return jsonify(
                {
                    "message": "Settings updated successfully",
                    "settings": user.settings.to_dict(include_sensitive=True),
                }
            )

        except Exception as e:
            db.session.rollback()
            self.logger.error(
                "Update settings error",
                extra={"request_id": request_id, "user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            return jsonify({"error": "Failed to update settings"}), 500
