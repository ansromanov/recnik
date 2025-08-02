import json
import redis
import openai
from typing import List, Optional, Dict
import random
from datetime import datetime, timedelta, timezone


class SentenceCacheService:
    """Service for caching example sentences for vocabulary words"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.cache_prefix = "sentence_cache:"
        self.cache_ttl = 86400 * 7  # 7 days in seconds
        self.sentences_per_word = 3  # Cache 2-3 sentences per word

    def _get_cache_key(self, serbian_word: str, english_translation: str) -> str:
        """Generate cache key for a word pair"""
        return (
            f"{self.cache_prefix}{serbian_word.lower()}:{english_translation.lower()}"
        )

    def get_cached_sentences(
        self, serbian_word: str, english_translation: str
    ) -> Optional[List[Dict]]:
        """Get cached sentences for a word (returns list of {serbian, english} pairs)"""
        try:
            cache_key = self._get_cache_key(serbian_word, english_translation)
            cached_data = self.redis.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                sentences = data.get("sentences", [])

                # Handle backward compatibility - convert old format to new format
                if sentences and isinstance(sentences[0], str):
                    # Old format: list of Serbian strings
                    sentences = [{"serbian": s, "english": ""} for s in sentences]

                return sentences

            return None
        except Exception as e:
            print(f"Error getting cached sentences: {e}")
            return None

    def get_random_sentence(
        self, serbian_word: str, english_translation: str
    ) -> Optional[Dict]:
        """Get a random cached sentence pair for a word"""
        sentences = self.get_cached_sentences(serbian_word, english_translation)
        if sentences:
            return random.choice(sentences)
        return None

    def cache_sentences(
        self, serbian_word: str, english_translation: str, sentences: List[Dict]
    ) -> bool:
        """Cache sentence pairs for a word (each sentence is {serbian, english})"""
        try:
            cache_key = self._get_cache_key(serbian_word, english_translation)
            cache_data = {
                "sentences": sentences,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "serbian_word": serbian_word,
                "english_translation": english_translation,
            }

            self.redis.setex(
                cache_key, self.cache_ttl, json.dumps(cache_data, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"Error caching sentences: {e}")
            return False

    def generate_and_cache_sentences(
        self,
        serbian_word: str,
        english_translation: str,
        api_key: str,
        category_name: str = None,
    ) -> List[Dict]:
        """Generate and cache sentence pairs (Serbian + English) for a word using OpenAI"""
        try:
            # Create prompt for generating sentence pairs
            category_context = f" (category: {category_name})" if category_name else ""

            prompt = f"""Generate {self.sentences_per_word} different example sentences using the Serbian word "{serbian_word}" ({english_translation}){category_context}.

For each sentence, provide BOTH the Serbian version AND its English translation.

Format your response EXACTLY like this:
Serbian: [Serbian sentence]
English: [English translation]

Serbian: [Serbian sentence]
English: [English translation]

Requirements:
- Each Serbian sentence should be simple and educational for Serbian learners
- Use natural, conversational Serbian
- Make the word's meaning clear from context
- Vary sentence structures and contexts
- Each sentence should be 6-15 words long
- English translations should be natural and accurate
- Do not number the sentences

