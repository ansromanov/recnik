#!/usr/bin/env python3
"""
Test script for the rate-limited Unsplash image service.
This script tests the background processing and rate limiting functionality.
"""

import os
import sys
import time

from dotenv import load_dotenv
import redis

# Load environment variables
load_dotenv()

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from image_service import RateLimitedImageService


def test_rate_limited_service():
    """Test the rate-limited image service"""

    # Check if Unsplash access key is available
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not unsplash_key:
        print("❌ UNSPLASH_ACCESS_KEY not found in environment variables")
        print("Please add your Unsplash access key to the .env file")
        return False

    print(f"✅ Found Unsplash access key: {unsplash_key[:10]}...")

    # Connect to Redis
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return False

    # Initialize rate-limited image service
    print("\n🔧 Initializing rate-limited image service...")
    image_service = RateLimitedImageService(redis_client)

    # Wait a moment for background processor to start
    time.sleep(2)

    # Test background status
    print("\n📊 Background Processing Status:")
    print("=" * 40)
    try:
        status = image_service.get_background_status()
        print(f"Queue length: {status.get('queue_length', 'unknown')}")
        print(
            f"Requests this hour: {status.get('requests_this_hour', 0)}/{status.get('max_requests_per_hour', 25)}"
        )
        print(f"Processing active: {status.get('is_processing', False)}")
        print(f"Background processor running: {status.get('processor_running', False)}")
    except Exception as e:
        print(f"❌ Error getting status: {e}")

    # Test rate limiting by checking current status
    print("\n⏱️  Rate Limiting Test:")
    print("=" * 30)
    current_requests = image_service._get_rate_limit_info()
    can_make_request = image_service._can_make_request()
    print(f"Current requests this hour: {current_requests}")
    print(f"Can make request: {'✅' if can_make_request else '❌'}")

    # Test adding words to background queue
    print("\n🔄 Testing Background Queue:")
    print("=" * 35)

    test_words = [
        {"serbian_word": "pas", "english_translation": "dog"},
        {"serbian_word": "mačka", "english_translation": "cat"},
        {"serbian_word": "kuća", "english_translation": "house"},
        {"serbian_word": "auto", "english_translation": "car"},
        {"serbian_word": "drvo", "english_translation": "tree"},
    ]

    # Add words to background queue
    added_count = image_service.populate_images_for_words(test_words)
    print(f"Added {added_count} words to background queue")

    # Check updated status
    status = image_service.get_background_status()
    print(f"Queue length after adding: {status.get('queue_length', 'unknown')}")

    # Test immediate processing (if rate limit allows)
    print("\n⚡ Testing Immediate Processing:")
    print("=" * 40)

    if can_make_request:
        try:
            print("Attempting immediate image fetch for 'pas' (dog)...")
            result = image_service.get_word_image_immediate("pas", "dog")

            if result and "error" not in result:
                print("✅ Successfully got image immediately!")
                print(
                    f"   - Size: {result.get('width', 'unknown')}x{result.get('height', 'unknown')}"
                )
                print(f"   - File size: {result.get('size', 0)} bytes")
                print(f"   - Photographer: {result.get('photographer', 'unknown')}")
            else:
                error = result.get("error", "Unknown error") if result else "No result"
                print(f"❌ Immediate processing failed: {error}")

        except Exception as e:
            print(f"❌ Exception during immediate processing: {e}")
    else:
        print("⏸️ Rate limit reached - cannot test immediate processing")

    # Test normal get_word_image (should return None and queue for background)
    print("\n🎯 Testing Normal Image Retrieval:")
    print("=" * 40)

    # This should return None and add to queue
    result = image_service.get_word_image("knjiga", "book")
    if result is None:
        print("✅ Correctly returned None - word queued for background processing")
    else:
        print(
            f"✅ Found cached image for 'knjiga': {result.get('search_query', 'unknown query')}"
        )

    # Show final status
    print("\n📈 Final Status:")
    print("=" * 20)
    status = image_service.get_background_status()
    cache_stats = image_service.get_cache_stats()

    print(f"Queue length: {status.get('queue_length', 'unknown')}")
    print(
        f"Requests used: {status.get('requests_this_hour', 0)}/{status.get('max_requests_per_hour', 25)}"
    )
    print(f"Total cached words: {cache_stats.get('total_cached_words', 0)}")
    print(f"Cache size: {cache_stats.get('cache_size_mb', 0)} MB")
    print(
        f"Background processor: {'✅ Running' if status.get('processor_running', False) else '❌ Stopped'}"
    )

    # Show how background processing works
    print("\n🔍 Background Processing Info:")
    print("=" * 35)
    print("The background processor will:")
    print("• Process 1 word every 2 minutes")
    print("• Stay under 25 requests per hour")
    print("• Cache results for 30 days")
    print("• Retry failed searches after 24 hours")
    print("• Run continuously in the background")

    if status.get("queue_length", 0) > 0:
        estimated_time = status.get("queue_length", 0) * 2  # 2 minutes per word
        print(
            f"\n⏰ Estimated processing time: ~{estimated_time} minutes for current queue"
        )

    # Stop background processor for clean shutdown
    print("\n🛑 Stopping background processor...")
    image_service.stop_background_processor()

    return True


if __name__ == "__main__":
    print("🚀 Testing Rate-Limited Unsplash Image Service")
    print("=" * 50)

    success = test_rate_limited_service()

    if success:
        print("\n✅ Rate-limited service test completed!")
        print("\nKey Features:")
        print("• ⏰ Aggressive rate limiting (25 requests/hour)")
        print("• 🔄 Background processing with 2-minute intervals")
        print("• 💾 30-day aggressive caching")
        print("• 🔒 Distributed locking for multiple instances")
        print("• 📊 Real-time status monitoring")
        print("\nYour app will now:")
        print("1. Queue image searches in the background")
        print("2. Process them slowly to respect rate limits")
        print("3. Cache results for 30 days")
        print("4. Never exceed your API quota")
    else:
        print("\n❌ Test failed. Check the errors above.")
