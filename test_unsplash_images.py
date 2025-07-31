#!/usr/bin/env python3
"""
Test script for the new Unsplash image service.
This script tests the image service functionality without needing the full Flask app.
"""

import os
import sys
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from image_service import ImageService


def test_image_service():
    """Test the image service with Unsplash integration"""

    # Check if Unsplash access key is available
    unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not unsplash_key:
        print("❌ UNSPLASH_ACCESS_KEY not found in environment variables")
        print("Please add your Unsplash access key to the .env file")
        print("You can get one for free at: https://unsplash.com/developers")
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
        print("Make sure Redis is running")
        return False

    # Initialize image service
    image_service = ImageService(redis_client)

    # Test words
    test_words = [
        ("pas", "dog"),
        ("mačka", "cat"),
        ("kuća", "house"),
        ("auto", "car"),
        ("drvo", "tree"),
    ]

    print("\n🔍 Testing image search for words:")
    print("=" * 50)

    for serbian_word, english_translation in test_words:
        print(f"\nSearching for: {serbian_word} ({english_translation})")

        try:
            result = image_service.get_word_image(serbian_word, english_translation)

            if result and "error" not in result:
                print(f"✅ Found image!")
                print(
                    f"   - Size: {result.get('width', 'unknown')}x{result.get('height', 'unknown')}"
                )
                print(f"   - File size: {result.get('size', 0)} bytes")
                print(f"   - Search query: {result.get('search_query', 'unknown')}")
                print(f"   - Photographer: {result.get('photographer', 'unknown')}")
                print(f"   - Source: {result.get('source', 'unknown')}")
                print(f"   - Cached at: {result.get('cached_at', 'unknown')}")
            else:
                error_msg = (
                    result.get("error", "Unknown error") if result else "No result"
                )
                print(f"❌ Failed to get image: {error_msg}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")

    # Test cache stats
    print(f"\n📊 Cache Statistics:")
    print("=" * 30)
    try:
        stats = image_service.get_cache_stats()
        print(f"Total cached words: {stats.get('total_cached_words', 0)}")
        print(f"Estimated cache size: {stats.get('cache_size_mb', 0)} MB")
    except Exception as e:
        print(f"❌ Failed to get cache stats: {e}")

    return True


if __name__ == "__main__":
    print("🖼️  Testing Unsplash Image Service")
    print("=" * 40)

    success = test_image_service()

    if success:
        print("\n✅ Test completed!")
        print("\nNext steps:")
        print("1. Make sure to add your UNSPLASH_ACCESS_KEY to the .env file")
        print("2. Restart your Flask application")
        print("3. The image service will now use Unsplash instead of Google Images")
    else:
        print("\n❌ Test failed. Check the errors above.")
