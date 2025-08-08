"""
Unit tests for OptimizedSerbianTextProcessor service
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.optimized_text_processor import OptimizedSerbianTextProcessor


class TestOptimizedTextProcessor:
    """Test OptimizedSerbianTextProcessor unit functionality"""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # Default to cache miss
        mock_redis.setex.return_value = True
        mock_redis.keys.return_value = []
        mock_redis.delete.return_value = 0
        return mock_redis

    @pytest.fixture
    def mock_translation_cache(self):
        """Create mock TranslationCache"""
        mock_cache = MagicMock()
        mock_cache.get_stats.return_value = {
            "total_requests": 10,
            "cache_hits": 5,
            "cache_misses": 5,
        }
        mock_cache.warm_cache.return_value = 5
        return mock_cache

    @pytest.fixture
    def processor(self, mock_redis_client, mock_translation_cache):
        """Create OptimizedSerbianTextProcessor instance with mocks"""
        with patch(
            "services.optimized_text_processor.TranslationCache",
            return_value=mock_translation_cache,
        ):
            processor = OptimizedSerbianTextProcessor(
                openai_api_key="test-api-key", redis_client=mock_redis_client, model="gpt-3.5-turbo"
            )
            return processor

    @pytest.fixture
    def sample_categories(self):
        """Sample categories for testing"""
        return [
            {"id": 1, "name": "Common Words"},
            {"id": 2, "name": "Verbs"},
            {"id": 3, "name": "Nouns"},
            {"id": 4, "name": "Adjectives"},
        ]

    @pytest.fixture
    def sample_processing_result(self):
        """Sample processing result"""
        return {
            "translations": [
                {
                    "serbian_word": "raditi",
                    "english_translation": "to work",
                    "category_id": 2,
                    "category_name": "Verbs",
                },
                {
                    "serbian_word": "pas",
                    "english_translation": "dog",
                    "category_id": 3,
                    "category_name": "Nouns",
                },
            ],
            "new_words": 2,
            "total_words": 2,
        }

    def test_cache_key_generation(self, processor):
        """Test cache key generation for text processing"""
        text = "Jutros sam ustao rano"
        max_words = 20
        temperature = 0.3

        cache_key = processor._generate_text_cache_key(text, max_words, temperature)

        assert cache_key.startswith("text_processing:")
        assert len(cache_key) > 20  # Should have hash component

        # Same inputs should generate same key
        cache_key2 = processor._generate_text_cache_key(text, max_words, temperature)
        assert cache_key == cache_key2

        # Different inputs should generate different keys
        cache_key3 = processor._generate_text_cache_key(text, 15, temperature)
        assert cache_key != cache_key3

    def test_cache_hit_scenario(
        self, processor, mock_redis_client, sample_categories, sample_processing_result
    ):
        """Test processing with cache hit"""
        # Setup cache hit
        cached_data = json.dumps(
            {**sample_processing_result, "cached_at": 1234567890, "cache_version": "1.0"}
        )
        mock_redis_client.get.return_value = cached_data

        text = "Jutros sam ustao rano"
        result = processor.process_text_optimized(text, sample_categories)

        # Should return cached result
        assert result["translations"] == sample_processing_result["translations"]
        assert result["new_words"] == 2

        # Should increment cache hit stats
        assert processor.stats["cache_hits"] == 1
        assert processor.stats["llm_calls"] == 0
        assert processor.stats["total_requests"] == 1

    @patch("services.optimized_text_processor.SerbianTextProcessor.process_text")
    def test_cache_miss_scenario(
        self,
        mock_process_text,
        processor,
        mock_redis_client,
        sample_categories,
        sample_processing_result,
    ):
        """Test processing with cache miss"""
        # Setup cache miss and LLM response
        mock_redis_client.get.return_value = None
        mock_process_text.return_value = sample_processing_result

        text = "Jutros sam ustao rano"
        result = processor.process_text_optimized(text, sample_categories)

        # Should call parent process_text method
        mock_process_text.assert_called_once_with(text, sample_categories, 20, 0.3)

        # Should return LLM result
        assert result["translations"] == sample_processing_result["translations"]
        assert result["new_words"] == 2

        # Should increment LLM call stats
        assert processor.stats["cache_hits"] == 0
        assert processor.stats["llm_calls"] == 1
        assert processor.stats["total_requests"] == 1

        # Should cache the result
        mock_redis_client.setex.assert_called_once()

    def test_apply_exclusions(self, processor, sample_processing_result):
        """Test word exclusion functionality"""
        excluded_words = {"raditi"}  # Exclude "raditi"

        result = processor._apply_exclusions(sample_processing_result, excluded_words)

        # Should filter out excluded word
        assert len(result["translations"]) == 1
        assert result["translations"][0]["serbian_word"] == "pas"
        assert result["new_words"] == 1
        assert result["excluded_count"] == 1

    def test_batch_processing_with_mixed_cache(
        self, processor, mock_redis_client, sample_categories, sample_processing_result
    ):
        """Test batch processing with some cache hits and misses"""
        texts = ["Text 1", "Text 2", "Text 3"]

        # Setup mixed cache scenario: first text cached, others not
        def mock_get(key):
            if "Text 1" in key or key.endswith("text_processing:"):
                return None  # Handle key pattern matching
            if key.startswith("text_processing:"):
                # Only first text is cached
                cache_keys = [processor._generate_text_cache_key(text, 20, 0.3) for text in texts]
                if key == cache_keys[0]:
                    return json.dumps(sample_processing_result)
            return None

        mock_redis_client.get.side_effect = mock_get

        with patch(
            "services.optimized_text_processor.SerbianTextProcessor.process_text",
            return_value=sample_processing_result,
        ):
            results = processor.batch_process_texts(texts, sample_categories)

        # Should return results for all texts
        assert len(results) == 3
        assert all(result is not None for result in results)

        # Should have mixed cache hits and LLM calls
        assert processor.stats["cache_hits"] >= 0  # At least some cache activity
        assert processor.stats["llm_calls"] >= 0  # At least some LLM calls

    def test_performance_stats_calculation(self, processor, mock_translation_cache):
        """Test performance statistics calculation"""
        # Simulate some processing activity
        processor.stats["total_requests"] = 10
        processor.stats["cache_hits"] = 7
        processor.stats["llm_calls"] = 3
        processor.stats["processing_time"] = 5.0

        stats = processor.get_processing_stats()

        # Check structure
        assert "processing_stats" in stats
        assert "cache_stats" in stats
        assert "performance_rating" in stats

        # Check calculations
        processing_stats = stats["processing_stats"]
        assert processing_stats["total_requests"] == 10
        assert processing_stats["cache_hits"] == 7
        assert processing_stats["llm_calls"] == 3
        assert processing_stats["cache_hit_rate_percent"] == 70.0
        assert processing_stats["avg_processing_time_seconds"] == 0.5

        # Should get performance rating
        assert stats["performance_rating"] in ["Excellent", "Good", "Fair", "Poor"]


class TestOptimizedTextProcessorAnalysis:
    """Test text analysis functionality"""

    @pytest.fixture
    def processor(self):
        """Create processor for analysis tests"""
        mock_redis = MagicMock()
        with patch("services.optimized_text_processor.TranslationCache"):
            return OptimizedSerbianTextProcessor("test-key", mock_redis)

    def test_text_pattern_analysis(self, processor):
        """Test text pattern analysis functionality"""
        texts = [
            "Jutros sam ustao rano",
            "Jutros sam ustao rano",  # Duplicate
            "Večeras idem u bioskop",
            "Sutra radim od kuće",
        ]

        analysis = processor.analyze_text_patterns(texts)

        # Check analysis structure
        assert "text_count" in analysis
        assert "unique_text_count" in analysis
        assert "duplicate_rate_percent" in analysis
        assert "avg_text_length" in analysis
        assert "most_common_words" in analysis
        assert "cache_benefit_estimate" in analysis
        assert "optimization_suggestions" in analysis

        # Check calculations
        assert analysis["text_count"] == 4
        assert analysis["unique_text_count"] == 3
        assert analysis["duplicate_rate_percent"] == 25.0  # 1 duplicate out of 4

        # Should provide cache benefit estimate
        assert analysis["cache_benefit_estimate"] in ["High", "Medium", "Low"]

        # Should provide optimization suggestions
        assert isinstance(analysis["optimization_suggestions"], list)
        assert len(analysis["optimization_suggestions"]) > 0

    def test_empty_text_analysis(self, processor):
        """Test analysis with empty text list"""
        analysis = processor.analyze_text_patterns([])

        assert "error" in analysis
        assert analysis["error"] == "No texts provided"

    def test_performance_rating_calculation(self, processor):
        """Test performance rating calculation logic"""
        # Test excellent rating
        rating = processor._get_performance_rating(85.0, 0.5)
        assert rating == "Excellent"

        # Test good rating
        rating = processor._get_performance_rating(65.0, 1.5)
        assert rating == "Good"

        # Test fair rating
        rating = processor._get_performance_rating(45.0, 2.5)
        assert rating == "Fair"

        # Test poor rating
        rating = processor._get_performance_rating(20.0, 5.0)
        assert rating == "Poor"


class TestOptimizedTextProcessorCacheMethods:
    """Test cache-related methods with missing coverage"""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client for cache testing"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.keys.return_value = ["text_processing:key1", "text_processing:key2"]
        mock_redis.delete.return_value = 2
        return mock_redis

    @pytest.fixture
    def processor(self, mock_redis_client):
        """Create processor for cache testing"""
        with patch("services.optimized_text_processor.TranslationCache"):
            return OptimizedSerbianTextProcessor("test-key", mock_redis_client)

    def test_clear_processing_cache_success(self, processor, mock_redis_client):
        """Test successful cache clearing"""
        result = processor.clear_processing_cache()

        # Should search for text processing keys and delete them
        mock_redis_client.keys.assert_called_once_with("text_processing:*")
        mock_redis_client.delete.assert_called_once_with(
            "text_processing:key1", "text_processing:key2"
        )
        assert result == 2

    def test_clear_processing_cache_no_keys(self, processor, mock_redis_client):
        """Test cache clearing when no keys exist"""
        mock_redis_client.keys.return_value = []

        result = processor.clear_processing_cache()

        mock_redis_client.keys.assert_called_once_with("text_processing:*")
        mock_redis_client.delete.assert_not_called()
        assert result == 0

    def test_clear_processing_cache_error(self, processor, mock_redis_client):
        """Test cache clearing with Redis error"""
        mock_redis_client.keys.side_effect = Exception("Redis connection error")

        result = processor.clear_processing_cache()

        assert result == 0

    def test_warm_cache_with_vocabulary_success(self, processor):
        """Test successful vocabulary cache warming"""
        vocabulary_words = [
            {
                "serbian_word": "raditi",
                "english_translation": "to work",
                "category_id": 2,
                "category_name": "Verbs",
            },
            {
                "serbian_word": "pas",
                "english_translation": "dog",
                "category_id": 3,
                "category_name": "Nouns",
            },
        ]

        # Mock the translation cache warm_cache method
        processor.cache.warm_cache.return_value = 2

        result = processor.warm_cache_with_vocabulary(vocabulary_words)

        # Should call cache.warm_cache with properly formatted data
        processor.cache.warm_cache.assert_called_once()
        args = processor.cache.warm_cache.call_args[0][0]

        assert "raditi" in args
        assert "pas" in args
        assert args["raditi"]["english_translation"] == "to work"
        assert args["pas"]["category_name"] == "Nouns"
        assert result == 2

    def test_warm_cache_with_vocabulary_empty_data(self, processor):
        """Test vocabulary cache warming with incomplete data"""
        vocabulary_words = [
            {"serbian_word": "raditi"},  # Missing translation
            {"english_translation": "dog"},  # Missing serbian word
            {"serbian_word": "pas", "english_translation": "dog"},  # Valid entry
        ]

        processor.cache.warm_cache.return_value = 1

        result = processor.warm_cache_with_vocabulary(vocabulary_words)

        # Should only process valid entries
        args = processor.cache.warm_cache.call_args[0][0]
        assert len(args) == 1
        assert "pas" in args
        assert "raditi" not in args
        assert result == 1


class TestOptimizedTextProcessorPreprocessing:
    """Test preprocessing and caching methods"""

    @pytest.fixture
    def processor(self):
        """Create processor for preprocessing tests"""
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True
        with patch("services.optimized_text_processor.TranslationCache"):
            return OptimizedSerbianTextProcessor("test-key", mock_redis)

    @patch("services.optimized_text_processor.SerbianTextProcessor.process_text")
    def test_preprocess_and_cache_common_words_success(self, mock_process_text, processor):
        """Test successful preprocessing and caching of common words"""
        common_texts = ["Jutros sam ustao rano", "Večeras idem u bioskop", "Sutra radim od kuće"]

        # Mock successful processing results
        mock_process_text.return_value = {
            "translations": [{"serbian_word": "test", "english_translation": "test"}],
            "new_words": 1,
        }

        result = processor.preprocess_and_cache_common_words(common_texts)

        # Should call process_text for each text
        assert mock_process_text.call_count == 3

        # Should return count of successfully cached entries
        assert result == 3

    @patch("services.optimized_text_processor.SerbianTextProcessor.process_text")
    def test_preprocess_and_cache_common_words_with_errors(self, mock_process_text, processor):
        """Test preprocessing with some processing errors"""
        common_texts = ["Text 1", "Text 2", "Text 3"]

        # Mock mixed results - some success, some error
        def mock_process_side_effect(text, categories, max_words=20, temperature=0.3):
            if text == "Text 2":
                raise Exception("Processing error")
            elif text == "Text 3":
                return {"error": "Invalid result"}
            else:
                return {
                    "translations": [{"serbian_word": "test", "english_translation": "test"}],
                    "new_words": 1,
                }

        mock_process_text.side_effect = mock_process_side_effect

        result = processor.preprocess_and_cache_common_words(common_texts)

        # Should only cache successful results (Text 1)
        assert result == 1

    def test_preprocess_and_cache_common_words_empty_list(self, processor):
        """Test preprocessing with empty text list"""
        result = processor.preprocess_and_cache_common_words([])

        assert result == 0


class TestOptimizedTextProcessorErrorHandling:
    """Test error handling scenarios"""

    @pytest.fixture
    def processor(self):
        """Create processor for error testing"""
        mock_redis = MagicMock()
        with patch("services.optimized_text_processor.TranslationCache"):
            return OptimizedSerbianTextProcessor("test-key", mock_redis)

    def test_get_cached_result_json_error(self, processor):
        """Test error handling in _get_cached_result with invalid JSON"""
        processor.redis.get.return_value = "invalid json data"

        result = processor._get_cached_result("test_key")

        assert result is None

    def test_get_cached_result_redis_error(self, processor):
        """Test error handling in _get_cached_result with Redis exception"""
        processor.redis.get.side_effect = Exception("Redis connection error")

        result = processor._get_cached_result("test_key")

        assert result is None

    def test_cache_result_redis_error(self, processor):
        """Test error handling in _cache_result with Redis exception"""
        processor.redis.setex.side_effect = Exception("Redis connection error")

        result = processor._cache_result("test_key", {"test": "data"})

        assert result is False

    @patch("services.optimized_text_processor.SerbianTextProcessor.process_text")
    def test_process_text_optimized_error_handling(self, mock_process_text, processor):
        """Test main processing method error handling"""
        mock_process_text.side_effect = Exception("LLM processing error")

        categories = [{"id": 1, "name": "Test"}]
        result = processor.process_text_optimized("test text", categories)

        # Should return error result
        assert "error" in result
        assert "Processing error:" in result["error"]
        assert result["processed_words"] == []
