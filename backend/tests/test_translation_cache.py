"""
Unit tests for Translation Cache service
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from services.translation_cache import TranslationCache


@pytest.mark.unit
@pytest.mark.redis
class TestTranslationCache:
    """Test cases for TranslationCache"""

    def test_init(self, fake_redis):
        """Test cache initialization"""
        cache = TranslationCache(fake_redis, ttl=7200)

        assert cache.redis == fake_redis
        assert cache.ttl == 7200
        assert cache.prefix == "translation:"
        assert cache.stats_prefix == "translation_stats:"

    def test_init_default_ttl(self, fake_redis):
        """Test cache initialization with default TTL"""
        cache = TranslationCache(fake_redis)

        assert cache.ttl == 30 * 24 * 3600  # 30 days

    def test_generate_key(self, translation_cache):
        """Test cache key generation"""
        key1 = translation_cache._generate_key("kuća")
        key2 = translation_cache._generate_key("KUĆA")  # Different case
        key3 = translation_cache._generate_key("  kuća  ")  # With whitespace

        # All should generate the same key (normalized)
        assert key1 == key2 == key3
        assert key1.startswith("translation:")
        assert len(key1) > len("translation:")

    def test_generate_key_different_words(self, translation_cache):
        """Test that different words generate different keys"""
        key1 = translation_cache._generate_key("kuća")
        key2 = translation_cache._generate_key("raditi")

        assert key1 != key2

    def test_set_and_get_translation(self, translation_cache):
        """Test setting and getting a translation"""
        word = "raditi"
        translation_data = {
            "serbian_word": "raditi",
            "english_translation": "to work",
            "category": "Verbs",
        }

        # Set translation
        success = translation_cache.set(word, translation_data)
        assert success is True

        # Get translation
        cached_data = translation_cache.get(word)
        assert cached_data is not None
        assert cached_data["serbian_word"] == "raditi"
        assert cached_data["english_translation"] == "to work"
        assert cached_data["category"] == "Verbs"

        # Should have metadata
        assert "cached_at" in cached_data
        assert "cache_version" in cached_data
        assert cached_data["word_normalized"] == "raditi"

    def test_get_nonexistent_translation(self, translation_cache):
        """Test getting a non-existent translation"""
        cached_data = translation_cache.get("nonexistent")
        assert cached_data is None

    def test_get_updates_access_time(self, translation_cache):
        """Test that getting a translation updates the access time"""
        word = "kuća"
        translation_data = {"english_translation": "house"}

        # Set translation
        translation_cache.set(word, translation_data)

        # Get first time
        first_access = translation_cache.get(word)
        first_access_time = first_access["last_accessed"]

        # Wait a bit longer to ensure time difference
        time.sleep(1.1)
        second_access = translation_cache.get(word)
        second_access_time = second_access["last_accessed"]

        # Access time should be updated
        assert second_access_time > first_access_time

    def test_set_with_redis_error(self, fake_redis):
        """Test handling of Redis errors during set"""
        # Mock Redis to raise an exception
        fake_redis.setex = Mock(side_effect=Exception("Redis connection lost"))

        cache = TranslationCache(fake_redis)
        success = cache.set("test", {"data": "test"})

        assert success is False

    def test_get_with_redis_error(self, fake_redis):
        """Test handling of Redis errors during get"""
        # Set up cache normally first
        cache = TranslationCache(fake_redis)
        cache.set("test", {"data": "test"})

        # Mock Redis to raise an exception on get
        fake_redis.get = Mock(side_effect=Exception("Redis connection lost"))

        result = cache.get("test")
        assert result is None

    def test_get_with_invalid_json(self, fake_redis):
        """Test handling of invalid JSON in cached data"""
        cache = TranslationCache(fake_redis)

        # Manually set invalid JSON data
        cache_key = cache._generate_key("test")
        fake_redis.set(cache_key, "invalid json data")

        result = cache.get("test")
        assert result is None

    def test_get_batch_translations(self, translation_cache):
        """Test getting multiple translations in batch"""
        # Set up test data
        translations = {
            "kuća": {"english_translation": "house"},
            "raditi": {"english_translation": "to work"},
            "grad": {"english_translation": "city"},
        }

        for word, data in translations.items():
            translation_cache.set(word, data)

        # Get batch
        words = ["kuća", "raditi", "grad", "nonexistent"]
        results = translation_cache.get_batch(words)

        assert len(results) == 4
        assert results["kuća"]["english_translation"] == "house"
        assert results["raditi"]["english_translation"] == "to work"
        assert results["grad"]["english_translation"] == "city"
        assert results["nonexistent"] is None

    def test_get_batch_empty_list(self, translation_cache):
        """Test getting batch with empty word list"""
        results = translation_cache.get_batch([])
        assert results == {}

    def test_set_batch_translations(self, translation_cache):
        """Test setting multiple translations in batch"""
        translations = {
            "auto": {"english_translation": "car"},
            "voda": {"english_translation": "water"},
            "sunce": {"english_translation": "sun"},
        }

        count = translation_cache.set_batch(translations)
        assert count == 3

        # Verify they were cached
        for word, expected_data in translations.items():
            cached_data = translation_cache.get(word)
            assert cached_data is not None
            assert (
                cached_data["english_translation"]
                == expected_data["english_translation"]
            )

    def test_set_batch_empty_dict(self, translation_cache):
        """Test setting batch with empty dictionary"""
        count = translation_cache.set_batch({})
        assert count == 0

    def test_get_stats(self, translation_cache):
        """Test getting cache statistics"""
        # Perform some cache operations
        translation_cache.set("test1", {"data": "1"})
        translation_cache.set("test2", {"data": "2"})

        translation_cache.get("test1")  # Hit
        translation_cache.get("test1")  # Hit
        translation_cache.get("nonexistent")  # Miss

        stats = translation_cache.get_stats()

        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "total_translations" in stats
        assert "hit_rate_percent" in stats
        assert "cache_size" in stats
        assert "cache_efficiency" in stats

        assert stats["cache_hits"] >= 2
        assert stats["cache_misses"] >= 1
        assert stats["total_translations"] >= 2

    def test_clear_stats(self, translation_cache):
        """Test clearing cache statistics"""
        # Generate some stats
        translation_cache.set("test", {"data": "test"})
        translation_cache.get("test")

        # Clear stats
        translation_cache.clear_stats()

        # Check stats are reset
        stats = translation_cache.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["total_translations"] == 0

    def test_clear_cache(self, translation_cache):
        """Test clearing all cached translations"""
        # Set up some translations
        translations = {
            "test1": {"data": "1"},
            "test2": {"data": "2"},
            "test3": {"data": "3"},
        }

        for word, data in translations.items():
            translation_cache.set(word, data)

        # Clear cache
        cleared_count = translation_cache.clear_cache()
        assert cleared_count == 3

        # Verify cache is empty
        for word in translations.keys():
            assert translation_cache.get(word) is None

    def test_clear_cache_empty(self, translation_cache):
        """Test clearing empty cache"""
        cleared_count = translation_cache.clear_cache()
        assert cleared_count == 0

    def test_warm_cache(self, translation_cache):
        """Test cache warming with known translations"""
        translations = {
            "pas": {"english_translation": "dog"},
            "mačka": {"english_translation": "cat"},
            "ptica": {"english_translation": "bird"},
        }

        warmed_count = translation_cache.warm_cache(translations)
        assert warmed_count == 3

        # Verify translations are cached
        for word, expected_data in translations.items():
            cached_data = translation_cache.get(word)
            assert cached_data is not None
            assert (
                cached_data["english_translation"]
                == expected_data["english_translation"]
            )

    def test_cleanup_old_entries(self, fake_redis):
        """Test cleaning up old cache entries"""
        cache = TranslationCache(fake_redis, ttl=3600)

        # Create some test data with different ages
        current_time = int(time.time())
        old_time = current_time - (70 * 24 * 3600)  # 70 days ago
        recent_time = current_time - (10 * 24 * 3600)  # 10 days ago

        # Set up test entries
        old_data = {
            "english_translation": "old",
            "cached_at": old_time,
            "last_accessed": old_time,
        }
        recent_data = {
            "english_translation": "recent",
            "cached_at": recent_time,
            "last_accessed": recent_time,
        }

        old_key = cache._generate_key("old_word")
        recent_key = cache._generate_key("recent_word")

        fake_redis.set(old_key, json.dumps(old_data))
        fake_redis.set(recent_key, json.dumps(recent_data))

        # Clean up entries older than 60 days
        cleaned_count = cache.cleanup_old_entries(max_age_days=60)

        # Should have cleaned up 1 old entry
        assert cleaned_count == 1

        # Recent entry should still exist
        assert fake_redis.get(recent_key) is not None
        assert fake_redis.get(old_key) is None

    def test_cleanup_old_entries_with_invalid_data(self, fake_redis):
        """Test cleanup with invalid JSON data"""
        cache = TranslationCache(fake_redis)

        # Set invalid JSON data
        invalid_key = cache._generate_key("invalid")
        fake_redis.set(invalid_key, "invalid json")

        # Should clean up invalid entries too
        cleaned_count = cache.cleanup_old_entries()
        assert cleaned_count == 1

    def test_stats_tracking(self, translation_cache):
        """Test that cache statistics are properly tracked"""
        # Perform various operations
        translation_cache.set("word1", {"translation": "translation1"})
        translation_cache.set("word2", {"translation": "translation2"})

        # Cache hits
        translation_cache.get("word1")
        translation_cache.get("word1")
        translation_cache.get("word2")

        # Cache misses
        translation_cache.get("nonexistent1")
        translation_cache.get("nonexistent2")

        stats = translation_cache.get_stats()

        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 2
        assert stats["total_translations"] == 2
        assert stats["total_requests"] == 5
        assert stats["hit_rate_percent"] == 60.0

    def test_stats_with_redis_error(self, fake_redis):
        """Test stats handling when Redis has errors"""
        # Mock Redis to raise an exception
        fake_redis.hgetall = Mock(side_effect=Exception("Redis error"))

        cache = TranslationCache(fake_redis)
        stats = cache.get_stats()

        assert "error" in stats
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0

    def test_case_insensitive_caching(self, translation_cache):
        """Test that caching is case insensitive"""
        # Set translation with lowercase
        translation_cache.set("kuća", {"english_translation": "house"})

        # Get with different cases
        result1 = translation_cache.get("kuća")
        result2 = translation_cache.get("KUĆA")
        result3 = translation_cache.get("Kuća")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        assert result1["english_translation"] == "house"
        assert result2["english_translation"] == "house"
        assert result3["english_translation"] == "house"

    def test_whitespace_normalization(self, translation_cache):
        """Test that whitespace is properly normalized"""
        # Set with whitespace
        translation_cache.set("  raditi  ", {"english_translation": "to work"})

        # Get with different whitespace
        result1 = translation_cache.get("raditi")
        result2 = translation_cache.get("  raditi")
        result3 = translation_cache.get("raditi  ")

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None

        for result in [result1, result2, result3]:
            assert result["english_translation"] == "to work"

    @patch("time.time")
    def test_ttl_expiration(self, mock_time, fake_redis):
        """Test that cache entries respect TTL"""
        # Set up time mocking
        current_time = 1000000
        mock_time.return_value = current_time

        cache = TranslationCache(fake_redis, ttl=3600)  # 1 hour TTL

        # Set a translation
        cache.set("test", {"data": "test"})

        # Verify it was set with correct TTL
        cache_key = cache._generate_key("test")
        assert fake_redis.ttl(cache_key) <= 3600
        assert fake_redis.ttl(cache_key) > 3500  # Should be close to 3600

    def test_update_stats_error_handling(self, fake_redis):
        """Test error handling in stats updates"""
        # Mock Redis to raise exception on hincrby
        fake_redis.hincrby = Mock(side_effect=Exception("Redis error"))

        cache = TranslationCache(fake_redis)

        # Should not raise exception, just log warning
        cache._update_stats(hit=True)
        cache._update_stats(hit=False)

        # Should complete without error
        assert True
