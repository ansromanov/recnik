import base64
import hashlib
import io
import json
import os
import random
import threading
import time

from PIL import Image
import requests


class RateLimitedImageService:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")

        if not self.unsplash_access_key:
            print("Warning: UNSPLASH_ACCESS_KEY not found in environment variables")

        self.headers = {
            "User-Agent": "Serbian Vocabulary App/1.0",
            "Accept": "application/json",
        }

        # Unsplash API endpoints
        self.unsplash_search_url = "https://api.unsplash.com/search/photos"

        # Rate limiting - very conservative to stay under 30/hour
        self.rate_limit_key = "unsplash_rate_limit"
        self.max_requests_per_hour = 25  # Stay well under 30/hour limit
        self.rate_limit_window = 3600  # 1 hour in seconds

        # Background processing
        self.background_queue_key = "image_queue"
        self.processing_lock_key = "image_processing_lock"
        self.background_thread = None
        self.should_stop_background = False

        # Start background processor
        self.start_background_processor()

    def _generate_cache_key(self, word):
        """Generate a cache key for the word"""
        return f"word_image:{hashlib.md5(word.lower().encode()).hexdigest()}"

    def _get_rate_limit_info(self):
        """Get current rate limit status"""
        try:
            current_hour = int(time.time() // self.rate_limit_window)
            rate_key = f"{self.rate_limit_key}:{current_hour}"
            current_count = self.redis_client.get(rate_key)
            return int(current_count) if current_count else 0
        except Exception as e:
            print(f"Error getting rate limit info: {e}")
            return 0

    def _increment_rate_limit(self):
        """Increment rate limit counter"""
        try:
            current_hour = int(time.time() // self.rate_limit_window)
            rate_key = f"{self.rate_limit_key}:{current_hour}"
            current_count = self.redis_client.incr(rate_key)

            # Set expiration for the key (2 hours to be safe)
            if current_count == 1:
                self.redis_client.expire(rate_key, self.rate_limit_window * 2)

            return current_count
        except Exception as e:
            print(f"Error incrementing rate limit: {e}")
            return 999  # Assume we're over limit if we can't track

    def _can_make_request(self):
        """Check if we can make another API request"""
        current_count = self._get_rate_limit_info()
        return current_count < self.max_requests_per_hour

    def _search_unsplash_images(self, query, max_results=3):
        """Search Unsplash for images matching the query with rate limiting"""
        if not self.unsplash_access_key:
            print("No Unsplash access key available")
            return []

        # Check rate limit before making request
        if not self._can_make_request():
            print(f"Rate limit reached. Current requests this hour: {self._get_rate_limit_info()}")
            return []

        try:
            # Increment rate limit counter
            request_count = self._increment_rate_limit()
            print(f"Making Unsplash API request #{request_count} this hour for query: {query}")

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
                self.unsplash_search_url, params=params, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            images = []

            for photo in data.get("results", []):
                try:
                    urls = photo.get("urls", {})
                    image_url = urls.get("small") or urls.get("regular") or urls.get("thumb")

                    if not image_url:
                        continue

                    images.append(
                        {
                            "url": image_url,
                            "width": photo.get("width", 400),
                            "height": photo.get("height", 400),
                            "alt": photo.get("alt_description", ""),
                            "description": photo.get("description", ""),
                            "photographer": photo.get("user", {}).get("name", ""),
                            "unsplash_id": photo.get("id", ""),
                        }
                    )

                except Exception as e:
                    print(f"Error processing Unsplash photo data: {e}")
                    continue

            return images

        except Exception as e:
            print(f"Error searching Unsplash for '{query}': {e}")
            return []

    def _download_and_process_image(self, image_info):
        """Download and process an image from Unsplash"""
        try:
            image_url = image_info["url"]

            response = requests.get(image_url, headers=self.headers, timeout=15, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                return None

            image_data = response.content

            with Image.open(io.BytesIO(image_data)) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                max_size = 400
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

                output = io.BytesIO()
                img.save(output, format="JPEG", quality=85, optimize=True)
                processed_data = output.getvalue()

                return {
                    "data": base64.b64encode(processed_data).decode("utf-8"),
                    "content_type": "image/jpeg",
                    "width": img.width,
                    "height": img.height,
                    "size": len(processed_data),
                    "photographer": image_info.get("photographer", ""),
                    "unsplash_id": image_info.get("unsplash_id", ""),
                    "alt_description": image_info.get("alt", ""),
                }

        except Exception as e:
            print(f"Error downloading/processing image from {image_url}: {e}")
            return None

    def _process_word_for_image(self, serbian_word, english_translation=None):
        """Process a single word for image search - used by background processor"""
        cache_key = self._generate_cache_key(serbian_word)

        # Check if already cached
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return  # Already have image
        except Exception as e:
            print(f"Error checking cache for {serbian_word}: {e}")

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

        best_image = None

        # Try each search query
        for query in search_queries:
            if not self._can_make_request():
                print(f"Rate limit reached, queuing {serbian_word} for later")
                self._add_to_background_queue(serbian_word, english_translation)
                return

            print(f"Background processing: Searching for {serbian_word} with query: {query}")
            images = self._search_unsplash_images(query, max_results=2)

            if not images:
                continue

            # Try to download first image only
            img_info = images[0]
            processed_image = self._download_and_process_image(img_info)
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
                break

        # Cache result
        cache_data = best_image or {
            "error": "No suitable image found",
            "cached_at": int(time.time()),
        }

        try:
            # Cache for 30 days (aggressive caching)
            self.redis_client.setex(cache_key, 30 * 24 * 60 * 60, json.dumps(cache_data))
            if best_image:
                print(f"✅ Cached image for {serbian_word}")
            else:
                print(f"❌ No image found for {serbian_word}, cached failure")
        except Exception as e:
            print(f"Error caching result for {serbian_word}: {e}")

    def _add_to_background_queue(self, serbian_word, english_translation=None):
        """Add word to background processing queue"""
        try:
            queue_item = {
                "serbian_word": serbian_word,
                "english_translation": english_translation,
                "added_at": int(time.time()),
            }
            self.redis_client.lpush(self.background_queue_key, json.dumps(queue_item))
            print(f"Added {serbian_word} to background queue")
        except Exception as e:
            print(f"Error adding {serbian_word} to queue: {e}")

    def _background_processor(self):
        """Background thread that processes image requests slowly"""
        print("🔄 Starting background image processor")

        while not self.should_stop_background:
            try:
                # Check if we can make requests
                if not self._can_make_request():
                    current_count = self._get_rate_limit_info()
                    print(
                        f"⏸️ Rate limit reached ({current_count}/{self.max_requests_per_hour}), waiting..."
                    )
                    time.sleep(300)  # Wait 5 minutes
                    continue

                # Try to get processing lock
                lock_acquired = self.redis_client.set(
                    self.processing_lock_key, "locked", ex=300, nx=True
                )

                if not lock_acquired:
                    print("Another instance is processing, waiting...")
                    time.sleep(60)
                    continue

                # Get item from queue
                queue_item_json = self.redis_client.rpop(self.background_queue_key)

                if not queue_item_json:
                    # No items in queue, wait and check again
                    self.redis_client.delete(self.processing_lock_key)
                    time.sleep(30)
                    continue

                # Process the item
                try:
                    queue_item = json.loads(queue_item_json)
                    serbian_word = queue_item["serbian_word"]
                    english_translation = queue_item.get("english_translation")

                    print(f"🔍 Background processing: {serbian_word}")
                    self._process_word_for_image(serbian_word, english_translation)

                    # Wait between requests to be extra conservative
                    time.sleep(120)  # 2 minutes between requests = max 30/hour

                except json.JSONDecodeError:
                    print(f"Invalid queue item: {queue_item_json}")
                except Exception as e:
                    print(f"Error processing queue item: {e}")

                # Release lock
                self.redis_client.delete(self.processing_lock_key)

            except Exception as e:
                print(f"Background processor error: {e}")
                time.sleep(60)

        print("🛑 Background processor stopped")

    def start_background_processor(self):
        """Start the background processor thread"""
        if self.background_thread and self.background_thread.is_alive():
            return

        self.should_stop_background = False
        self.background_thread = threading.Thread(target=self._background_processor, daemon=True)
        self.background_thread.start()

    def stop_background_processor(self):
        """Stop the background processor"""
        self.should_stop_background = True
        if self.background_thread:
            self.background_thread.join(timeout=5)

    def get_word_image(self, serbian_word, english_translation=None):
        """Get an image for a word - returns cached if available, queues for background if not"""
        cache_key = self._generate_cache_key(serbian_word)

        # Try to get from cache first
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                cached_result = json.loads(cached_data)
                if "error" not in cached_result:
                    return cached_result
                else:
                    # If it was a cached failure, check if enough time has passed to retry
                    cached_at = cached_result.get("cached_at", 0)
                    if time.time() - cached_at < 24 * 60 * 60:  # 24 hours
                        return None  # Don't retry failed searches too soon
        except Exception as e:
            print(f"Error reading from Redis cache: {e}")

        # Not in cache or cache expired, add to background queue
        self._add_to_background_queue(serbian_word, english_translation)

        # Return immediately - image will be available later
        return None

    def get_word_image_immediate(self, serbian_word, english_translation=None):
        """Get image immediately if rate limit allows - for testing/admin use"""
        if not self._can_make_request():
            return {
                "error": f"Rate limit reached ({self._get_rate_limit_info()}/{self.max_requests_per_hour} requests this hour)"
            }

        # Process immediately
        self._process_word_for_image(serbian_word, english_translation)

        # Return cached result
        cache_key = self._generate_cache_key(serbian_word)
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Error reading immediate result: {e}")

        return {"error": "Failed to process image"}

    def populate_images_for_words(self, words_list):
        """Add a list of words to the background processing queue"""
        added_count = 0

        for word_data in words_list:
            if isinstance(word_data, dict):
                serbian_word = word_data.get("serbian_word")
                english_translation = word_data.get("english_translation")
            else:
                serbian_word = word_data
                english_translation = None

            if serbian_word:
                # Check if already cached
                cache_key = self._generate_cache_key(serbian_word)
                try:
                    cached_data = self.redis_client.get(cache_key)
                    if cached_data:
                        continue  # Already have this word
                except:
                    pass

                self._add_to_background_queue(serbian_word, english_translation)
                added_count += 1

        print(f"Added {added_count} words to background processing queue")
        return added_count

    def get_background_status(self):
        """Get status of background processing"""
        try:
            queue_length = self.redis_client.llen(self.background_queue_key)
            current_requests = self._get_rate_limit_info()

            # Check if processing is active
            is_processing = bool(self.redis_client.get(self.processing_lock_key))

            return {
                "queue_length": queue_length,
                "requests_this_hour": current_requests,
                "max_requests_per_hour": self.max_requests_per_hour,
                "is_processing": is_processing,
                "processor_running": self.background_thread and self.background_thread.is_alive(),
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_word_image_cache(self, serbian_word):
        """Clear cached image for a specific word"""
        cache_key = self._generate_cache_key(serbian_word)
        try:
            self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            print(f"Error clearing cache for word '{serbian_word}': {e}")
            return False

    def get_cache_stats(self):
        """Get statistics about the image cache"""
        try:
            keys = self.redis_client.keys("word_image:*")
            total_keys = len(keys)

            # Count successful vs failed caches
            successful_caches = 0
            failed_caches = 0

            cache_info = {
                "total_cached_words": total_keys,
                "cache_size_mb": 0,
                "successful_caches": 0,
                "failed_caches": 0,
            }

            if keys:
                sample_size = min(20, len(keys))
                sample_keys = random.sample(keys, sample_size)
                total_sample_size = 0

                for key in sample_keys:
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            total_sample_size += len(data)
                            try:
                                parsed_data = json.loads(data)
                                if "error" in parsed_data:
                                    failed_caches += 1
                                else:
                                    successful_caches += 1
                            except:
                                pass
                    except:
                        continue

                if total_sample_size > 0:
                    avg_size = total_sample_size / sample_size
                    estimated_total_size = avg_size * total_keys
                    cache_info["cache_size_mb"] = round(estimated_total_size / (1024 * 1024), 2)

                # Extrapolate success/failure rates
                if sample_size > 0:
                    success_rate = successful_caches / sample_size
                    cache_info["successful_caches"] = int(total_keys * success_rate)
                    cache_info["failed_caches"] = total_keys - cache_info["successful_caches"]

            return cache_info
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def clear_all_cache(self):
        """Clear all cached images"""
        try:
            keys = self.redis_client.keys("word_image:*")
            if keys:
                self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            print(f"Error clearing all cache: {e}")
            return 0


# Maintain backward compatibility
ImageService = RateLimitedImageService
