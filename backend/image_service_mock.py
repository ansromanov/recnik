import base64
import hashlib
import io
import json
import random
import time

from PIL import Image, ImageDraw, ImageFont


class MockImageService:
    """Mock image service that generates simple placeholder images with text"""

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def _generate_cache_key(self, word):
        """Generate a cache key for the word"""
        return f"word_image:{hashlib.md5(word.lower().encode()).hexdigest()}"

    def _generate_placeholder_image(self, word, translation):
        """Generate a simple placeholder image with the word text"""
        # Create a 300x200 image
        width, height = 300, 200

        # Random pastel colors
        colors = [
            (255, 182, 193),  # Light pink
            (173, 216, 230),  # Light blue
            (144, 238, 144),  # Light green
            (255, 218, 185),  # Peach
            (221, 160, 221),  # Plum
            (255, 255, 224),  # Light yellow
            (230, 230, 250),  # Lavender
        ]

        # Select color based on word hash for consistency
        color_index = hash(word) % len(colors)
        bg_color = colors[color_index]

        # Create image
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fall back to default if not available
        try:
            # Try different font sizes
            font_size = 24
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        # Draw the Serbian word (larger)
        serbian_text = word
        # Get text bounding box
        bbox = draw.textbbox((0, 0), serbian_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Center the Serbian word
        x = (width - text_width) // 2
        y = height // 3 - text_height // 2
        draw.text((x, y), serbian_text, fill=(50, 50, 50), font=font)

        # Draw the English translation (smaller, below)
        english_text = f"({translation})"
        bbox_en = draw.textbbox((0, 0), english_text, font=font)
        text_width_en = bbox_en[2] - bbox_en[0]

        x_en = (width - text_width_en) // 2
        y_en = height * 2 // 3
        draw.text((x_en, y_en), english_text, fill=(80, 80, 80), font=font)

        # Add a simple border
        draw.rectangle([0, 0, width - 1, height - 1], outline=(100, 100, 100), width=2)

        # Convert to base64
        output = io.BytesIO()
        img.save(output, format="PNG", optimize=True)
        image_data = output.getvalue()

        return {
            "data": base64.b64encode(image_data).decode("utf-8"),
            "content_type": "image/png",
            "width": width,
            "height": height,
            "size": len(image_data),
        }

    def get_word_image(self, serbian_word, english_translation=None):
        """Get an image for a word - generates a placeholder"""
        cache_key = self._generate_cache_key(serbian_word)

        # Try to get from cache first
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Error reading from Redis cache: {e}")

        # Generate placeholder image
        try:
            processed_image = self._generate_placeholder_image(
                serbian_word, english_translation or serbian_word
            )

            image_data = {
                "image_data": processed_image["data"],
                "content_type": processed_image["content_type"],
                "width": processed_image["width"],
                "height": processed_image["height"],
                "size": processed_image["size"],
                "search_query": f"placeholder for {serbian_word}",
                "cached_at": int(time.time()),
                "is_placeholder": True,
            }

            # Cache the result for 7 days
            try:
                self.redis_client.setex(cache_key, 7 * 24 * 60 * 60, json.dumps(image_data))
            except Exception as e:
                print(f"Error writing to Redis cache: {e}")

            return image_data

        except Exception as e:
            print(f"Error generating placeholder image: {e}")
            return {
                "error": f"Failed to generate image: {e!s}",
                "cached_at": int(time.time()),
            }

    def clear_word_image_cache(self, serbian_word):
        """Clear cached image for a specific word"""
        cache_key = self._generate_cache_key(serbian_word)
        try:
            self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            print(f"Error clearing cache for word '{serbian_word}': {e}")
            return False

    def get_cache_stats(self):
        """Get statistics about the image cache"""
        try:
            keys = self.redis_client.keys("word_image:*")
            total_keys = len(keys)

            cache_info = {"total_cached_words": total_keys, "cache_size_mb": 0}

            # Sample a few keys to estimate cache size
            if keys:
                sample_size = min(10, len(keys))
                sample_keys = random.sample(keys, sample_size)
                total_sample_size = 0

                for key in sample_keys:
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            total_sample_size += len(data)
                    except:
                        continue

                if total_sample_size > 0:
                    avg_size = total_sample_size / sample_size
                    estimated_total_size = avg_size * total_keys
                    cache_info["cache_size_mb"] = round(estimated_total_size / (1024 * 1024), 2)

            return cache_info
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}
