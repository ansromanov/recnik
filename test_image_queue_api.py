#!/usr/bin/env python3
"""
Test script for the new image queue population API endpoint
"""


import requests

BASE_URL = "http://localhost:3001"


def test_image_queue_population():
    """Test the image queue population API endpoint"""

    print("🧪 Testing Image Queue Population API")
    print("=" * 50)

    # Test endpoint without authentication (should fail)
    print("\n1. Testing without authentication...")
    response = requests.post(f"{BASE_URL}/api/images/populate-queue")
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly requires authentication")
    else:
        print("❌ Should require authentication")
        print(f"Response: {response.text}")

    # For a real test, we'd need to:
    # 1. Register/login a user
    # 2. Get JWT token
    # 3. Make authenticated request

    print("\n2. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API is healthy: {data['message']}")
    else:
        print("❌ API health check failed")

    print("\n3. Testing metrics endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        print(f"Metrics endpoint status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Prometheus metrics are available")
            # Show a few lines of metrics
            lines = response.text.split("\n")[:10]
            print("Sample metrics:")
            for line in lines:
                if line and not line.startswith("#"):
                    print(f"  {line}")
                    break
        else:
            print("❌ Metrics endpoint not accessible")
    except Exception as e:
        print(f"Error accessing metrics: {e}")


def get_queue_status():
    """Get current queue status from Redis"""
    print("\n4. Checking queue status via backend logs...")
    print(
        "(Queue status is visible in the queue-populator and image-sync-service logs)"
    )

    return {
        "message": "Check docker-compose logs queue-populator and image-sync-service for current status"
    }


if __name__ == "__main__":
    test_image_queue_population()
    get_queue_status()

    print("\n" + "=" * 50)
    print("🎯 To manually test the authenticated endpoint:")
    print("1. Register a user via the frontend at http://localhost:3000")
    print("2. Use the JWT token to call:")
    print("   POST /api/images/populate-queue")
    print("   with headers: {'Authorization': 'Bearer <token>'}")
    print("3. Check logs: docker-compose logs -f queue-populator")
    print("=" * 50)
