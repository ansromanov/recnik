#!/usr/bin/env python3
"""
Test script for the enhanced word search functionality with LLM integration
"""

from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TEST_USER = {"username": "test_search_user", "password": "test123"}


def test_enhanced_search():
    """Test the enhanced search functionality"""

    # 1. Register/Login test user
    print("🔐 Setting up test user...")
    try:
        # Try to register
        response = requests.post(f"{API_BASE_URL}/auth/register", json=TEST_USER)
        if response.status_code == 201:
            print("✅ Test user registered successfully")
        elif response.status_code == 409:
            print("ℹ️ Test user already exists, logging in...")
    except Exception as e:
        print(f"⚠️ Registration failed: {e}")

    # Login
    response = requests.post(f"{API_BASE_URL}/auth/login", json=TEST_USER)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Successfully logged in")

    # 2. Test search with different scenarios
    test_cases = [
        {
            "query": "radim",
            "description": "Serbian verb form (should normalize to 'raditi')",
        },
        {
            "query": "working",
            "description": "English word (should translate to Serbian)",
        },
        {
            "query": "kuće",
            "description": "Serbian noun (plural, should normalize to 'kuća')",
        },
        {
            "query": "nonexistentword123",
            "description": "Non-existent word (should get suggestion)",
        },
        {
            "query": "čitam",
            "description": "Serbian verb with special characters",
        },
    ]

    print("\n🔍 Testing enhanced search functionality...")

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['description']} ---")
        print(f"Query: '{test_case['query']}'")

        try:
            response = requests.get(
                f"{API_BASE_URL}/words/search",
                params={"q": test_case["query"]},
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                print("✅ Search successful")
                print(f"   - Vocabulary results: {len(data.get('vocabulary_results', []))}")
                print(f"   - All results: {len(data.get('all_results', []))}")
                print(f"   - Has results: {data.get('has_results', False)}")

                # Check suggestion
                suggestion = data.get("suggestion")
                if suggestion:
                    print("   - Suggestion available: Yes")
                    print(f"   - LLM processed: {suggestion.get('llm_processed', False)}")
                    print(f"   - Suggested Serbian: {suggestion.get('suggested_serbian', 'N/A')}")
                    print(f"   - Suggested English: {suggestion.get('suggested_english', 'N/A')}")
                    print(f"   - Confidence: {suggestion.get('confidence', 'N/A')}")
                    print(f"   - Word type: {suggestion.get('word_type', 'N/A')}")
                    print(f"   - Message: {suggestion.get('message', 'N/A')}")
                    if suggestion.get("error"):
                        print(f"   - Error: {suggestion['error']}")
                else:
                    print("   - Suggestion available: No")

            else:
                print(f"❌ Search failed: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Error during search: {e}")

    # 3. Test adding a suggested word
    print("\n➕ Testing word addition...")

    test_word_data = {
        "serbian_word": "testirati",
        "english_translation": "to test",
        "category_id": 1,
        "context": "Testing the enhanced search functionality",
        "notes": "Added via test script",
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/words/add-suggested", json=test_word_data, headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Word added successfully: {data.get('message')}")
                print(f"   - Queued for image: {data.get('queued_for_image', False)}")
            else:
                print(f"⚠️ Word addition failed: {data}")
        else:
            print(f"❌ Word addition failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error adding word: {e}")

    print("\n🎉 Enhanced search testing completed!")
    print("\nTo fully test LLM functionality:")
    print("1. Configure OpenAI API key in user settings")
    print("2. Test with various Serbian word forms")
    print("3. Check that suggestions show proper normalization")


if __name__ == "__main__":
    test_enhanced_search()
