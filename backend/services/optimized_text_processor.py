"""
Optimized Text Processing Service
Dramatically improves word translation performance using intelligent caching and batch processing
"""

import json
import re
import logging
import time
import hashlib
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai

from .translation_cache import TranslationCache

logger = logging.getLogger(__name__)


class OptimizedTextProcessor:
    """
    High-performance text processor with intelligent caching and batch optimization
    """

    def __init__(self, redis_client, categories):
        self.translation_cache = TranslationCache(redis_client)
        self.categories = categories
        self.category_names = ", ".join([c.name for c in categories])

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "batch_efficiency": 0.0,
            "processing_time": 0.0,
        }

    def _tokenize_serbian_text(self, text: str) -> List[str]:
        """
        Advanced Serbian text tokenization with better word extraction
        """
        # Remove punctuation but preserve Serbian special characters
        text = re.sub(r'[.,!?;:\'"«»()[\]{}]', " ", text.lower())

        # Split on whitespace and filter out short tokens
        words = [
            word.strip() for word in re.split(r"\s+", text) if len(word.strip()) > 1
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)

        return unique_words

    def _prepare_translation_prompt(self, word: str) -> str:
        """
        Create optimized translation prompt for OpenAI
        """
        return f"""You are a Serbian-English translator and linguist. For the given Serbian word:
1. If it's a verb, convert it to infinitive form (e.g., "радим" → "радити", "идем" → "ићи")
2. Convert to lowercase UNLESS it's a proper noun (names of people, places, etc.)
3. Translate it to English
4. Categorize it into one of these categories: {self.category_names}

Respond in JSON format: {{"serbian_infinitive": "word in infinitive/base form", "translation": "english word", "category": "category name", "is_proper_noun": true/false}}

Serbian word: "{word}" """

    def _translate_word_openai(
        self, word: str, api_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Translate a single word using OpenAI with error handling and retry logic
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                completion = openai.ChatCompletion.create(
                    api_key=api_key,
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": self._prepare_translation_prompt(word),
                        }
                    ],
                    temperature=0.3,
                    max_tokens=150,
                    timeout=10,  # 10 second timeout
                )

                response = completion.choices[0].message["content"].strip()

                try:
                    parsed = json.loads(response)

                    # Find matching category
                    category = next(
                        (
                            c
                            for c in self.categories
                            if c.name.lower() == parsed["category"].lower()
                        ),
                        None,
                    )

                    return {
                        "serbian_word": parsed.get("serbian_infinitive", word),
                        "english_translation": parsed["translation"],
                        "category_id": category.id if category else 1,
                        "category_name": category.name if category else "Common Words",
                        "original_form": word,
                        "is_proper_noun": parsed.get("is_proper_noun", False),
                        "translation_quality": "high",
                        "source": "openai_gpt35",
                    }

                except json.JSONDecodeError:
                    logger.warning(
                        f"Failed to parse JSON response for '{word}': {response}"
                    )
                    return {
                        "serbian_word": word,
                        "english_translation": response[:100],  # Truncate if needed
                        "category_id": 1,
                        "category_name": "Common Words",
                        "original_form": word,
                        "translation_quality": "low",
                        "source": "openai_unparsed",
                    }

            except Exception as e:
                logger.warning(
                    f"Translation attempt {attempt + 1} failed for '{word}': {e}"
                )
                if attempt == max_retries - 1:
                    return {
                        "serbian_word": word,
                        "english_translation": "Translation failed",
                        "category_id": 1,
                        "category_name": "Common Words",
                        "original_form": word,
                        "translation_quality": "failed",
                        "error": str(e),
                        "source": "error",
                    }
                time.sleep(0.5)  # Brief pause before retry

        return None

    def _batch_translate_with_cache(
        self, words: List[str], api_key: str
    ) -> Tuple[List[Dict], Dict]:
        """
        Efficiently translate multiple words using cache-first approach with batch processing
        """
        start_time = time.time()

        # Step 1: Check cache for all words
        cached_results = self.translation_cache.get_batch(words)

        # Separate cached vs uncached words
        cached_translations = []
        uncached_words = []

        for word in words:
            cached_result = cached_results.get(word)
            if cached_result and "error" not in cached_result:
                cached_translations.append(cached_result)
                self.metrics["cache_hits"] += 1
            else:
                uncached_words.append(word)

        logger.info(
            f"Cache performance: {len(cached_translations)}/{len(words)} hits ({len(uncached_words)} to translate)"
        )

        # Step 2: Translate uncached words
        new_translations = []
        translations_to_cache = {}

        if uncached_words and api_key:
            # Use ThreadPoolExecutor for concurrent translations (limited concurrency)
            max_workers = min(3, len(uncached_words))  # Conservative concurrency

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit translation tasks
                future_to_word = {
                    executor.submit(self._translate_word_openai, word, api_key): word
                    for word in uncached_words
                }

                # Collect results as they complete
                for future in as_completed(future_to_word):
                    word = future_to_word[future]
                    try:
                        translation_result = future.result(timeout=15)
                        if translation_result:
                            new_translations.append(translation_result)
                            translations_to_cache[word] = translation_result
                            self.metrics["api_calls"] += 1
                    except Exception as e:
                        logger.error(f"Failed to translate '{word}': {e}")
                        # Add a fallback translation
                        fallback_translation = {
                            "serbian_word": word,
                            "english_translation": "Translation unavailable",
                            "category_id": 1,
                            "category_name": "Common Words",
                            "original_form": word,
                            "translation_quality": "unavailable",
                            "error": str(e),
                        }
                        new_translations.append(fallback_translation)

            # Step 3: Cache new translations
            if translations_to_cache:
                cached_count = self.translation_cache.set_batch(translations_to_cache)
                logger.info(f"Cached {cached_count} new translations")

        # Combine all translations
        all_translations = cached_translations + new_translations

        # Calculate performance metrics
        processing_time = time.time() - start_time
        cache_hit_rate = (len(cached_translations) / max(1, len(words))) * 100

        performance_metrics = {
            "total_words": len(words),
            "cache_hits": len(cached_translations),
            "new_translations": len(new_translations),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "processing_time_sec": round(processing_time, 2),
            "translations_per_second": round(len(words) / max(0.1, processing_time), 2),
            "api_calls_made": len(uncached_words),
        }

        return all_translations, performance_metrics

    def process_text(
        self, text: str, api_key: str, max_words: int = 50
    ) -> Dict[str, Any]:
        """
        Main text processing method with intelligent caching and optimization

        Args:
            text: Input Serbian text to process
            api_key: OpenAI API key for translation
            max_words: Maximum number of words to process (default 50)

        Returns:
            Dictionary with translation results and performance metrics
        """
        process_start_time = time.time()
        self.metrics["total_requests"] += 1

        if not text.strip():
            return {
                "total_words": 0,
                "existing_words": 0,
                "new_words": 0,
                "translations": [],
                "performance": {
                    "processing_time_sec": 0,
                    "cache_hit_rate": 0,
                    "error": "Empty text provided",
                },
            }

        if not api_key:
            return {
                "total_words": 0,
                "existing_words": 0,
                "new_words": 0,
                "translations": [],
                "performance": {
                    "processing_time_sec": 0,
                    "cache_hit_rate": 0,
                    "error": "OpenAI API key required",
                },
            }

        try:
            # Tokenize text
            words = self._tokenize_serbian_text(text)
            unique_words = words[:max_words]  # Limit to max_words

            logger.info(f"Processing {len(unique_words)} unique words from text")

            # Translate words using optimized batch processing
            translations, batch_metrics = self._batch_translate_with_cache(
                unique_words, api_key
            )

            # Update overall metrics
            self.metrics["batch_efficiency"] = batch_metrics["cache_hit_rate"]
            self.metrics["processing_time"] = batch_metrics["processing_time_sec"]

            # Calculate final metrics
            total_processing_time = time.time() - process_start_time

            performance_metrics = {
                **batch_metrics,
                "total_processing_time_sec": round(total_processing_time, 2),
                "tokenization_efficiency": f"{len(unique_words)}/{len(words)} unique",
                "overall_speed": f"{batch_metrics['translations_per_second']:.1f} words/sec",
            }

            result = {
                "total_words": len(words),
                "unique_words": len(unique_words),
                "existing_words": batch_metrics["cache_hits"],  # Words found in cache
                "new_words": batch_metrics[
                    "new_translations"
                ],  # Newly translated words
                "translations": translations,
                "performance": performance_metrics,
                "cache_stats": self.translation_cache.get_stats(),
            }

            logger.info(
                f"Text processing completed: {len(translations)} translations in {total_processing_time:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return {
                "total_words": 0,
                "existing_words": 0,
                "new_words": 0,
                "translations": [],
                "performance": {
                    "processing_time_sec": time.time() - process_start_time,
                    "cache_hit_rate": 0,
                    "error": str(e),
                },
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics for the text processor"""
        cache_stats = self.translation_cache.get_stats()

        return {
            "processor_metrics": self.metrics,
            "cache_metrics": cache_stats,
            "efficiency_rating": cache_stats.get("cache_efficiency", "Unknown"),
            "recommendations": self._get_performance_recommendations(cache_stats),
        }

    def _get_performance_recommendations(self, cache_stats: Dict) -> List[str]:
        """Generate performance recommendations based on current metrics"""
        recommendations = []

        hit_rate = cache_stats.get("hit_rate_percent", 0)
        if hit_rate < 50:
            recommendations.append(
                "Consider pre-warming cache with common Serbian words"
            )
        elif hit_rate < 80:
            recommendations.append(
                "Cache performance is good, consider increasing cache TTL"
            )
        else:
            recommendations.append(
                "Excellent cache performance! No immediate optimizations needed"
            )

        cache_size = cache_stats.get("cache_size", 0)
        if cache_size > 10000:
            recommendations.append(
                "Large cache size detected, consider periodic cleanup"
            )

        return recommendations

    def warm_cache_with_common_words(
        self, common_words: List[str], api_key: str
    ) -> Dict[str, Any]:
        """
        Pre-populate cache with common Serbian words for better performance

        Args:
            common_words: List of common Serbian words to pre-translate
            api_key: OpenAI API key

        Returns:
            Results of cache warming operation
        """
        logger.info(f"Starting cache warming with {len(common_words)} common words")

        # Only translate words not already in cache
        cached_results = self.translation_cache.get_batch(common_words)
        uncached_words = [word for word, result in cached_results.items() if not result]

        if not uncached_words:
            logger.info("All common words already cached")
            return {
                "already_cached": len(common_words),
                "newly_cached": 0,
                "total_processed": len(common_words),
            }

        # Translate uncached words in smaller batches to avoid overwhelming the API
        batch_size = 20
        total_cached = 0

        for i in range(0, len(uncached_words), batch_size):
            batch = uncached_words[i : i + batch_size]
            logger.info(
                f"Processing cache warming batch {i // batch_size + 1}/{(len(uncached_words) + batch_size - 1) // batch_size}"
            )

            translations, metrics = self._batch_translate_with_cache(batch, api_key)
            total_cached += metrics["new_translations"]

            # Small delay between batches to be respectful to the API
            if i + batch_size < len(uncached_words):
                time.sleep(1)

        logger.info(f"Cache warming completed: {total_cached} new translations cached")

        return {
            "already_cached": len(common_words) - len(uncached_words),
            "newly_cached": total_cached,
            "total_processed": len(common_words),
            "cache_stats": self.translation_cache.get_stats(),
        }
