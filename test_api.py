#!/usr/bin/env python3

import requests

BASE_URL = "http://localhost:3001"


def test_api():
    print("Testing Serbian Vocabulary API...")

    # Test 1: Health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Test 2: Categories without auth
    print("\n2. Testing categories without authentication...")
    response = requests.get(f"{BASE_URL}/api/categories")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        categories = response.json()
        print(f"Found {len(categories)} categories")
        # Show categories with top_100_count > 0
        top_100_categories = [
            cat for cat in categories if cat.get("top_100_count", 0) > 0
        ]
        print(f"Categories with Top 100 words: {len(top_100_categories)}")
        for cat in top_100_categories[:3]:
            print(f"  - {cat['name']}: {cat['top_100_count']} words")
    else:
        print(f"Error: {response.text}")

    # Test 3: Try to login (if you have test credentials)
    print("\n3. Testing login...")
    login_data = {"username": "test", "password": "test"}
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"},
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        auth_response = response.json()
        token = auth_response.get("access_token")
        print("Login successful, got token")

        # Test 4: Categories with auth
        print("\n4. Testing categories with authentication...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            categories = response.json()
            print(f"Found {len(categories)} categories (authenticated)")
    else:
        print(f"Login failed: {response.json() if response.text else 'No response'}")

        # Try to register a test user
        print("\n3a. Trying to register test user...")
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=login_data,
            headers={"Content-Type": "application/json"},
        )
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("Registration successful")
            auth_response = response.json()
            token = auth_response.get("access_token")

            # Test categories with new auth
            print("\n4. Testing categories with authentication...")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            response = requests.get(f"{BASE_URL}/api/categories", headers=headers)
            print(f"Status: {response.status_code}")
        else:
            print(
                f"Registration failed: {response.json() if response.text else 'No response'}"
            )


if __name__ == "__main__":
    test_api()
