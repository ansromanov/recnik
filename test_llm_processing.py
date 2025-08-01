#!/usr/bin/env python3
"""
Test script for the new LLM prompt-based text processing
"""

import requests
import json

# Test data
test_text = """
Danas sam bio u gradu i kupio sam hleb, mleko i jabuke. Prodavac je bio vrlo ljubazan. 
Pošao sam kući autobusom koji vozi svakih 15 minuta. U parku sam video decu kako se igraju.
Takođe sam prošao pored biblioteke i video sam da imaju nove knjige.
"""


def test_process_text():
    """Test the new text processing endpoint"""

    # First, let's register a test user
    register_data = {"username": "test_llm_user", "password": "testpass123"}

    print("🔐 Registering test user...")
    try:
        response = requests.post(
            "http://localhost:3001/api/auth/register", json=register_data, timeout=10
        )

        if response.status_code == 201:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ User registered successfully. Token: {token[:20]}...")
        elif response.status_code == 409:
            # User already exists, try to login
            print("👤 User already exists, trying to login...")
            login_response = requests.post(
                "http://localhost:3001/api/auth/login", json=register_data, timeout=10
            )
            if login_response.status_code == 200:
                data = login_response.json()
                token = data.get("access_token")
                print(f"✅ Login successful. Token: {token[:20]}...")
            else:
                print(f"❌ Login failed: {login_response.text}")
                return
        else:
            print(f"❌ Registration failed: {response.text}")
            return

    except Exception as e:
        print(f"❌ Auth error: {e}")
        return

    # Set up OpenAI API key (you'll need to provide a valid key)
    print("\n⚙️  Setting up OpenAI API key...")
    settings_data = {
        "openai_api_key": "your-openai-api-key-here"  # Replace with actual key
    }

    try:
        settings_response = requests.put(
            "http://localhost:3001/api/settings",
            json=settings_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        if settings_response.status_code == 200:
            print("✅ OpenAI API key configured")
        else:
            print(f"⚠️  Could not set API key: {settings_response.text}")
            print(
                "📝 Note: You'll need to set a valid OpenAI API key to test the LLM processing"
            )

    except Exception as e:
        print(f"⚠️  Settings error: {e}")

    # Test the new text processing
    print(f"\n🧠 Testing LLM-based text processing...")
    print(f"📄 Input text: {test_text[:100]}...")

    try:
        process_response = requests.post(
            "http://localhost:3001/api/process-text",
            json={"text": test_text},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60,  # Longer timeout for LLM processing
        )

        if process_response.status_code == 200:
            result = process_response.json()
            print("✅ Text processing successful!")
            print(f"📊 Results:")
            print(f"   • Total words: {result.get('total_words', 0)}")
            print(f"   • New words: {result.get('new_words', 0)}")
            print(f"   • Filtering summary: {result.get('filtering_summary', {})}")

            translations = result.get("translations", [])
            if translations:
                print(f"\n🎯 Sample processed words:")
                for i, word in enumerate(translations[:5]):  # Show first 5
                    print(
                        f"   {i + 1}. {word['serbian_word']} → {word['english_translation']} ({word['category_name']})"
                    )
                    if word.get("original_form"):
                        print(f"      Original form: {word['original_form']}")

        elif process_response.status_code == 400:
            error_data = process_response.json()
            if "OpenAI API key" in error_data.get("error", ""):
                print(
                    "⚠️  OpenAI API key required - please set a valid key in the script"
                )
                print(
                    "📝 The LLM prompt-based processing is working, but needs API key"
                )
            else:
                print(f"❌ Processing failed: {error_data}")
        else:
            print(f"❌ Processing failed: {process_response.text}")

    except Exception as e:
        print(f"❌ Processing error: {e}")


if __name__ == "__main__":
    test_process_text()
