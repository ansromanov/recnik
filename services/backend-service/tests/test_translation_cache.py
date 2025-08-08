"""
Unit tests for TranslationCache service
"""

import json
import os
import sys
import time
from unittest.mock import MagicMock

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.translation_cache import TranslationCache


class TestTranslationCache:
    """Test TranslationCache unit functionality"""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        mock_redis = MagicMock()
        mock_redis.exists.return_value = False
        mock_redis.hset.return_value = True
        mock_redis.set.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.hincrby.return_value = 1
        mock_redis.hgetall.return_value = {
            "cache_hits": "10",
            "cache_misses": "5",
            "total_translations": "15",
            "last_reset": str(int(time.time())),
        }
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = 0
        mock_redis.mget.return_value = []
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.execute.return_value = [True, True, True]
        return mock_redis

    @pytest.fixture
    def translation_cache(self, mock_redis_client):
        """Create TranslationCache instance with mock Redis"""
        return TranslationCache(mock_redis_client, ttl=3600)

    @pytest.fixture
    def sample_translation_data(self):
        """Sample translation data for testing"""
        return {
            "serbian_word": "raditi",
            "english_translation": "to work",
            "category_id": 2,
            "category_name": "Verbs",
        }

    def test_cache_key_generation(self, translation_cache):
        """Test cache key generation for words"""
        word = "Raditi"  # Mixed case
        cache_key = translation_cache._generate_key(word)

        assert cache_key.startswith("translation:")
        assert len(cache_key) > 20  # Should have hash component

        # Same word (different case) should generate same key
        cache_key2 = translation_cache._generate_key("raditi")
        assert cache_key == cache_key2

        # Different words should generate different keys
        cache_key3 = translation_cache._generate_key("pas")
        assert cache_key != cache_key3

    def test_cache_set_and_get(self, translation_cache, mock_redis_client, sample_translation_data):
        """Test setting and getting cached translations"""
        word = "raditi"

        # Test setting cache
        result = translation_cache.set(word, sample_translation_data)
        assert result is True

        # Verify Redis setex was called
        mock_redis_client.setex.assert_called()

        # Verify stats were updated
        mock_redis_client.hincrby.assert_called_with(
            "translation_cache_stats", "total_translations", 1
        )

    def test_cache_hit_scenario(
        self, translation_cache, mock_redis_client, sample_translation_data
    ):
        """Test cache hit scenario"""
        word = "raditi"

        # Setup cache hit
        cached_data = {
            **sample_translation_data,
            "cached_at": int(time.time()),
            "cache_version": "1.0",
            "word_normalized": word,
        }
        mock_redis_client.get.return_value = json.dumps(cached_data)

        # Get from cache
        result = translation_cache.get(word)

        # Should return cached data
        assert result is not None
        assert result["serbian_word"] == "raditi"
        assert result["english_translation"] == "to work"
        assert "last_accessed" in result

        # Should update hit stats
        mock_redis_client.hincrby.assert_called_with("translation_cache_stats", "cache_hits", 1)

    def test_cache_miss_scenario(self, translation_cache, mock_redis_client):
        """Test cache miss scenario"""
        word = "nepoznata_rec"

        # Setup cache miss
        mock_redis_client.get.return_value = None

        # Get from cache
        result = translation_cache.get(word)

        # Should return None
        assert result is None

        # Should update miss stats
        mock_redis_client.hincrby.assert_called_with("translation_cache_stats", "cache_misses", 1)

    def test_batch_operations(self, translation_cache, mock_redis_client):
        """Test batch get and set operations"""
        words = ["raditi", "pas", "velik"]

        # Test batch get with mixed results
        cached_translation = {
            "serbian_word": "raditi",
            "english_translation": "to work",
            "cached_at": int(time.time()),
        }
        mock_redis_client.mget.return_value = [
            json.dumps(cached_translation),  # raditi cached
            None,  # pas not cached
            None,  # velik not cached
        ]

        results = translation_cache.get_batch(words)

        # Should return results for all words
        assert len(results) == 3
        assert results["raditi"] is not None
        assert results["pas"] is None
        assert results["velik"] is None

        # Test batch set
        translations = {
            "pas": {"serbian_word": "pas", "english_translation": "dog"},
            "velik": {"serbian_word": "velik", "english_translation": "big"},
        }

        mock_redis_client.execute.return_value = [True, True]  # Both successful

        cached_count = translation_cache.set_batch(translations)

        # Should return number of successful caches
        assert cached_count == 2

        # Should use pipeline for batch operations
        mock_redis_client.pipeline.assert_called()

    def test_cache_statistics(self, translation_cache, mock_redis_client):
        """Test cache statistics calculation"""
        # Setup mock stats data
        mock_redis_client.hgetall.return_value = {
            "cache_hits": "20",
            "cache_misses": "5",
            "total_translations": "25",
            "last_reset": str(int(time.time())),
        }
        mock_redis_client.keys.return_value = ["key1", "key2", "key3"]  # 3 cache entries
        mock_redis_client.get.side_effect = [
            "data1",
            "data2",
            "data3",
        ]  # Sample data for memory estimation

        stats = translation_cache.get_stats()

        # Check basic stats
        assert stats["cache_hits"] == 20
        assert stats["cache_misses"] == 5
        assert stats["total_requests"] == 25
        assert stats["hit_rate_percent"] == 80.0  # 20/25 * 100
        assert stats["cache_size"] == 3

        # Check efficiency rating (80% hit rate should be "Good", >80% is "Excellent")
        assert stats["cache_efficiency"] in ["Good", "Excellent"]  # 80% hit rate

    def test_cache_cleanup_operations(self, translation_cache, mock_redis_client):
        """Test cache cleanup and maintenance operations"""
        # Test clear cache
        mock_redis_client.keys.return_value = ["translation:key1", "translation:key2"]
        mock_redis_client.delete.return_value = 2

        cleared_count = translation_cache.clear_cache()
        assert cleared_count == 2

        # Test clear stats
        translation_cache.clear_stats()
        mock_redis_client.hset.assert_called_with(
            "translation_cache_stats",
            mapping={
                "cache_hits": 0,
                "cache_misses": 0,
                "total_translations": 0,
                "last_reset": int(time.time()),
            },
        )

    def test_cache_warming(self, translation_cache, mock_redis_client):
        """Test cache warming functionality"""
        word_translations = {
            "raditi": {"serbian_word": "raditi", "english_translation": "to work"},
            "pas": {"serbian_word": "pas", "english_translation": "dog"},
            "velik": {"serbian_word": "velik", "english_translation": "big"},
        }

        mock_redis_client.execute.return_value = [True, True, True]  # All successful

        warmed_count = translation_cache.warm_cache(word_translations)

        # Should warm all entries
        assert warmed_count == 3

        # Should use batch operations
        mock_redis_client.pipeline.assert_called()

    def test_error_handling(self, translation_cache, mock_redis_client):
        """Test error handling in cache operations"""
        word = "test_word"

        # Test get with Redis error
        mock_redis_client.get.side_effect = Exception("Redis connection error")

        result = translation_cache.get(word)
        assert result is None

        # Should still update miss stats despite error
        mock_redis_client.hincrby.assert_called_with("translation_cache_stats", "cache_misses", 1)

        # Test set with Redis error
        mock_redis_client.setex.side_effect = Exception("Redis connection error")

        success = translation_cache.set(word, {"test": "data"})
        assert success is False

    def test_old_entries_cleanup(self, translation_cache, mock_redis_client):
        """Test cleanup of old cache entries"""
        # Mock old and new cache entries
        old_time = int(time.time()) - (70 * 24 * 3600)  # 70 days old
        new_time = int(time.time()) - (10 * 24 * 3600)  # 10 days old

        mock_redis_client.keys.return_value = ["translation:key1", "translation:key2"]
        mock_redis_client.get.side_effect = [
            json.dumps({"cached_at": old_time, "last_accessed": old_time}),  # Old entry
            json.dumps({"cached_at": new_time, "last_accessed": new_time}),  # New entry
        ]
        mock_redis_client.delete.return_value = 1  # One old entry deleted

        cleaned_count = translation_cache.cleanup_old_entries(max_age_days=60)

        # Should clean up 1 old entry
        assert cleaned_count == 1

        # Should call delete with old keys
        mock_redis_client.delete.assert_called()


class TestTranslationCacheEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.fixture
    def translation_cache(self):
        """Create TranslationCache with mock Redis for edge case testing"""
        mock_redis = MagicMock()
        return TranslationCache(mock_redis)

    def test_empty_batch_operations(self, translation_cache):
        """Test batch operations with empty inputs"""
        # Empty batch get
        results = translation_cache.get_batch([])
        assert results == {}

        # Empty batch set
        cached_count = translation_cache.set_batch({})
        assert cached_count == 0

    def test_invalid_json_handling(self, translation_cache):
        """Test handling of corrupted cache data"""
        mock_redis = translation_cache.redis
        mock_redis.get.return_value = "invalid json data"

        # Should handle JSON decode error gracefully
        result = translation_cache.get("test_word")
        assert result is None

    def test_unicode_word_handling(self, translation_cache):
        """Test handling of Unicode Serbian words"""
        unicode_words = ["čovek", "đak", "žena", "šuma"]

        for word in unicode_words:
            cache_key = translation_cache._generate_key(word)
            assert cache_key.startswith("translation:")
            assert len(cache_key) > 20
