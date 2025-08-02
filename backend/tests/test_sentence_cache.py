"""
Tests for sentence caching functionality
"""

import pytest
import json
from unittest.mock import Mock, patch
from services.sentence_cache import SentenceCacheService


class TestSentenceCache:
    """Test sentence caching service and API endpoints"""

    @pytest.fixture
    def sentence_cache_service(self, fake_redis):
        """Create sentence cache service with fake Redis"""
        return SentenceCacheService(fake_redis)

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response for sentence generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = {
            "content": "Pas trči kroz park.\nMoj pas voli da igra.\nVeliki pas laje glasno."
        }
        return mock_response

    def test_cache_and_retrieve_sentences(self, sentence_cache_service):
        """Test basic sentence caching and retrieval"""
        serbian_word = "pas"
        english_translation = "dog"
        test_sentences = [
            "Pas trči kroz park.",
            "Moj pas voli da igra.",
            "Veliki pas laje glasno.",
        ]

        # Cache sentences
        success = sentence_cache_service.cache_sentences(
            serbian_word, english_translation, test_sentences
        )
        assert success

        # Retrieve cached sentences
        cached_sentences = sentence_cache_service.get_cached_sentences(
            serbian_word, english_translation
        )
        assert cached_sentences == test_sentences

        # Get random sentence
        random_sentence = sentence_cache_service.get_random_sentence(
            serbian_word, english_translation
        )
        assert random_sentence in test_sentences

    def test_cache_miss(self, sentence_cache_service):
        """Test behavior when no cached sentences exist"""
        cached_sentences = sentence_cache_service.get_cached_sentences(
            "nonexistent", "word"
        )
        assert cached_sentences is None

        random_sentence = sentence_cache_service.get_random_sentence(
            "nonexistent", "word"
        )
        assert random_sentence is None

    @patch("openai.ChatCompletion.create")
    def test_generate_and_cache_sentences(
        self, mock_openai, sentence_cache_service, mock_openai_response
    ):
        """Test sentence generation and caching"""
        mock_openai.return_value = mock_openai_response

        serbian_word = "raditi"
        english_translation = "to work"
        api_key = "test-api-key"

        # Generate and cache sentences
        sentences = sentence_cache_service.generate_and_cache_sentences(
            serbian_word, english_translation, api_key
        )

        # Verify sentences were generated
        assert len(sentences) > 0
        assert all(isinstance(s, str) for s in sentences)

        # Verify sentences were cached
        cached_sentences = sentence_cache_service.get_cached_sentences(
            serbian_word, english_translation
        )
        assert cached_sentences == sentences

        # Verify OpenAI was called
        mock_openai.assert_called_once()

    def test_cache_stats(self, sentence_cache_service):
        """Test cache statistics"""
        # Initially empty cache
        stats = sentence_cache_service.get_cache_stats()
        assert stats["total_cached_words"] == 0

        # Add some cached sentences
        sentence_cache_service.cache_sentences(
            "pas", "dog", ["Test sentence 1", "Test sentence 2"]
        )
        sentence_cache_service.cache_sentences("mačka", "cat", ["Test sentence 3"])

        # Check updated stats
        stats = sentence_cache_service.get_cache_stats()
        assert stats["total_cached_words"] == 2

    def test_clear_cache(self, sentence_cache_service):
        """Test cache clearing"""
        # Add some cached sentences
        sentence_cache_service.cache_sentences("pas", "dog", ["Test sentence"])
        sentence_cache_service.cache_sentences("mačka", "cat", ["Test sentence"])

        # Verify cache has content
        stats = sentence_cache_service.get_cache_stats()
        assert stats["total_cached_words"] == 2

        # Clear cache
        cleared_count = sentence_cache_service.clear_cache()
        assert cleared_count == 2

        # Verify cache is empty
        stats = sentence_cache_service.get_cache_stats()
        assert stats["total_cached_words"] == 0


class TestSentenceCacheIntegration:
    """Test sentence cache integration with word processing"""

    def test_warm_cache_for_words(self, fake_redis):
        """Test warming cache for multiple words"""
        service = SentenceCacheService(fake_redis)

        # Mock words data
        words_data = [
            {
                "serbian_word": "pas",
                "english_translation": "dog",
                "category_name": "Animals",
            },
            {
                "serbian_word": "mačka",
                "english_translation": "cat",
                "category_name": "Animals",
            },
        ]

        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = {
                "content": "Test sentence 1.\nTest sentence 2."
            }
            mock_openai.return_value = mock_response

            # Warm cache
            cached_count = service.warm_cache_for_words(words_data, "test-api-key")

            # Verify both words were cached
            assert cached_count == 2

            # Verify sentences are retrievable
            pas_sentences = service.get_cached_sentences("pas", "dog")
            assert pas_sentences is not None
            assert len(pas_sentences) > 0

            cat_sentences = service.get_cached_sentences("mačka", "cat")
            assert cat_sentences is not None
            assert len(cat_sentences) > 0

    def test_populate_user_vocabulary_cache(self, fake_redis):
        """Test populating cache for user vocabulary"""
        service = SentenceCacheService(fake_redis)

        # Pre-cache one word
        service.cache_sentences("pas", "dog", ["Cached sentence"])

        words_data = [
            {"serbian_word": "pas", "english_translation": "dog"},
            {"serbian_word": "mačka", "english_translation": "cat"},
        ]

        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = {"content": "Generated sentence"}
            mock_openai.return_value = mock_response

            result = service.populate_user_vocabulary_cache(words_data, "test-api-key")

            # Should cache only the new word (mačka)
            assert result["success"] is True
            assert result["already_cached"] == 1  # pas was already cached
            assert result["newly_cached"] == 1  # mačka was newly cached
            assert result["total_words"] == 2

    def test_cache_key_generation(self, fake_redis):
        """Test cache key generation is consistent"""
        service = SentenceCacheService(fake_redis)

        # Test key generation with different cases
        key1 = service._get_cache_key("Pas", "Dog")
        key2 = service._get_cache_key("pas", "dog")
        key3 = service._get_cache_key("PAS", "DOG")

        # All should be the same (lowercase)
        assert key1 == key2 == key3
        assert "sentence_cache:pas:dog" in key1
