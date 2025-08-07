#!/usr/bin/env python3
"""
Standalone Image Sync Service
A dedicated service for fetching and caching images from Unsplash with detailed logging.
"""

import base64
import hashlib
import io
import json
import logging
import os
import sys
import time

from dotenv import load_dotenv
from PIL import Image
import redis
import requests

# Load environment variables
load_dotenv()

# Import configuration
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend-service"))
try:
    from config import RATE_LIMIT_WINDOW, UNSPLASH_RATE_LIMIT
except ImportError:
    # Fallback values if config import fails
    UNSPLASH_RATE_LIMIT = 50
    RATE_LIMIT_WINDOW = 3600


class ImageSyncService:
    def __init__(self, redis_client, logger):
        self.redis_client = redis_client
        self.logger = logger
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")

        if not self.unsplash_access_key:
            self.logger.error("UNSPLASH_ACCESS_KEY not found in environment variables")
            raise ValueError("Missing Unsplash API key")

        self.logger.info(f"Initialized with Unsplash key: {self.unsplash_access_key[:10]}...")

        self.headers = {
            "User-Agent": os.getenv("IMAGE_USER_AGENT", "Recnik Image Sync/1.0"),
            "Accept": "application/json",
        }

        # Unsplash API endpoints
        self.unsplash_search_url = "https://api.unsplash.com/search/photos"
        self.unsplash_timeout = int(os.getenv("UNSPLASH_TIMEOUT", "10"))

        # Rate limiting - configurable
        self.rate_limit_key = "unsplash_rate_limit"
        self.max_requests_per_hour = UNSPLASH_RATE_LIMIT
        self.rate_limit_window = RATE_LIMIT_WINDOW

        # Background processing
        self.background_queue_key = "image_queue"
        self.priority_queue_key = "image_queue_priority"
        self.processing_lock_key = "image_processing_lock"

        # Statistics
        self.stats = {
            "processed_words": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "cache_hits": 0,
            "api_requests": 0,
            "start_time": time.time(),
        }

        self.logger.info("Image Sync Service initialized successfully")

    def _generate_cache_key(self, word):
        """Generate a cache key for the word"""
        return f"word_image:{hashlib.md5(word.lower().encode()).hexdigest()}"

    def _get_rate_limit_info(self):
        """Get current rate limit status"""
        try:
            current_hour = int(time.time() // self.rate_limit_window)
            rate_key = f"{self.rate_limit_key}:{current_hour}"
            current_count = self.redis_client.get(rate_key)
            count = int(current_count) if current_count else 0
            self.logger.debug(f"Current rate limit: {count}/{self.max_requests_per_hour}")
            return count
        except Exception as e:
            self.logger.error(f"Error getting rate limit info: {e}")
            return 0

    def _increment_rate_limit(self):
        """Increment rate limit counter"""
        try:
            current_hour = int(time.time() // self.rate_limit_window)
            rate_key = f"{self.rate_limit_key}:{current_hour}"
            current_count = self.redis_client.incr(rate_key)

            # Set expiration for the key
            if current_count == 1:
                self.redis_client.expire(rate_key, self.rate_limit_window * 2)

            self.stats["api_requests"] += 1
            self.logger.info(
                f"API request #{current_count} this hour (limit: {self.max_requests_per_hour})"
            )
            return current_count
        except Exception as e:
            self.logger.error(f"Error incrementing rate limit: {e}")
            return 999

    def _can_make_request(self):
        """Check if we can make another API request"""
        current_count = self._get_rate_limit_info()
        can_make = current_count < self.max_requests_per_hour
        if not can_make:
            self.logger.warning(f"Rate limit reached: {current_count}/{self.max_requests_per_hour}")
        return can_make

    def _search_unsplash_images(self, query, max_results=3):
        """Search Unsplash for images matching the query"""
        if not self._can_make_request():
            self.logger.warning(f"Rate limit reached, skipping search for: {query}")
            return []

        try:
            request_count = self._increment_rate_limit()
            self.logger.info(f"🔍 Searching Unsplash for: '{query}' (request #{request_count})")

            params = {
                "query": query,
                "per_page": max_results,
                "orientation": "squarish",
                "content_filter": "high",
                "order_by": "relevant",
            }

            headers = {
                **self.headers,
                "Authorization": f"Client-ID {self.unsplash_access_key}",
            }

            response = requests.get(
                self.unsplash_search_url,
                params=params,
                headers=headers,
                timeout=self.unsplash_timeout,
            )
            response.raise_for_status()

            data = response.json()
            images = []

            self.logger.info(f"Found {len(data.get('results', []))} results for '{query}'")

            for i, photo in enumerate(data.get("results", [])):
                try:
                    urls = photo.get("urls", {})
                    image_url = urls.get("small") or urls.get("regular") or urls.get("thumb")

                    if not image_url:
                        self.logger.warning(f"No valid URL found for result #{i + 1}")
                        continue

                    photographer = photo.get("user", {}).get("name", "Unknown")
                    unsplash_id = photo.get("id", "")

                    images.append(
                        {
                            "url": image_url,
                            "width": photo.get("width", 400),
                            "height": photo.get("height", 400),
                            "alt": photo.get("alt_description", ""),
                            "description": photo.get("description", ""),
                            "photographer": photographer,
                            "unsplash_id": unsplash_id,
                        }
                    )

                    self.logger.debug(f"Result #{i + 1}: {image_url} by {photographer}")

                except Exception as e:
                    self.logger.error(f"Error processing photo result #{i + 1}: {e}")
                    continue

            self.logger.info(f"✅ Successfully processed {len(images)} images for '{query}'")
            return images

        except Exception as e:
            self.logger.error(f"❌ Error searching Unsplash for '{query}': {e}")
            return []

    def _download_and_process_image(self, image_info, word):
        """Download and process an image"""
        try:
            image_url = image_info["url"]
            photographer = image_info.get("photographer", "Unknown")

            self.logger.info(f"📥 Downloading image for '{word}' from {photographer}")
            self.logger.debug(f"Image URL: {image_url}")

            response = requests.get(image_url, headers=self.headers, timeout=15, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                self.logger.warning(f"Invalid content type: {content_type}")
                return None

            image_data = response.content
            original_size = len(image_data)
            self.logger.debug(f"Downloaded {original_size} bytes")

            with Image.open(io.BytesIO(image_data)) as img:
                original_dims = f"{img.width}x{img.height}"

                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                    self.logger.debug("Converted image mode to RGB")

                max_size = int(os.getenv("IMAGE_MAX_SIZE", "400"))
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    self.logger.debug(f"Resized from {original_dims} to {img.width}x{img.height}")

                output = io.BytesIO()
                img.save(
                    output,
                    format="JPEG",
                    quality=int(os.getenv("IMAGE_QUALITY", "85")),
                    optimize=True,
                )
                processed_data = output.getvalue()
                final_size = len(processed_data)

                compression_ratio = (1 - final_size / original_size) * 100
                self.logger.info(
                    f"✅ Processed image: {original_dims} → {img.width}x{img.height}, "
                    f"{original_size} → {final_size} bytes ({compression_ratio:.1f}% compression)"
                )

                return {
                    "data": base64.b64encode(processed_data).decode("utf-8"),
                    "content_type": "image/jpeg",
                    "width": img.width,
                    "height": img.height,
                    "size": final_size,
                    "photographer": image_info.get("photographer", ""),
                    "unsplash_id": image_info.get("unsplash_id", ""),
                    "alt_description": image_info.get("alt", ""),
                }

        except Exception as e:
            self.logger.error(f"❌ Error downloading/processing image for '{word}': {e}")
            return None

    def process_word(self, serbian_word, english_translation=None):
        """Process a single word for image search"""
        start_time = time.time()
        self.logger.info(f"🔄 Processing word: '{serbian_word}' ({english_translation})")

        cache_key = self._generate_cache_key(serbian_word)

        # Check if already cached
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                cached_result = json.loads(cached_data)
                if "error" not in cached_result:
                    self.stats["cache_hits"] += 1
                    self.logger.info(f"✅ Cache hit for '{serbian_word}' - skipping")
                    return
                else:
                    # Check if enough time passed to retry failed searches
                    cached_at = cached_result.get("cached_at", 0)
                    hours_since_cache = (time.time() - cached_at) / 3600
                    if hours_since_cache < 24:
                        self.logger.info(
                            f"⏭️  Recent failure cached for '{serbian_word}' ({hours_since_cache:.1f}h ago) - skipping"
                        )
                        return
                    else:
                        self.logger.info(
                            f"🔄 Retrying failed search for '{serbian_word}' (cached {hours_since_cache:.1f}h ago)"
                        )
        except Exception as e:
            self.logger.error(f"Error checking cache for '{serbian_word}': {e}")

        # Build search queries
        search_queries = []
        if english_translation:
            search_queries.append(english_translation)

            # Add category-specific searches
            common_categories = {
                "food",
                "animal",
                "house",
                "car",
                "tree",
                "flower",
                "book",
                "water",
                "fire",
                "sun",
                "moon",
                "mountain",
                "river",
                "sea",
            }

            if any(cat in english_translation.lower() for cat in common_categories):
                search_queries.append(f"{english_translation} object")

        search_queries.append(serbian_word)

        self.logger.debug(f"Search queries for '{serbian_word}': {search_queries}")

        best_image = None

        # Try each search query
        for i, query in enumerate(search_queries):
            if not self._can_make_request():
                self.logger.warning(f"Rate limit reached, stopping search for '{serbian_word}'")
                break

            self.logger.info(f"🔍 Search attempt {i + 1}/{len(search_queries)}: '{query}'")
            images = self._search_unsplash_images(query, max_results=2)

            if not images:
                self.logger.info(f"No images found for query: '{query}'")
                continue

            # Try to download first image
            img_info = images[0]
            processed_image = self._download_and_process_image(img_info, serbian_word)
            if processed_image:
                best_image = {
                    "image_data": processed_image["data"],
                    "content_type": processed_image["content_type"],
                    "width": processed_image["width"],
                    "height": processed_image["height"],
                    "size": processed_image["size"],
                    "search_query": query,
                    "photographer": processed_image.get("photographer", ""),
                    "unsplash_id": processed_image.get("unsplash_id", ""),
                    "alt_description": processed_image.get("alt_description", ""),
                    "cached_at": int(time.time()),
                    "source": "unsplash",
                }
                self.logger.info(
                    f"✅ Successfully found image for '{serbian_word}' using query: '{query}'"
                )
                break
            else:
                self.logger.warning(f"Failed to download image for query: '{query}'")

        # Cache result
        cache_data = best_image or {
            "error": "No suitable image found",
            "cached_at": int(time.time()),
        }

        try:
            # Cache for 30 days
            cache_ttl = 30 * 24 * 60 * 60
            self.redis_client.setex(cache_key, cache_ttl, json.dumps(cache_data))

            if best_image:
                self.stats["successful_downloads"] += 1
                self.logger.info(f"✅ Cached successful result for '{serbian_word}' (TTL: 30 days)")
            else:
                self.stats["failed_downloads"] += 1
                self.logger.warning(f"❌ Cached failure for '{serbian_word}' (TTL: 30 days)")

        except Exception as e:
            self.logger.error(f"Error caching result for '{serbian_word}': {e}")

        self.stats["processed_words"] += 1
        processing_time = time.time() - start_time
        self.logger.info(f"⏱️  Processed '{serbian_word}' in {processing_time:.2f}s")

    def get_queue_item(self):
        """Get next item from processing queue - priority queue first"""
        try:
            # First check priority queue
            queue_item_json = self.redis_client.rpop(self.priority_queue_key)
            if queue_item_json:
                queue_item = json.loads(queue_item_json)
                # Remove from tracking set
                self._remove_from_tracking_set(queue_item.get("serbian_word"))
                self.logger.info(
                    f"🔥 Processing HIGH PRIORITY item: {queue_item.get('serbian_word')}"
                )
                return queue_item

            # If no priority items, check regular queue
            queue_item_json = self.redis_client.rpop(self.background_queue_key)
            if not queue_item_json:
                return None

            queue_item = json.loads(queue_item_json)
            # Remove from tracking set
            self._remove_from_tracking_set(queue_item.get("serbian_word"))
            return queue_item
        except Exception as e:
            self.logger.error(f"Error getting queue item: {e}")
            return None

    def _remove_from_tracking_set(self, serbian_word):
        """Remove word from the tracking set when processed"""
        try:
            if serbian_word:
                queued_words_set_key = f"{self.background_queue_key}_words_set"
                self.redis_client.srem(queued_words_set_key, serbian_word)
        except Exception as e:
            self.logger.error(f"Error removing {serbian_word} from tracking set: {e}")

    def get_queue_length(self):
        """Get current queue lengths"""
        try:
            regular_length = self.redis_client.llen(self.background_queue_key)
            priority_length = self.redis_client.llen(self.priority_queue_key)
            return {
                "regular": regular_length,
                "priority": priority_length,
                "total": regular_length + priority_length,
            }
        except Exception as e:
            self.logger.error(f"Error getting queue length: {e}")
            return {"regular": 0, "priority": 0, "total": 0}

    def acquire_processing_lock(self, timeout=300):
        """Acquire distributed processing lock"""
        try:
            lock_acquired = self.redis_client.set(
                self.processing_lock_key, "locked", ex=timeout, nx=True
            )
            if lock_acquired:
                self.logger.debug("Acquired processing lock")
            return lock_acquired
        except Exception as e:
            self.logger.error(f"Error acquiring lock: {e}")
            return False

    def release_processing_lock(self):
        """Release distributed processing lock"""
        try:
            self.redis_client.delete(self.processing_lock_key)
            self.logger.debug("Released processing lock")
        except Exception as e:
            self.logger.error(f"Error releasing lock: {e}")

    def log_stats(self):
        """Log current statistics"""
        uptime = time.time() - self.stats["start_time"]
        rate_info = self._get_rate_limit_info()
        queue_length = self.get_queue_length()

        self.logger.info("📊 === IMAGE SYNC STATISTICS ===")
        self.logger.info(f"Uptime: {uptime / 3600:.1f} hours")
        self.logger.info(f"Words processed: {self.stats['processed_words']}")
        self.logger.info(f"Successful downloads: {self.stats['successful_downloads']}")
        self.logger.info(f"Failed downloads: {self.stats['failed_downloads']}")
        self.logger.info(f"Cache hits: {self.stats['cache_hits']}")
        self.logger.info(f"API requests: {self.stats['api_requests']}")
        self.logger.info(f"Current rate limit: {rate_info}/{self.max_requests_per_hour}")
        self.logger.info(f"Queue length: {queue_length}")

        success_rate = (
            self.stats["successful_downloads"] / max(1, self.stats["processed_words"])
        ) * 100
        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info("=================================")

    def run(self):
        """Main processing loop"""
        self.logger.info("🚀 Starting Image Sync Service")
        self.logger.info(f"Rate limit: {self.max_requests_per_hour} requests/hour")
        self.logger.info("Processing interval: 30 seconds")

        last_stats_log = time.time()

        while True:
            try:
                # Log stats every 10 minutes
                if time.time() - last_stats_log > 600:
                    self.log_stats()
                    last_stats_log = time.time()

                # Check rate limit
                if not self._can_make_request():
                    wait_minutes = 2
                    self.logger.info(f"⏸️  Rate limit reached, waiting {wait_minutes} minutes...")
                    time.sleep(wait_minutes * 5)
                    continue

                # Try to acquire processing lock
                if not self.acquire_processing_lock():
                    self.logger.debug("Another instance is processing, waiting...")
                    time.sleep(60)
                    continue

                # Get item from queue
                queue_item = self.get_queue_item()

                if not queue_item:
                    queue_length = self.get_queue_length()
                    if queue_length["total"] == 0:
                        self.logger.info("📭 Queue empty, waiting for new items...")
                    else:
                        self.logger.warning(
                            f"Failed to get item from queue (priority: {queue_length['priority']}, regular: {queue_length['regular']})"
                        )

                    self.release_processing_lock()
                    time.sleep(30)
                    continue

                # Process the item
                try:
                    serbian_word = queue_item["serbian_word"]
                    english_translation = queue_item.get("english_translation")
                    added_at = queue_item.get("added_at", time.time())

                    queue_age = (time.time() - added_at) / 60  # minutes
                    self.logger.info(
                        f"📤 Processing queued item: '{serbian_word}' (queued {queue_age:.1f}m ago)"
                    )

                    self.process_word(serbian_word, english_translation)

                    # Wait between requests to be conservative
                    self.logger.info("⏳ Waiting 30 seconds before next request...")
                    time.sleep(30)

                except Exception as e:
                    self.logger.error(f"Error processing queue item: {e}")

                # Release lock
                self.release_processing_lock()

            except KeyboardInterrupt:
                self.logger.info("🛑 Received shutdown signal")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(60)

        self.logger.info("👋 Image Sync Service stopped")
        self.log_stats()


def setup_logging():
    """Setup detailed logging"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Create logger
    logger = logging.getLogger("ImageSyncService")
    logger.setLevel(getattr(logging, log_level))

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    log_file = os.getenv("LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    return logger


def main():
    """Main entry point"""
    logger = setup_logging()

    try:
        # Connect to Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        logger.info(f"Connecting to Redis: {redis_url}")

        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Connected to Redis")

        # Initialize and run service
        service = ImageSyncService(redis_client, logger)
        service.run()

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