Word: {serbian_word} ({english_translation})
Generate {self.sentences_per_word} sentence pairs:"""

            completion = openai.ChatCompletion.create(
                api_key=api_key,
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Serbian language teacher creating example sentences with English translations for vocabulary learning. Generate natural, educational sentence pairs that help students understand word usage in both languages.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            response = completion.choices[0].message["content"].strip()

            # Parse sentence pairs from response
            sentence_pairs = []
            lines = response.split("\n")

            i = 0
            while i < len(lines) and len(sentence_pairs) < self.sentences_per_word:
                serbian_line = lines[i].strip()

                # Look for Serbian sentence
                if serbian_line.lower().startswith("serbian:"):
                    serbian_sentence = serbian_line[
                        8:
                    ].strip()  # Remove "Serbian:" prefix

                    # Look for corresponding English translation
                    if i + 1 < len(lines):
                        english_line = lines[i + 1].strip()
                        if english_line.lower().startswith("english:"):
                            english_sentence = english_line[
                                8:
                            ].strip()  # Remove "English:" prefix

                            # Validate sentences
                            if (
                                serbian_sentence
                                and len(serbian_sentence) > 10
                                and english_sentence
                                and len(english_sentence) > 5
                            ):
                                sentence_pairs.append(
                                    {
                                        "serbian": serbian_sentence,
                                        "english": english_sentence,
                                    }
                                )

                            i += 2  # Skip both lines
                            continue

                i += 1

            # Ensure we have at least one sentence pair
            if not sentence_pairs:
                sentence_pairs = [
                    {
                        "serbian": f"{serbian_word} је важна реч у српском језику.",
                        "english": f"{serbian_word} is an important word in Serbian language.",
                    }
                ]

            # Limit to desired number of sentence pairs
            sentence_pairs = sentence_pairs[: self.sentences_per_word]

            # Cache the sentence pairs
            self.cache_sentences(serbian_word, english_translation, sentence_pairs)

            return sentence_pairs

        except Exception as e:
            print(f"Error generating sentences for {serbian_word}: {e}")
            # Return a fallback sentence pair
            return [
                {
                    "serbian": f"Ово је пример реченице са речју {serbian_word}.",
                    "english": f"This is an example sentence with the word {serbian_word}.",
                }
            ]

    def warm_cache_for_words(
        self, words_data: List[Dict], api_key: str, batch_size: int = 5
    ) -> int:
        """Warm cache for multiple words in batches"""
        cached_count = 0

        for i in range(0, len(words_data), batch_size):
            batch = words_data[i : i + batch_size]

            for word_data in batch:
                serbian_word = word_data.get("serbian_word")
                english_translation = word_data.get("english_translation")
                category_name = word_data.get("category_name")

                if not serbian_word or not english_translation:
                    continue

                # Check if already cached
                if self.get_cached_sentences(serbian_word, english_translation):
                    continue

                try:
                    sentence_pairs = self.generate_and_cache_sentences(
                        serbian_word, english_translation, api_key, category_name
                    )
                    if sentence_pairs:
                        cached_count += 1
                        print(
                            f"Cached {len(sentence_pairs)} sentence pairs for: {serbian_word}"
                        )
                except Exception as e:
                    print(f"Error caching sentences for {serbian_word}: {e}")
                    continue

        return cached_count

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            # Count cache entries
            cache_keys = self.redis.keys(f"{self.cache_prefix}*")
            total_cached = len(cache_keys)

            # Sample some entries to check content
            sample_size = min(10, total_cached)
            total_sentences = 0

            if cache_keys:
                sample_keys = random.sample(cache_keys, sample_size)
                for key in sample_keys:
                    try:
                        data = json.loads(self.redis.get(key))
                        total_sentences += len(data.get("sentences", []))
                    except:
                        pass

                avg_sentences = total_sentences / sample_size if sample_size > 0 else 0
                estimated_total_sentences = int(avg_sentences * total_cached)
            else:
                estimated_total_sentences = 0

            return {
                "total_cached_words": total_cached,
                "estimated_total_sentences": estimated_total_sentences,
                "average_sentences_per_word": round(
                    estimated_total_sentences / total_cached, 1
                )
                if total_cached > 0
                else 0,
                "cache_ttl_days": self.cache_ttl / 86400,
                "sentences_per_word_target": self.sentences_per_word,
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {
                "total_cached_words": 0,
                "estimated_total_sentences": 0,
                "average_sentences_per_word": 0,
                "cache_ttl_days": 7,
                "sentences_per_word_target": self.sentences_per_word,
                "error": str(e),
            }

    def clear_cache(self, word_pattern: str = None) -> int:
        """Clear sentence cache"""
        try:
            if word_pattern:
                pattern = f"{self.cache_prefix}*{word_pattern.lower()}*"
            else:
                pattern = f"{self.cache_prefix}*"

            keys = self.redis.keys(pattern)
            if keys:
                deleted = self.redis.delete(*keys)
                return deleted
            return 0
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return 0

    def populate_user_vocabulary_cache(
        self, user_words: List[Dict], api_key: str
    ) -> Dict:
        """Populate cache for user's vocabulary words"""
        try:
            # Filter words that don't have cached sentences
            words_to_cache = []
            already_cached = 0

            for word_data in user_words:
                serbian_word = word_data.get("serbian_word")
                english_translation = word_data.get("english_translation")

                if not serbian_word or not english_translation:
                    continue

                if self.get_cached_sentences(serbian_word, english_translation):
                    already_cached += 1
                else:
                    words_to_cache.append(word_data)

            # Cache sentences for words that need them
            newly_cached = self.warm_cache_for_words(words_to_cache, api_key)

            return {
                "success": True,
                "total_words": len(user_words),
                "already_cached": already_cached,
                "newly_cached": newly_cached,
                "words_to_cache": len(words_to_cache),
            }

        except Exception as e:
            print(f"Error populating vocabulary cache: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_words": len(user_words) if user_words else 0,
                "already_cached": 0,
                "newly_cached": 0,
                "words_to_cache": 0,
            }
