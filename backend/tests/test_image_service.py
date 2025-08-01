"""
Unit tests for Image Service
"""

import pytest
import json
import time
import base64
from unittest.mock import Mock, patch, MagicMock
from image_service import RateLimitedImageService


@pytest.mark.unit
@pytest.mark.redis
class TestRateLimitedImageService:
    """Test cases for RateLimitedImageService"""

    def test_init(self, fake_redis):
        """Test service initialization"""
        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key"}):
            service = RateLimitedImageService(fake_redis)

            assert service.redis_client == fake_redis
            assert service.unsplash_access_key == "test-key"
            assert service.max_requests_per_hour == 25
            assert service.rate_limit_window == 3600

    def test_init_without_api_key(self, fake_redis):
        """Test initialization without Unsplash API key"""
        with patch.dict("os.environ", {}, clear=True):
            service = RateLimitedImageService(fake_redis)
            assert service.unsplash_access_key is None

    def test_generate_cache_key(self, fake_redis):
        """Test cache key generation"""
        service = RateLimitedImageService(fake_redis)

        key1 = service._generate_cache_key("kuća")
        key2 = service._generate_cache_key("KUĆA")  # Different case
        key3 = service._generate_cache_key("kuća")  # Same as first

        # Should normalize case
        assert key1 == key2 == key3
        assert key1.startswith("word_image:")

        # Different words should have different keys
        key4 = service._generate_cache_key("raditi")
        assert key1 != key4

    def test_get_rate_limit_info_no_requests(self, fake_redis):
        """Test getting rate limit info when no requests made"""
        service = RateLimitedImageService(fake_redis)

        count = service._get_rate_limit_info()
        assert count == 0

    def test_increment_rate_limit(self, fake_redis):
        """Test incrementing rate limit counter"""
        service = RateLimitedImageService(fake_redis)

        # First increment
        count1 = service._increment_rate_limit()
        assert count1 == 1

        # Second increment
        count2 = service._increment_rate_limit()
        assert count2 == 2

        # Verify it's tracked correctly
        info = service._get_rate_limit_info()
        assert info == 2

    def test_can_make_request(self, fake_redis):
        """Test rate limit checking"""
        service = RateLimitedImageService(fake_redis)

        # Should be able to make requests initially
        assert service._can_make_request() is True

        # Simulate reaching limit
        current_hour = int(time.time() // service.rate_limit_window)
        rate_key = f"{service.rate_limit_key}:{current_hour}"
        fake_redis.set(rate_key, service.max_requests_per_hour)

        assert service._can_make_request() is False

    def test_get_rate_limit_info_with_redis_error(self, fake_redis):
        """Test rate limit info when Redis raises error"""
        fake_redis.get = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)
        count = service._get_rate_limit_info()

        assert count == 0  # Should default to 0 on error

    def test_increment_rate_limit_with_redis_error(self, fake_redis):
        """Test rate limit increment when Redis raises error"""
        fake_redis.incr = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)
        count = service._increment_rate_limit()

        assert count == 999  # Should assume over limit on error

    @patch("requests.get")
    def test_search_unsplash_images_success(self, mock_get, fake_redis):
        """Test successful Unsplash image search"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "test-id-1",
                    "urls": {
                        "small": "https://images.unsplash.com/test1-small",
                        "regular": "https://images.unsplash.com/test1-regular",
                    },
                    "width": 400,
                    "height": 300,
                    "alt_description": "Test image 1",
                    "description": "A test image",
                    "user": {"name": "Test Photographer"},
                },
                {
                    "id": "test-id-2",
                    "urls": {"thumb": "https://images.unsplash.com/test2-thumb"},
                    "width": 300,
                    "height": 300,
                },
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key"}):
            service = RateLimitedImageService(fake_redis)

            images = service._search_unsplash_images("house", max_results=2)

            assert len(images) == 2
            assert images[0]["url"] == "https://images.unsplash.com/test1-small"
            assert images[0]["photographer"] == "Test Photographer"
            assert images[0]["unsplash_id"] == "test-id-1"
            assert images[1]["url"] == "https://images.unsplash.com/test2-thumb"

    @patch("requests.get")
    def test_search_unsplash_images_no_api_key(self, mock_get, fake_redis):
        """Test Unsplash search without API key"""
        service = RateLimitedImageService(fake_redis)
        service.unsplash_access_key = None

        images = service._search_unsplash_images("test")

        assert images == []
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_search_unsplash_images_rate_limited(self, mock_get, fake_redis):
        """Test Unsplash search when rate limited"""
        # Set up rate limit
        current_hour = int(time.time() // 3600)
        rate_key = f"unsplash_rate_limit:{current_hour}"
        fake_redis.set(rate_key, 25)  # At max limit

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key"}):
            service = RateLimitedImageService(fake_redis)

            images = service._search_unsplash_images("test")

            assert images == []
            mock_get.assert_not_called()

    @patch("requests.get")
    def test_search_unsplash_images_api_error(self, mock_get, fake_redis):
        """Test Unsplash search with API error"""
        mock_get.side_effect = Exception("API Error")

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key"}):
            service = RateLimitedImageService(fake_redis)

            images = service._search_unsplash_images("test")

            assert images == []

    @patch("requests.get")
    @patch("PIL.Image.open")
    def test_download_and_process_image_success(
        self, mock_image_open, mock_get, fake_redis
    ):
        """Test successful image download and processing"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = b"fake image data"
        mock_response.headers = {"content-type": "image/jpeg"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock PIL Image
        mock_img = Mock()
        mock_img.mode = "RGB"
        mock_img.width = 800
        mock_img.height = 600
        mock_img.thumbnail.return_value = None
        mock_img.save.return_value = None
        mock_image_open.return_value.__enter__.return_value = mock_img

        # Mock BytesIO for output
        with patch("io.BytesIO") as mock_bytesio:
            mock_output = Mock()
            mock_output.getvalue.return_value = b"processed image data"
            mock_bytesio.return_value = mock_output

            service = RateLimitedImageService(fake_redis)

            image_info = {
                "url": "https://test.com/image.jpg",
                "photographer": "Test Photographer",
                "unsplash_id": "test-id",
                "alt": "Test alt text",
            }

            result = service._download_and_process_image(image_info)

            assert result is not None
            assert result["content_type"] == "image/jpeg"
            assert result["photographer"] == "Test Photographer"
            assert result["unsplash_id"] == "test-id"
            assert result["alt_description"] == "Test alt text"
            assert "data" in result

    @patch("requests.get")
    def test_download_and_process_image_invalid_content_type(
        self, mock_get, fake_redis
    ):
        """Test image download with invalid content type"""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        service = RateLimitedImageService(fake_redis)

        image_info = {"url": "https://test.com/notimage.html"}
        result = service._download_and_process_image(image_info)

        assert result is None

    @patch("requests.get")
    def test_download_and_process_image_http_error(self, mock_get, fake_redis):
        """Test image download with HTTP error"""
        mock_get.side_effect = Exception("HTTP Error")

        service = RateLimitedImageService(fake_redis)

        image_info = {"url": "https://test.com/image.jpg"}
        result = service._download_and_process_image(image_info)

        assert result is None

    def test_add_to_background_queue(self, fake_redis):
        """Test adding word to background queue"""
        service = RateLimitedImageService(fake_redis)

        service._add_to_background_queue("kuća", "house")

        # Check if item was added to queue
        queue_length = fake_redis.llen(service.background_queue_key)
        assert queue_length == 1

        # Check queue item content
        queue_item_json = fake_redis.lrange(service.background_queue_key, 0, 0)[0]
        queue_item = json.loads(queue_item_json)

        assert queue_item["serbian_word"] == "kuća"
        assert queue_item["english_translation"] == "house"
        assert "added_at" in queue_item

    def test_add_to_background_queue_redis_error(self, fake_redis):
        """Test adding to queue when Redis raises error"""
        fake_redis.lpush = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)

        # Should not raise exception
        service._add_to_background_queue("test", "test")

    def test_get_word_image_cached(self, fake_redis):
        """Test getting word image when cached"""
        service = RateLimitedImageService(fake_redis)

        # Set up cached data
        cache_key = service._generate_cache_key("kuća")
        cached_data = {
            "image_data": "base64encodeddata",
            "content_type": "image/jpeg",
            "width": 400,
            "height": 300,
        }
        fake_redis.set(cache_key, json.dumps(cached_data))

        result = service.get_word_image("kuća", "house")

        assert result == cached_data

    def test_get_word_image_not_cached(self, fake_redis):
        """Test getting word image when not cached"""
        service = RateLimitedImageService(fake_redis)

        result = service.get_word_image("kuća", "house")

        # Should return None and add to queue
        assert result is None

        # Check if added to queue
        queue_length = fake_redis.llen(service.background_queue_key)
        assert queue_length == 1

    def test_get_word_image_cached_failure_recent(self, fake_redis):
        """Test getting word image with recent cached failure"""
        service = RateLimitedImageService(fake_redis)

        # Set up recent cached failure
        cache_key = service._generate_cache_key("kuća")
        cached_data = {
            "error": "No suitable image found",
            "cached_at": int(time.time()),  # Recent failure
        }
        fake_redis.set(cache_key, json.dumps(cached_data))

        result = service.get_word_image("kuća", "house")

        # Should return None and not add to queue again
        assert result is None
        queue_length = fake_redis.llen(service.background_queue_key)
        assert queue_length == 0

    def test_get_word_image_cached_failure_old(self, fake_redis):
        """Test getting word image with old cached failure"""
        service = RateLimitedImageService(fake_redis)

        # Set up old cached failure
        cache_key = service._generate_cache_key("kuća")
        cached_data = {
            "error": "No suitable image found",
            "cached_at": int(time.time()) - 25 * 60 * 60,  # 25 hours ago
        }
        fake_redis.set(cache_key, json.dumps(cached_data))

        result = service.get_word_image("kuća", "house")

        # Should return None and add to queue for retry
        assert result is None
        queue_length = fake_redis.llen(service.background_queue_key)
        assert queue_length == 1

    def test_populate_images_for_words(self, fake_redis):
        """Test populating images for word list"""
        service = RateLimitedImageService(fake_redis)

        words_list = [
            {"serbian_word": "kuća", "english_translation": "house"},
            {"serbian_word": "auto", "english_translation": "car"},
            "raditi",  # String format
        ]

        added_count = service.populate_images_for_words(words_list)

        assert added_count == 3
        queue_length = fake_redis.llen(service.background_queue_key)
        assert queue_length == 3

    def test_populate_images_for_words_skip_cached(self, fake_redis):
        """Test populate skips already cached words"""
        service = RateLimitedImageService(fake_redis)

        # Cache one word
        cache_key = service._generate_cache_key("kuća")
        fake_redis.set(cache_key, json.dumps({"image_data": "test"}))

        words_list = [
            {"serbian_word": "kuća", "english_translation": "house"},  # Cached
            {"serbian_word": "auto", "english_translation": "car"},  # Not cached
        ]

        added_count = service.populate_images_for_words(words_list)

        assert added_count == 1  # Only added uncached word

    def test_get_background_status(self, fake_redis):
        """Test getting background processing status"""
        service = RateLimitedImageService(fake_redis)

        # Add some items to queue
        for i in range(3):
            service._add_to_background_queue(f"word{i}", f"translation{i}")

        status = service.get_background_status()

        assert status["queue_length"] == 3
        assert "requests_this_hour" in status
        assert status["max_requests_per_hour"] == 25
        assert "is_processing" in status
        assert "processor_running" in status

    def test_get_background_status_redis_error(self, fake_redis):
        """Test background status when Redis raises error"""
        fake_redis.llen = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)
        status = service.get_background_status()

        assert "error" in status

    def test_clear_word_image_cache(self, fake_redis):
        """Test clearing cache for specific word"""
        service = RateLimitedImageService(fake_redis)

        # Set up cached data
        cache_key = service._generate_cache_key("kuća")
        fake_redis.set(cache_key, json.dumps({"test": "data"}))

        # Clear cache
        result = service.clear_word_image_cache("kuća")

        assert result is True
        assert fake_redis.get(cache_key) is None

    def test_clear_word_image_cache_redis_error(self, fake_redis):
        """Test clearing cache when Redis raises error"""
        fake_redis.delete = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)
        result = service.clear_word_image_cache("kuća")

        assert result is False

    def test_get_cache_stats(self, fake_redis):
        """Test getting cache statistics"""
        service = RateLimitedImageService(fake_redis)

        # Set up some cached data
        for i in range(5):
            cache_key = service._generate_cache_key(f"word{i}")
            if i < 3:
                # Successful cache
                data = {"image_data": "test", "content_type": "image/jpeg"}
            else:
                # Failed cache
                data = {"error": "No image found"}
            fake_redis.set(cache_key, json.dumps(data))

        stats = service.get_cache_stats()

        assert stats["total_cached_words"] == 5
        assert "cache_size_mb" in stats
        assert "successful_caches" in stats
        assert "failed_caches" in stats

    def test_get_cache_stats_redis_error(self, fake_redis):
        """Test cache stats when Redis raises error"""
        fake_redis.keys = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)
        stats = service.get_cache_stats()

        assert "error" in stats

    def test_clear_all_cache(self, fake_redis):
        """Test clearing all cached images"""
        service = RateLimitedImageService(fake_redis)

        # Set up some cached data
        for i in range(3):
            cache_key = service._generate_cache_key(f"word{i}")
            fake_redis.set(cache_key, json.dumps({"test": f"data{i}"}))

        cleared_count = service.clear_all_cache()

        assert cleared_count == 3

        # Verify all are cleared
        for i in range(3):
            cache_key = service._generate_cache_key(f"word{i}")
            assert fake_redis.get(cache_key) is None

    def test_clear_all_cache_empty(self, fake_redis):
        """Test clearing cache when no cached images"""
        service = RateLimitedImageService(fake_redis)

        cleared_count = service.clear_all_cache()
        assert cleared_count == 0

    def test_clear_all_cache_redis_error(self, fake_redis):
        """Test clearing all cache when Redis raises error"""
        fake_redis.keys = Mock(side_effect=Exception("Redis error"))

        service = RateLimitedImageService(fake_redis)
        cleared_count = service.clear_all_cache()

        assert cleared_count == 0

    def test_background_processor_lifecycle(self, fake_redis):
        """Test background processor start/stop"""
        service = RateLimitedImageService(fake_redis)

        # Should start automatically
        assert service.background_thread is not None

        # Stop processor
        service.stop_background_processor()
        assert service.should_stop_background is True


@pytest.mark.integration
class TestRateLimitedImageServiceIntegration:
    """Integration tests for RateLimitedImageService"""

    @pytest.mark.slow
    def test_real_unsplash_search(self, fake_redis):
        """Test with real Unsplash API (requires API key)"""
        import os

        api_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not api_key:
            pytest.skip("Unsplash API key not available")

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": api_key}):
            service = RateLimitedImageService(fake_redis)

            # Test rate limit check
            can_make_request = service._can_make_request()
            if not can_make_request:
                pytest.skip("Rate limit reached")

            # Search for a common word
            images = service._search_unsplash_images("house", max_results=1)

            # Basic assertions for real API response
            assert isinstance(images, list)
            if images:  # If API returned results
                assert "url" in images[0]
                assert "width" in images[0]
                assert "height" in images[0]
