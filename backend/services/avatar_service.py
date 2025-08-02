import hashlib
import random
import string
from typing import Optional, Dict, Any
import requests
from datetime import datetime


class AvatarService:
    """Service for generating and managing user avatars"""

    def __init__(self):
        # DiceBear API for AI-generated avatars
        self.dicebear_base_url = "https://api.dicebear.com/7.x"

        # Available avatar styles
        self.avatar_styles = [
            "avataaars",  # Cartoon-style avatars
            "big-smile",  # Simple smiley faces
            "bottts",  # Robot-style avatars
            "fun-emoji",  # Emoji-style avatars
            "identicon",  # Geometric patterns
            "initials",  # Letter-based avatars
            "lorelei",  # Illustrated female avatars
            "micah",  # Illustrated male avatars
            "miniavs",  # Minimal avatars
            "open-peeps",  # Hand-drawn style avatars
            "personas",  # Professional avatars
            "pixel-art",  # 8-bit style avatars
        ]

        # Default style preferences
        self.default_style = "avataaars"
        self.fallback_style = "initials"

    def generate_avatar_seed(self, username: str) -> str:
        """Generate a unique seed for avatar generation based on username"""
        # Use only username for deterministic seed generation
        # This ensures same username always generates same seed
        seed = hashlib.md5(username.encode()).hexdigest()[:16]

        return seed

    def get_avatar_url(
        self, seed: str, style: Optional[str] = None, size: int = 128
    ) -> str:
        """Generate avatar URL using DiceBear API"""
        if not style or style not in self.avatar_styles:
            style = self.default_style

        # Build avatar URL with parameters
        params = {
            "seed": seed,
            "size": size,
            "backgroundColor": "transparent",
            "format": "svg",
        }

        # Add style-specific options
        if style == "avataaars":
            params.update(
                {
                    "accessoriesChance": 30,
                    "facialHairChance": 20,
                    "clothingGraphic": "bear,cumbia,deer,diamond,hola,pizza,resist,selena,skull,skull-outline,bear",
                }
            )
        elif style == "initials":
            params.update(
                {
                    "backgroundColor": "b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf",
                    "textColor": "1e40af,7c3aed,dc2626,ea580c,eab308",
                }
            )
        elif style == "big-smile":
            params.update(
                {
                    "backgroundColor": "fbbf24,f59e0b,d97706,dc2626,7c3aed,3b82f6",
                }
            )

        # Build URL
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        avatar_url = f"{self.dicebear_base_url}/{style}/svg?{param_string}"

        return avatar_url

    def get_random_avatar_style(self) -> str:
        """Get a random avatar style"""
        return random.choice(self.avatar_styles)

    def create_user_avatar(
        self, username: str, style: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new avatar for a user"""
        # Generate unique seed
        seed = self.generate_avatar_seed(username)

        # Use provided style or default style for consistency
        if not style:
            style = self.default_style

        # Generate avatar URL
        avatar_url = self.get_avatar_url(seed, style)

        return {
            "avatar_url": avatar_url,
            "avatar_type": "ai_generated",
            "avatar_seed": seed,
            "avatar_style": style,
        }

    def regenerate_avatar(
        self,
        username: str,
        style: Optional[str] = None,
        keep_seed: bool = False,
        current_seed: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Regenerate avatar for a user"""
        # Use existing seed or generate new one
        if keep_seed and current_seed:
            seed = current_seed
        else:
            # Generate a new random seed when not keeping the current one
            import time

            random_part = str(int(time.time() * 1000000))  # microsecond timestamp
            seed = hashlib.md5((username + random_part).encode()).hexdigest()[:16]

        # Use provided style or select random one
        if not style:
            style = self.get_random_avatar_style()

        # Generate new avatar URL
        avatar_url = self.get_avatar_url(seed, style)

        return {
            "avatar_url": avatar_url,
            "avatar_type": "ai_generated",
            "avatar_seed": seed,
            "avatar_style": style,
        }

    def get_avatar_variations(self, seed: str, count: int = 6) -> list:
        """Get multiple avatar variations for user to choose from"""
        variations = []

        # Get variations with different styles
        styles_to_use = random.sample(
            self.avatar_styles, min(count, len(self.avatar_styles))
        )

        for style in styles_to_use:
            avatar_url = self.get_avatar_url(seed, style)
            variations.append(
                {
                    "style": style,
                    "avatar_url": avatar_url,
                    "style_name": style.replace("-", " ").title(),
                }
            )

        return variations

    def validate_uploaded_avatar(
        self, file_data: bytes, content_type: str
    ) -> Dict[str, Any]:
        """Validate uploaded avatar file"""
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if len(file_data) > max_size:
            return {
                "valid": False,
                "error": "File size too large. Maximum allowed size is 5MB.",
            }

        # Check content type
        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]
        if content_type not in allowed_types:
            return {
                "valid": False,
                "error": f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
            }

        # Basic file signature validation
        if content_type in ["image/jpeg", "image/jpg"]:
            if not file_data.startswith(b"\xff\xd8\xff"):
                return {"valid": False, "error": "Invalid JPEG file"}
        elif content_type == "image/png":
            if not file_data.startswith(b"\x89PNG\r\n\x1a\n"):
                return {"valid": False, "error": "Invalid PNG file"}
        elif content_type == "image/gif":
            if not file_data.startswith(b"GIF"):
                return {"valid": False, "error": "Invalid GIF file"}
        elif content_type == "image/webp":
            if not (b"WEBP" in file_data[:20]):
                return {"valid": False, "error": "Invalid WebP file"}

        return {"valid": True, "size": len(file_data), "content_type": content_type}

    def get_initials_avatar(
        self, username: str, background_color: Optional[str] = None
    ) -> str:
        """Generate simple initials-based avatar as fallback"""
        # Extract initials from username
        initials = username[:2].upper() if len(username) >= 2 else username.upper()

        # Use initials as seed
        seed = hashlib.md5(initials.encode()).hexdigest()[:8]

        # Generate avatar URL
        avatar_url = self.get_avatar_url(seed, "initials")

        return avatar_url

    def get_default_avatar(self, username: str) -> Dict[str, Any]:
        """Get default avatar for new users"""
        return self.create_user_avatar(username, self.default_style)


# Global avatar service instance
avatar_service = AvatarService()
