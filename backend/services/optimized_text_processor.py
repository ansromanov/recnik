"""
Optimized Serbian Text Processing Service with Caching and Performance Features
"""

import hashlib
import json
import logging
import time
from typing import Any, Optional

from .text_processor import SerbianTextProcessor
from .translation_cache import TranslationCache

logger = logging.getLogger(__name__)


class OptimizedSerbianTextProcessor(SerbianTextProcessor):
    """
    Enhanced Serbian text processor with intelligent caching, batch processing,
    and performance optimizations.
    """

    def __init__(
        self,
        openai_api_key: str,
        redis_client,
        model: str = "gpt-3.5-turbo",
        cache_ttl: int = 30 * 24 * 3600,  # 30 days
    ):
        """
        Initialize the optimized text processor.

        Args:
            openai_api_key: OpenAI API key
            redis_client: Redis client for caching
            model: OpenAI model to use
            cache_ttl: Cache time-to-live in seconds
        """
        super().__init__(openai_api_key, model)
        self.cache = TranslationCache(redis_client, cache_ttl)
        self.redis = redis_client

        # Performance tracking
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "llm_calls": 0,
            "processing_time": 0,
        }

    def process_text_optimized(
        self,
        text: str,
        categories: list[dict[str, Any]],
        max_words: int = 20,
        temperature: float = 0.3,
        use_cache: bool = True,
        excluded_words: Optional[set[str]] = None,
    ) -> dict[str, Any]:
        """
        Process Serbian text with caching and optimization features.

        Args:
            text: Input Serbian text
            categories: Available word categories
            max_words: Maximum number of words to extract
            temperature: OpenAI temperature setting
            use_cache: Whether to use caching
            excluded_words: Set of words to exclude from processing

        Returns:
            Dictionary with processed words and filtering summary
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # Generate cache key for the text processing request
            cache_key = self._generate_text_cache_key(text, max_words, temperature)

            # Try to get from cache first
            if use_cache:
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    self.stats["cache_hits"] += 1
                    logger.info(
                        f"Cache HIT for text processing (key: {cache_key[:16]}...)"
                    )

                    # Apply current exclusions to cached result
                    if excluded_words:
                        cached_result = self._apply_exclusions(
                            cached_result, excluded_words
                        )

                    return cached_result

            # Process with LLM if not cached
            logger.info(f"Cache MISS - processing with LLM (key: {cache_key[:16]}...)")
            self.stats["llm_calls"] += 1

            # Use parent class method for actual processing
            result = super().process_text(text, categories, max_words, temperature)

            # Apply exclusions if provided
            if excluded_words:
                result = self._apply_exclusions(result, excluded_words)

            # Cache the result
            if use_cache and "error" not in result:
                self._cache_result(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error in optimized text processing: {e}")
            return {
                "error": f"Processing error: {e!s}",
                "processed_words": [],
            }
        finally:
            processing_time = time.time() - start_time
            self.stats["processing_time"] += processing_time
            logger.info(f"Text processing completed in {processing_time:.2f}s")

    def batch_process_texts(
        self,
        texts: list[str],
        categories: list[dict[str, Any]],
        max_words: int = 20,
        temperature: float = 0.3,
        excluded_words: Optional[set[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        Process multiple texts efficiently with batch optimization.

        Args:
            texts: List of input texts
            categories: Available word categories
            max_words: Maximum words per text
            temperature: OpenAI temperature
            excluded_words: Words to exclude

        Returns:
            List of processing results
        """
        if not texts:
            return []

        logger.info(f"Starting batch processing of {len(texts)} texts")
        start_time = time.time()

        # Generate cache keys for all texts
        cache_keys = [
            self._generate_text_cache_key(text, max_words, temperature)
            for text in texts
        ]

        # Check cache for all texts
        cached_results = {}
        uncached_texts = []
        uncached_indices = []

        for i, (text, cache_key) in enumerate(zip(texts, cache_keys)):
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                cached_results[i] = cached_result
                self.stats["cache_hits"] += 1
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        logger.info(f"Cache hits: {len(cached_results)}/{len(texts)}")

        # Process uncached texts
        results = [None] * len(texts)

        # Fill in cached results
        for i, result in cached_results.items():
            if excluded_words:
                result = self._apply_exclusions(result, excluded_words)
            results[i] = result

        # Process uncached texts one by one (can be optimized further with batch LLM calls)
        for text, i in zip(uncached_texts, uncached_indices):
            try:
                result = super().process_text(text, categories, max_words, temperature)
                self.stats["llm_calls"] += 1

                if excluded_words:
                    result = self._apply_exclusions(result, excluded_words)

                results[i] = result

                # Cache the result
                cache_key = cache_keys[i]
                if "error" not in result:
                    self._cache_result(cache_key, result)

            except Exception as e:
                logger.error(f"Error processing text {i}: {e}")
                results[i] = {
                    "error": f"Processing error: {e!s}",
                    "processed_words": [],
                }

        processing_time = time.time() - start_time
        logger.info(f"Batch processing completed in {processing_time:.2f}s")

        return results

    def preprocess_and_cache_common_words(self, common_texts: list[str]) -> int:
        """
        Preprocess common text patterns and cache them for faster future processing.

        Args:
            common_texts: List of common text patterns to preprocess

        Returns:
            Number of successfully cached entries
        """
        logger.info(f"Preprocessing and caching {len(common_texts)} common texts")

        # Mock categories for preprocessing
        categories = [
            {"id": 1, "name": "Common Words"},
            {"id": 2, "name": "Verbs"},
            {"id": 3, "name": "Nouns"},
            {"id": 4, "name": "Adjectives"},
        ]

        cached_count = 0
        for text in common_texts:
            try:
                result = super().process_text(text, categories)
                if "error" not in result:
                    cache_key = self._generate_text_cache_key(text, 20, 0.3)
                    if self._cache_result(cache_key, result):
                        cached_count += 1
            except Exception as e:
                logger.error(f"Error preprocessing text: {e}")

        logger.info(f"Successfully cached {cached_count}/{len(common_texts)} texts")
        return cached_count

    def get_processing_stats(self) -> dict[str, Any]:
        """
        Get processing performance statistics.

        Returns:
            Dictionary with performance stats
        """
        cache_stats = self.cache.get_stats()

        total_requests = max(1, self.stats["total_requests"])
        avg_processing_time = self.stats["processing_time"] / total_requests
        cache_hit_rate = (self.stats["cache_hits"] / total_requests) * 100

        return {
            "processing_stats": {
                "total_requests": self.stats["total_requests"],
                "cache_hits": self.stats["cache_hits"],
                "llm_calls": self.stats["llm_calls"],
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "avg_processing_time_seconds": round(avg_processing_time, 3),
                "total_processing_time_seconds": round(
                    self.stats["processing_time"], 2
                ),
            },
            "cache_stats": cache_stats,
            "performance_rating": self._get_performance_rating(
                cache_hit_rate, avg_processing_time
            ),
        }

    def clear_processing_cache(self) -> int:
        """
        Clear the text processing cache.

        Returns:
            Number of cache entries cleared
        """
        try:
            # Clear text processing cache entries
            cache_keys = self.redis.keys("text_processing:*")
            if cache_keys:
                deleted_count = self.redis.delete(*cache_keys)
                logger.info(f"Cleared {deleted_count} text processing cache entries")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Error clearing processing cache: {e}")
            return 0

    def warm_cache_with_vocabulary(self, vocabulary_words: list[dict[str, Any]]) -> int:
        """
        Warm the cache with existing vocabulary words for faster lookups.

        Args:
            vocabulary_words: List of vocabulary word dictionaries

        Returns:
            Number of entries warmed
        """
        logger.info(f"Warming cache with {len(vocabulary_words)} vocabulary words")

        # Create translation data for caching
        translation_data = {}
        for word_info in vocabulary_words:
            serbian_word = word_info.get("serbian_word", "")
            english_translation = word_info.get("english_translation", "")

            if serbian_word and english_translation:
                translation_data[serbian_word] = {
                    "serbian_word": serbian_word,
                    "english_translation": english_translation,
                    "category_id": word_info.get("category_id", 1),
                    "category_name": word_info.get("category_name", "Common Words"),
                    "source": "vocabulary_warm_up",
                }

        return self.cache.warm_cache(translation_data)

    def _generate_text_cache_key(
        self, text: str, max_words: int, temperature: float
    ) -> str:
        """Generate a cache key for text processing requests."""
        # Create a hash of the text content and parameters
        content = f"{text.strip()[:1000]}|{max_words}|{temperature}"
        hash_key = hashlib.md5(content.encode("utf-8")).hexdigest()
        return f"text_processing:{hash_key}"

    def _get_cached_result(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Get cached result for a text processing request."""
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
        return None

    def _cache_result(self, cache_key: str, result: dict[str, Any]) -> bool:
        """Cache a text processing result."""
        try:
            # Add caching metadata
            cache_data = {
                **result,
                "cached_at": int(time.time()),
                "cache_version": "1.0",
            }

            # Cache for 24 hours (text processing cache should be shorter than translation cache)
            success = self.redis.setex(cache_key, 24 * 3600, json.dumps(cache_data))
            return bool(success)
        except Exception as e:
            logger.error(f"Error caching result: {e}")
            return False

    def _apply_exclusions(
        self, result: dict[str, Any], excluded_words: set[str]
    ) -> dict[str, Any]:
        """Apply word exclusions to processing result."""
        if not excluded_words or "translations" not in result:
            return result

        # Filter out excluded words
        original_translations = result["translations"]
        filtered_translations = [
            t
            for t in original_translations
            if t.get("serbian_word", "").lower() not in excluded_words
        ]

        # Update counts
        filtered_count = len(original_translations) - len(filtered_translations)

        return {
            **result,
            "translations": filtered_translations,
            "new_words": len(filtered_translations),
            "excluded_count": filtered_count,
        }

    def _get_performance_rating(self, cache_hit_rate: float, avg_time: float) -> str:
        """Get a performance rating based on cache hit rate and processing time."""
        if cache_hit_rate >= 80 and avg_time < 1.0:
            return "Excellent"
        elif cache_hit_rate >= 60 and avg_time < 2.0:
            return "Good"
        elif cache_hit_rate >= 40 and avg_time < 3.0:
            return "Fair"
        else:
            return "Poor"

    def analyze_text_patterns(self, texts: list[str]) -> dict[str, Any]:
        """
        Analyze patterns in text for optimization insights.

        Args:
            texts: List of texts to analyze

        Returns:
            Analysis results with optimization suggestions
        """
        if not texts:
            return {"error": "No texts provided"}

        # Basic pattern analysis
        total_chars = sum(len(text) for text in texts)
        avg_length = total_chars / len(texts)

        # Word frequency analysis
        all_words = []
        for text in texts:
            words = text.lower().split()
            all_words.extend(words)

        word_freq = {}
        for word in all_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Most common words
        common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        # Estimate potential cache benefit
        unique_texts = len(set(texts))
        duplicate_rate = (len(texts) - unique_texts) / len(texts) * 100

        return {
            "text_count": len(texts),
            "unique_text_count": unique_texts,
            "duplicate_rate_percent": round(duplicate_rate, 2),
            "avg_text_length": round(avg_length, 1),
            "total_words": len(all_words),
            "unique_words": len(word_freq),
            "most_common_words": common_words[:10],
            "cache_benefit_estimate": (
                "High"
                if duplicate_rate > 20
                else "Medium"
                if duplicate_rate > 5
                else "Low"
            ),
            "optimization_suggestions": self._get_optimization_suggestions(
                duplicate_rate, avg_length
            ),
        }

    def _get_optimization_suggestions(
        self, duplicate_rate: float, avg_length: float
    ) -> list[str]:
        """Get optimization suggestions based on text analysis."""
        suggestions = []

        if duplicate_rate > 20:
            suggestions.append(
                "High duplicate rate - caching will provide significant performance benefits"
            )

        if avg_length > 2000:
            suggestions.append(
                "Long texts detected - consider text chunking for better processing"
            )

        if duplicate_rate < 5:
            suggestions.append(
                "Low duplicate rate - focus on vocabulary caching instead of text caching"
            )

        suggestions.append(
            "Consider preprocessing common text patterns during off-peak hours"
        )

        return suggestions


# Convenience function for creating optimized processor
def create_optimized_processor(openai_api_key: str, redis_client, **kwargs):
    """
    Create an optimized text processor with default settings.

    Args:
        openai_api_key: OpenAI API key
        redis_client: Redis client
        **kwargs: Additional arguments for the processor

    Returns:
        OptimizedSerbianTextProcessor instance
    """
    return OptimizedSerbianTextProcessor(openai_api_key, redis_client, **kwargs)


# Example usage and testing
def test_optimized_processor():
    """Test function for the optimized processor"""
    import os

    import redis

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return

    # Mock redis client for testing
    try:
        redis_client = redis.from_url("redis://localhost:6379/0")
        redis_client.ping()
    except:
        print("Redis not available - using mock client")
        from unittest.mock import MagicMock

        redis_client = MagicMock()

    processor = OptimizedSerbianTextProcessor(api_key, redis_client)

    # Test categories
    categories = [
        {"id": 1, "name": "Common Words"},
        {"id": 2, "name": "Verbs"},
        {"id": 3, "name": "Nouns"},
        {"id": 4, "name": "Adjectives"},
    ]

    # Test texts
    test_texts = [
        "Jutros sam ustao rano i pošao u grad.",
        "Kupovao sam hranu na pijaci. Prodavci su bili ljubazni.",
        "Video sam prijatelje na kafi. Razgovarali smo o filmu.",
        "Jutros sam ustao rano i pošao u grad.",  # Duplicate for cache testing
    ]

    print("🧠 Testing Optimized Serbian Text Processor...")

    # Test single text processing
    print("\n📄 Testing single text processing...")
    result = processor.process_text_optimized(test_texts[0], categories)
    print(f"✅ Processed {result.get('new_words', 0)} words")

    # Test batch processing
    print("\n📦 Testing batch processing...")
    batch_results = processor.batch_process_texts(test_texts, categories)
    print(f"✅ Batch processed {len(batch_results)} texts")

    # Test pattern analysis
    print("\n📊 Testing pattern analysis...")
    analysis = processor.analyze_text_patterns(test_texts)
    print(f"✅ Analysis: {analysis.get('duplicate_rate_percent', 0)}% duplicates")

    # Get performance stats
    print("\n📈 Performance statistics:")
    stats = processor.get_processing_stats()
    print(f"   Cache hit rate: {stats['processing_stats']['cache_hit_rate_percent']}%")
    print(
        f"   Avg processing time: {stats['processing_stats']['avg_processing_time_seconds']}s"
    )
    print(f"   Performance rating: {stats['performance_rating']}")

    print("\n🎉 Optimized processor testing completed!")


if __name__ == "__main__":
    test_optimized_processor()
