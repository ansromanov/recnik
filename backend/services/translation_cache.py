"""
Translation Cache Service
Provides intelligent caching for word translations to dramatically improve performance
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TranslationCache:
    """
    High-performance translation cache with intelligent cache management
    """

    def __init__(self, redis_client, ttl=30 * 24 * 3600):
        self.redis = redis_client
        self.ttl = ttl  # 30 days default
        self.prefix = "translation:"
        self.stats_prefix = "translation_stats:"

        # Initialize cache statistics
        self._init_stats()

    def _init_stats(self):
        """Initialize cache statistics tracking"""
        stats_key = f"{self.stats_prefix}initialized"
        if not self.redis.exists(stats_key):
            self.redis.hset(
                "translation_cache_stats",
                mapping={
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_translations": 0,
                    "last_reset": int(time.time()),
                },
            )
            self.redis.set(stats_key, "1", ex=24 * 3600)  # Reset daily

    def _generate_key(self, word: str) -> str:
        """Generate a consistent cache key for the word"""
        # Normalize the word (lowercase, strip whitespace)
        normalized_word = word.lower().strip()
        hash_key = hashlib.md5(normalized_word.encode("utf-8")).hexdigest()
        return f"{self.prefix}{hash_key}"

    def _update_stats(self, hit: bool):
        """Update cache statistics"""
        try:
            if hit:
                self.redis.hincrby("translation_cache_stats", "cache_hits", 1)
            else:
                self.redis.hincrby("translation_cache_stats", "cache_misses", 1)
        except Exception as e:
            logger.warning(f"Failed to update cache stats: {e}")

    def get(self, word: str) -> Optional[dict[Any, Any]]:
        """
        Get cached translation for a word

        Args:
            word: The word to get translation for

        Returns:
            Cached translation data or None if not found
        """
        try:
            cache_key = self._generate_key(word)
            cached_data = self.redis.get(cache_key)

            if cached_data:
                self._update_stats(hit=True)
                result = json.loads(cached_data)

                # Update access time for LRU tracking
                result["last_accessed"] = int(time.time())
                self.redis.setex(cache_key, self.ttl, json.dumps(result))

                logger.debug(f"Cache HIT for word: {word}")
                return result
            else:
                self._update_stats(hit=False)
                logger.debug(f"Cache MISS for word: {word}")
                return None

        except Exception as e:
            logger.error(f"Error getting cached translation for '{word}': {e}")
            self._update_stats(hit=False)
            return None

    def set(self, word: str, translation_data: dict[Any, Any]) -> bool:
        """
        Cache translation data for a word

        Args:
            word: The word to cache translation for
            translation_data: Translation result to cache

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            cache_key = self._generate_key(word)

            # Add metadata to cached data
            enhanced_data = {
                **translation_data,
                "cached_at": int(time.time()),
                "cache_version": "1.0",
                "word_normalized": word.lower().strip(),
            }

            # Cache the data
            success = self.redis.setex(cache_key, self.ttl, json.dumps(enhanced_data))

            if success:
                self.redis.hincrby("translation_cache_stats", "total_translations", 1)
                logger.debug(f"Successfully cached translation for word: {word}")
            else:
                logger.warning(f"Failed to cache translation for word: {word}")

            return bool(success)

        except Exception as e:
            logger.error(f"Error caching translation for '{word}': {e}")
            return False

    def get_batch(self, words: list[str]) -> dict[str, Optional[dict[Any, Any]]]:
        """
        Get cached translations for multiple words in a single operation

        Args:
            words: List of words to get translations for

        Returns:
            Dictionary mapping words to their cached translations (None if not cached)
        """
        if not words:
            return {}

        try:
            # Generate cache keys for all words
            word_to_key = {word: self._generate_key(word) for word in words}
            cache_keys = list(word_to_key.values())

            # Get all cached values in one operation
            cached_values = self.redis.mget(cache_keys)

            results = {}
            for word, cached_value in zip(words, cached_values):
                if cached_value:
                    try:
                        translation_data = json.loads(cached_value)
                        translation_data["last_accessed"] = int(time.time())

                        # Update the cache with new access time
                        cache_key = word_to_key[word]
                        self.redis.setex(cache_key, self.ttl, json.dumps(translation_data))

                        results[word] = translation_data
                        self._update_stats(hit=True)
                    except json.JSONDecodeError:
                        results[word] = None
                        self._update_stats(hit=False)
                else:
                    results[word] = None
                    self._update_stats(hit=False)

            hit_count = sum(1 for result in results.values() if result is not None)
            logger.info(f"Batch cache lookup: {hit_count}/{len(words)} hits")

            return results

        except Exception as e:
            logger.error(f"Error in batch cache lookup: {e}")
            return dict.fromkeys(words)

    def set_batch(self, translations: dict[str, dict[Any, Any]]) -> int:
        """
        Cache multiple translations in a single operation

        Args:
            translations: Dictionary mapping words to their translation data

        Returns:
            Number of successfully cached translations
        """
        if not translations:
            return 0

        try:
            # Prepare all cache operations
            pipe = self.redis.pipeline()

            for word, translation_data in translations.items():
                cache_key = self._generate_key(word)

                enhanced_data = {
                    **translation_data,
                    "cached_at": int(time.time()),
                    "cache_version": "1.0",
                    "word_normalized": word.lower().strip(),
                }

                pipe.setex(cache_key, self.ttl, json.dumps(enhanced_data))

            # Execute all cache operations
            results = pipe.execute()

            # Update statistics
            successful_caches = sum(1 for result in results if result)
            self.redis.hincrby("translation_cache_stats", "total_translations", successful_caches)

            logger.info(f"Batch cache set: {successful_caches}/{len(translations)} successful")
            return successful_caches

        except Exception as e:
            logger.error(f"Error in batch cache set: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache performance statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            stats_raw = self.redis.hgetall("translation_cache_stats")

            # Convert bytes keys/values to strings if needed (for fakeredis compatibility)
            stats = {}
            for k, v in stats_raw.items():
                key = k.decode() if isinstance(k, bytes) else k
                value = v.decode() if isinstance(v, bytes) else v
                stats[key] = value

            # Convert string values to integers
            for key in [
                "cache_hits",
                "cache_misses",
                "total_translations",
                "last_reset",
            ]:
                if key in stats:
                    stats[key] = int(stats.get(key, 0))

            # Calculate derived statistics
            total_requests = stats.get("cache_hits", 0) + stats.get("cache_misses", 0)
            hit_rate = (stats.get("cache_hits", 0) / max(1, total_requests)) * 100

            # Get cache size information
            cache_keys = self.redis.keys(f"{self.prefix}*")
            cache_size = len(cache_keys)

            # Estimate memory usage (rough approximation)
            sample_size = min(10, len(cache_keys))
            if sample_size > 0:
                sample_keys = cache_keys[:sample_size]
                total_sample_memory = sum(len(self.redis.get(key) or "") for key in sample_keys)
                avg_memory_per_key = total_sample_memory / sample_size
                estimated_total_memory = avg_memory_per_key * cache_size
            else:
                estimated_total_memory = 0

            return {
                **stats,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
                "cache_size": cache_size,
                "estimated_memory_mb": round(estimated_total_memory / (1024 * 1024), 2),
                "cache_efficiency": (
                    "Excellent" if hit_rate > 80 else "Good" if hit_rate > 60 else "Poor"
                ),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "error": str(e),
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate_percent": 0.0,
            }

    def clear_stats(self):
        """Reset cache statistics"""
        try:
            self.redis.hset(
                "translation_cache_stats",
                mapping={
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "total_translations": 0,
                    "last_reset": int(time.time()),
                },
            )
            logger.info("Cache statistics reset")
        except Exception as e:
            logger.error(f"Error clearing cache stats: {e}")

    def clear_cache(self) -> int:
        """
        Clear all cached translations

        Returns:
            Number of cache entries cleared
        """
        try:
            cache_keys = self.redis.keys(f"{self.prefix}*")
            if cache_keys:
                deleted_count = self.redis.delete(*cache_keys)
                logger.info(f"Cleared {deleted_count} cache entries")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    def warm_cache(self, word_translations: dict[str, dict[Any, Any]]) -> int:
        """
        Pre-populate cache with known translations (cache warming)

        Args:
            word_translations: Dictionary of word -> translation data

        Returns:
            Number of entries warmed
        """
        logger.info(f"Warming cache with {len(word_translations)} translations")
        return self.set_batch(word_translations)

    def cleanup_old_entries(self, max_age_days: int = 60) -> int:
        """
        Clean up old cache entries that haven't been accessed recently

        Args:
            max_age_days: Maximum age in days for cache entries

        Returns:
            Number of entries cleaned up
        """
        try:
            cutoff_time = int(time.time()) - (max_age_days * 24 * 3600)
            cache_keys = self.redis.keys(f"{self.prefix}*")

            old_keys = []
            for key in cache_keys:
                try:
                    cached_data = self.redis.get(key)
                    if cached_data:
                        data = json.loads(cached_data)
                        last_accessed = data.get("last_accessed", data.get("cached_at", 0))
                        if last_accessed < cutoff_time:
                            old_keys.append(key)
                except:
                    # If we can't parse the data, consider it for cleanup
                    old_keys.append(key)

            if old_keys:
                deleted_count = self.redis.delete(*old_keys)
                logger.info(f"Cleaned up {deleted_count} old cache entries")
                return deleted_count

            return 0

        except Exception as e:
            logger.error(f"Error cleaning up old cache entries: {e}")
            return 0
