#!/usr/bin/env python3
"""
Test script for the separated Image Sync Service
Tests the communication between backend and image sync service through Redis.
"""

import json
import time

import redis
import requests


class ImageSyncServiceTester:
    def __init__(self, redis_url="redis://localhost:6379", backend_url="http://localhost:3001"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.backend_url = backend_url
        self.queue_key = "image_queue"

    def test_redis_connection(self):
        """Test Redis connectivity"""
        try:
            self.redis_client.ping()
            print("✅ Redis connection successful")
            return True
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            return False

    def test_backend_connection(self):
        """Test backend API connectivity"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend API connection successful")
                return True
            else:
                print(f"❌ Backend API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend API connection failed: {e}")
            return False

    def add_test_words_to_queue(self):
        """Add test words to the image processing queue"""
        test_words = [
            {"serbian_word": "мачка", "english_translation": "cat"},
            {"serbian_word": "пас", "english_translation": "dog"},
            {"serbian_word": "кућа", "english_translation": "house"},
            {"serbian_word": "вода", "english_translation": "water"},
            {"serbian_word": "сунце", "english_translation": "sun"},
        ]

        added_count = 0
        for word_data in test_words:
            queue_item = {**word_data, "added_at": int(time.time()), "test_mode": True}
            try:
                self.redis_client.lpush(self.queue_key, json.dumps(queue_item))
                added_count += 1
                print(f"➕ Added '{word_data['serbian_word']}' to queue")
            except Exception as e:
                print(f"❌ Failed to add '{word_data['serbian_word']}': {e}")

        print(f"✅ Added {added_count} test words to queue")
        return added_count

    def check_queue_status(self):
        """Check current queue status"""
        try:
            queue_length = self.redis_client.llen(self.queue_key)
            print(f"📊 Current queue length: {queue_length}")

            # Check processing lock
            processing_lock = self.redis_client.get("image_processing_lock")
            if processing_lock:
                print("🔒 Image sync service is currently processing")
            else:
                print("🔓 Image sync service is idle")

            # Check rate limit
            current_hour = int(time.time() // 3600)
            rate_key = f"unsplash_rate_limit:{current_hour}"
            current_requests = self.redis_client.get(rate_key)
            current_requests = int(current_requests) if current_requests else 0
            print(f"🌐 API requests this hour: {current_requests}/25")

            return queue_length

        except Exception as e:
            print(f"❌ Error checking queue status: {e}")
            return -1

    def check_cached_images(self):
        """Check for cached images"""
        try:
            cache_keys = self.redis_client.keys("word_image:*")
            cache_count = len(cache_keys)
            print(f"🖼️  Cached images: {cache_count}")

            if cache_count > 0:
                # Sample a few cached images
                sample_keys = cache_keys[:3]
                for key in sample_keys:
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            cached_result = json.loads(data)
                            if "error" in cached_result:
                                print(f"   ❌ {key}: {cached_result['error']}")
                            else:
                                size_kb = cached_result.get("size", 0) // 1024
                                width = cached_result.get("width", "unknown")
                                height = cached_result.get("height", "unknown")
                                print(f"   ✅ {key}: {width}x{height}, {size_kb}KB")
                    except Exception as e:
                        print(f"   ⚠️  {key}: Error reading cache - {e}")

            return cache_count

        except Exception as e:
            print(f"❌ Error checking cached images: {e}")
            return -1

    def test_backend_api_endpoints(self):
        """Test backend image API endpoints (requires authentication)"""
        print("\n📡 Testing Backend API Endpoints:")
        print("   (Note: Some endpoints require authentication)")

        # Test status endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/images/background/status", timeout=5)
            print(f"   Status endpoint: {response.status_code}")
            if response.status_code == 401:
                print("     (Authentication required - this is expected)")
        except Exception as e:
            print(f"   Status endpoint error: {e}")

        # Test cache stats endpoint
        try:
            response = requests.get(f"{self.backend_url}/api/images/cache/stats", timeout=5)
            print(f"   Cache stats endpoint: {response.status_code}")
            if response.status_code == 401:
                print("     (Authentication required - this is expected)")
        except Exception as e:
            print(f"   Cache stats endpoint error: {e}")

    def monitor_processing(self, duration_seconds=60):
        """Monitor queue processing for a specified duration"""
        print(f"\n🔍 Monitoring queue processing for {duration_seconds} seconds...")

        start_time = time.time()
        initial_queue_length = self.check_queue_status()

        while time.time() - start_time < duration_seconds:
            current_queue_length = self.redis_client.llen(self.queue_key)

            if current_queue_length != initial_queue_length:
                processed = initial_queue_length - current_queue_length
                print(f"📈 Progress: {processed} items processed")
                initial_queue_length = current_queue_length

            # Check for new cached images
            cache_count = len(self.redis_client.keys("word_image:*"))

            print(f"   Queue: {current_queue_length}, Cache: {cache_count}", end="\r")
            time.sleep(5)

        print("\n✅ Monitoring complete")

    def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting Image Sync Service Test Suite")
        print("=" * 50)

        # Test connections
        print("\n1️⃣ Testing Connections:")
        redis_ok = self.test_redis_connection()
        backend_ok = self.test_backend_connection()

        if not redis_ok:
            print("❌ Cannot proceed without Redis connection")
            return

        # Check initial status
        print("\n2️⃣ Initial Status:")
        initial_queue = self.check_queue_status()
        initial_cache = self.check_cached_images()

        # Add test words
        print("\n3️⃣ Adding Test Words:")
        added_count = self.add_test_words_to_queue()

        # Check updated status
        print("\n4️⃣ Updated Status:")
        updated_queue = self.check_queue_status()

        # Test API endpoints
        if backend_ok:
            self.test_backend_api_endpoints()

        # Instructions for next steps
        print("\n5️⃣ Next Steps:")
        print("   To see the image sync service in action:")
        print("   1. Start the image sync service: docker-compose up -d image-sync-service")
        print("   2. Monitor logs: docker-compose logs -f image-sync-service")
        print("   3. Re-run this test to see processing")

        if updated_queue > 0:
            print(f"\n   Queue has {updated_queue} items ready for processing")

            response = input("\n🔍 Monitor processing for 60 seconds? (y/N): ")
            if response.lower() == "y":
                self.monitor_processing(60)

        print("\n✅ Test suite complete!")
        print("\nFor detailed logs and monitoring, use:")
        print("   docker-compose logs -f image-sync-service")
        print("   docker-compose ps image-sync-service")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Image Sync Service")
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis URL (default: redis://localhost:6379)",
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:3001",
        help="Backend URL (default: http://localhost:3001)",
    )
    parser.add_argument("--quick", action="store_true", help="Run quick test (skip monitoring)")

    args = parser.parse_args()

    tester = ImageSyncServiceTester(args.redis_url, args.backend_url)

    if args.quick:
        print("🚀 Running Quick Test")
        tester.test_redis_connection()
        tester.test_backend_connection()
        tester.check_queue_status()
        tester.check_cached_images()
    else:
        tester.run_full_test()


if __name__ == "__main__":
    main()
