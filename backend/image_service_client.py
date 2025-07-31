import json
import hashlib
import time
from datetime import datetime


class ImageServiceClient:
    """
    Simplified image service client that communicates with the separate image sync service
    through Redis. This replaces the heavy image processing logic in the backend.
    """

    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.background_queue_key = "image_queue"

    def _generate_cache_key(self, word):
        """Generate a cache key for the word"""
        return f"word_image:{hashlib.md5(word.lower().encode()).hexdigest()}"

    def get_word_image(self, serbian_word, english_translation=None):
        """
        Get an image for a word - returns cached if available, queues for background if not.
        This is the main method used by the backend API.
        """
        cache_key = self._generate_cache_key(serbian_word)

        # Try to get from cache first
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                cached_result = json.loads(cached_data)
                if "error" not in cached_result:
                    return cached_result
                else:
                    # If it was a cached failure, check if enough time has passed to retry
                    cached_at = cached_result.get("cached_at", 0)
                    if time.time() - cached_at < 24 * 60 * 60:  # 24 hours
                        return None  # Don't retry failed searches too soon
        except Exception as e:
            print(f"Error reading from Redis cache: {e}")

        # Not in cache or cache expired, add to background queue
        self._add_to_background_queue(serbian_word, english_translation)

        # Return immediately - image will be available later
        return None

    def _add_to_background_queue(self, serbian_word, english_translation=None):
        """Add word to background processing queue for the image sync service"""
        try:
            queue_item = {
                "serbian_word": serbian_word,
                "english_translation": english_translation,
                "added_at": int(time.time()),
            }
            self.redis_client.lpush(self.background_queue_key, json.dumps(queue_item))
            print(f"Queued {serbian_word} for image processing")
        except Exception as e:
            print(f"Error adding {serbian_word} to queue: {e}")

    def populate_images_for_words(self, words_list):
        """Add a list of words to the background processing queue"""
        added_count = 0

        for word_data in words_list:
            if isinstance(word_data, dict):
                serbian_word = word_data.get("serbian_word")
                english_translation = word_data.get("english_translation")
            else:
                serbian_word = word_data
                english_translation = None

            if serbian_word:
                # Check if already cached
                cache_key = self._generate_cache_key(serbian_word)
                try:
                    cached_data = self.redis_client.get(cache_key)
                    if cached_data:
                        continue  # Already have this word
                except:
                    pass

                self._add_to_background_queue(serbian_word, english_translation)
                added_count += 1

        print(f"Added {added_count} words to image processing queue")
        return added_count

    def get_background_status(self):
        """Get status of background processing from the image sync service"""
        try:
            queue_length = self.redis_client.llen(self.background_queue_key)

            # Check if processing is active by looking for the lock
            processing_lock_key = "image_processing_lock"
            is_processing = bool(self.redis_client.get(processing_lock_key))

            # Get rate limit info from the image sync service
            rate_limit_key = "unsplash_rate_limit"
            current_hour = int(time.time() // 3600)
            rate_key = f"{rate_limit_key}:{current_hour}"
            current_requests = self.redis_client.get(rate_key)
            current_requests = int(current_requests) if current_requests else 0

            return {
                "queue_length": queue_length,
                "requests_this_hour": current_requests,
                "max_requests_per_hour": 25,  # Same as image sync service
                "is_processing": is_processing,
                "service_type": "separate_image_sync_service",
            }
        except Exception as e:
            return {"error": str(e)}

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

            cache_info = {
                "total_cached_words": total_keys,
                "cache_size_mb": 0,
                "successful_caches": 0,
                "failed_caches": 0,
                "service_type": "separate_image_sync_service",
            }

            if keys:
                # Sample some keys to estimate cache stats
                import random

                sample_size = min(20, len(keys))
                sample_keys = random.sample(keys, sample_size)
                total_sample_size = 0
                successful_caches = 0
                failed_caches = 0

                for key in sample_keys:
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            total_sample_size += len(data)
                            try:
                                parsed_data = json.loads(data)
                                if "error" in parsed_data:
                                    failed_caches += 1
                                else:
                                    successful_caches += 1
                            except:
                                pass
                    except:
                        continue

                if total_sample_size > 0:
                    avg_size = total_sample_size / sample_size
                    estimated_total_size = avg_size * total_keys
                    cache_info["cache_size_mb"] = round(
                        estimated_total_size / (1024 * 1024), 2
                    )

                # Extrapolate success/failure rates
                if sample_size > 0:
                    success_rate = successful_caches / sample_size
                    cache_info["successful_caches"] = int(total_keys * success_rate)
                    cache_info["failed_caches"] = (
                        total_keys - cache_info["successful_caches"]
                    )

            return cache_info
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def clear_all_cache(self):
        """Clear all cached images"""
        try:
            keys = self.redis_client.keys("word_image:*")
            if keys:
                self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            print(f"Error clearing all cache: {e}")
            return 0

    # For compatibility with the old interface, these methods queue requests
    def get_word_image_immediate(self, serbian_word, english_translation=None):
        """
        Legacy method for immediate image processing.
        Now just queues the request and returns cached result if available.
        """
        # First try to get from cache
        result = self.get_word_image(serbian_word, english_translation)
        if result:
            return result

        # If not in cache, it's been queued. Return status message.
        return {
            "error": "Image processing queued. The image will be available shortly via the separate image sync service."
        }
