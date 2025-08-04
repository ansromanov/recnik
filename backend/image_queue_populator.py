#!/usr/bin/env python3
"""
Image Queue Populator Service
Automatically populates the image processing queue with words from:
1. All user vocabularies
2. Top 100 words
"""

from datetime import datetime, timedelta
import json
import time

from flask import Flask
import redis

import config
from models import UserVocabulary, Word, db


class ImageQueuePopulator:
    def __init__(self):
        self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
        self.queue_key = "image_queue"
        self.population_lock_key = "image_queue_population_lock"

        # Initialize Flask app for database access
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(self.app)

        print("🚀 Image Queue Populator initialized")

    def _generate_cache_key(self, word):
        """Generate cache key to check if image already exists"""
        import hashlib

        return f"word_image:{hashlib.md5(word.lower().encode()).hexdigest()}"

    def _is_word_already_cached(self, serbian_word):
        """Check if word already has a cached image"""
        try:
            cache_key = self._generate_cache_key(serbian_word)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                cached_result = json.loads(cached_data)
                # Return True if we have a successful cache (not an error)
                return "error" not in cached_result
            return False
        except Exception as e:
            print(f"Error checking cache for {serbian_word}: {e}")
            return False

    def _is_word_in_queue(self, serbian_word):
        """Check if word is already in the processing queue using a tracking set"""
        try:
            # Use a Redis set to track queued words for efficient lookups
            queued_words_set_key = f"{self.queue_key}_words_set"
            is_queued = self.redis_client.sismember(queued_words_set_key, serbian_word)
            return bool(is_queued)
        except Exception as e:
            print(f"Error checking queue for {serbian_word}: {e}")
            return False

    def _add_word_to_queue(
        self, serbian_word, english_translation, word_type="vocabulary"
    ):
        """Add a word to the image processing queue"""
        # Skip if already cached or in queue
        if self._is_word_already_cached(serbian_word):
            return False

        if self._is_word_in_queue(serbian_word):
            return False

        try:
            queue_item = {
                "serbian_word": serbian_word,
                "english_translation": english_translation,
                "added_at": int(time.time()),
                "source": word_type,
                "auto_populated": True,
            }

            # Add to queue and tracking set atomically
            queued_words_set_key = f"{self.queue_key}_words_set"
            pipe = self.redis_client.pipeline()
            pipe.lpush(self.queue_key, json.dumps(queue_item))
            pipe.sadd(queued_words_set_key, serbian_word)
            pipe.execute()

            print(f"➕ Added '{serbian_word}' ({word_type}) to queue")
            return True

        except Exception as e:
            print(f"❌ Failed to add '{serbian_word}' to queue: {e}")
            return False

    def populate_user_vocabulary_words(self):
        """Populate queue with words from all user vocabularies"""
        print("\n📚 Populating user vocabulary words...")

        with self.app.app_context():
            try:
                # Get all unique words from user vocabularies
                user_vocab_words = (
                    db.session.query(Word).join(UserVocabulary).distinct().all()
                )

                added_count = 0
                total_count = len(user_vocab_words)

                print(f"Found {total_count} unique words in user vocabularies")

                for word in user_vocab_words:
                    if self._add_word_to_queue(
                        word.serbian_word, word.english_translation, "user_vocabulary"
                    ):
                        added_count += 1

                print(
                    f"✅ Added {added_count}/{total_count} user vocabulary words to queue"
                )
                return added_count

            except Exception as e:
                print(f"❌ Error populating user vocabulary words: {e}")
                return 0

    def populate_top_100_words(self):
        """Populate queue with top 100 words"""
        print("\n🔥 Populating top 100 words...")

        with self.app.app_context():
            try:
                # Get all top 100 words
                top_100_words = Word.query.filter_by(is_top_100=True).all()

                added_count = 0
                total_count = len(top_100_words)

                print(f"Found {total_count} top 100 words")

                for word in top_100_words:
                    if self._add_word_to_queue(
                        word.serbian_word, word.english_translation, "top_100"
                    ):
                        added_count += 1

                print(f"✅ Added {added_count}/{total_count} top 100 words to queue")
                return added_count

            except Exception as e:
                print(f"❌ Error populating top 100 words: {e}")
                return 0

    def populate_recent_words(self, days=7):
        """Populate queue with recently added words"""
        print(f"\n🆕 Populating words added in last {days} days...")

        with self.app.app_context():
            try:
                # Get words added in the last N days
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                recent_words = Word.query.filter(Word.created_at >= cutoff_date).all()

                added_count = 0
                total_count = len(recent_words)

                print(f"Found {total_count} recent words")

                for word in recent_words:
                    if self._add_word_to_queue(
                        word.serbian_word, word.english_translation, "recent"
                    ):
                        added_count += 1

                print(f"✅ Added {added_count}/{total_count} recent words to queue")
                return added_count

            except Exception as e:
                print(f"❌ Error populating recent words: {e}")
                return 0

    def get_queue_status(self):
        """Get current queue status"""
        try:
            queue_length = self.redis_client.llen(self.queue_key)

            # Count cached images
            cache_keys = self.redis_client.keys("word_image:*")
            cache_count = len(cache_keys)

            # Check rate limit
            current_hour = int(time.time() // 3600)
            rate_key = f"unsplash_rate_limit:{current_hour}"
            current_requests = self.redis_client.get(rate_key)
            current_requests = int(current_requests) if current_requests else 0

            return {
                "queue_length": queue_length,
                "cached_images": cache_count,
                "requests_this_hour": current_requests,
                "max_requests_per_hour": 25,
            }

        except Exception as e:
            print(f"Error getting queue status: {e}")
            return {}

    def run_population_cycle(self):
        """Run a complete population cycle"""
        print("🔄 Starting image queue population cycle")
        print("=" * 50)

        # Try to acquire population lock
        lock_acquired = self.redis_client.set(
            self.population_lock_key,
            "locked",
            ex=300,  # 5 minutes
            nx=True,
        )

        if not lock_acquired:
            print("⏸️  Another population process is running, skipping...")
            return

        try:
            # Show initial status
            initial_status = self.get_queue_status()
            print(
                f"📊 Initial status: Queue={initial_status.get('queue_length', 0)}, "
                f"Cached={initial_status.get('cached_images', 0)}"
            )

            total_added = 0

            # Populate different word types
            total_added += self.populate_top_100_words()
            total_added += self.populate_user_vocabulary_words()
            total_added += self.populate_recent_words(days=7)

            # Show final status
            final_status = self.get_queue_status()
            print(
                f"\n📊 Final status: Queue={final_status.get('queue_length', 0)}, "
                f"Cached={final_status.get('cached_images', 0)}"
            )

            print(f"\n✅ Population cycle complete! Added {total_added} words to queue")

            if total_added > 0:
                print("🎯 Image sync service will now process these words automatically")
                print("📝 Monitor progress: docker-compose logs -f image-sync-service")
            else:
                print("ℹ️  No new words added - all words are already cached or queued")

        finally:
            # Release lock
            self.redis_client.delete(self.population_lock_key)

    def run_continuous(self, interval_minutes=60):
        """Run population continuously at specified intervals"""
        print(f"🔁 Starting continuous population (every {interval_minutes} minutes)")

        while True:
            try:
                self.run_population_cycle()

                print(
                    f"\n⏰ Waiting {interval_minutes} minutes until next population cycle..."
                )
                time.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                print("\n🛑 Received shutdown signal")
                break
            except Exception as e:
                print(f"❌ Error in continuous run: {e}")
                print(f"⏰ Waiting {interval_minutes} minutes before retry...")
                time.sleep(interval_minutes * 60)

        print("👋 Image Queue Populator stopped")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Populate Image Processing Queue")
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuously (default: run once)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Minutes between population cycles (default: 60)",
    )
    parser.add_argument(
        "--top100-only", action="store_true", help="Only populate top 100 words"
    )
    parser.add_argument(
        "--vocab-only", action="store_true", help="Only populate user vocabulary words"
    )
    parser.add_argument(
        "--recent-only", action="store_true", help="Only populate recent words"
    )

    args = parser.parse_args()

    populator = ImageQueuePopulator()

    if args.continuous:
        populator.run_continuous(args.interval)
    else:
        # Run once based on options
        if args.top100_only:
            populator.populate_top_100_words()
        elif args.vocab_only:
            populator.populate_user_vocabulary_words()
        elif args.recent_only:
            populator.populate_recent_words()
        else:
            populator.run_population_cycle()


if __name__ == "__main__":
    main()
