#!/usr/bin/env python3
"""
Test script for the improved LLM prompt-based text processing with infinitive conversion
"""

import requests

# Enhanced test data with various verb forms to test infinitive conversion
test_texts = {
    "basic_verbs": """
    Danas radim u gradu. Jučer sam radio ceo dan. Sutra ću raditi još više.
    Kupujem hranu na pijaci. Kupio sam hleb i mleko. Kupovala je voće.
    Čitam zanimljivu knjigu. Pročitao sam tri poglavlja. Čitaće celu noć.
    """,
    "mixed_content": """
    Jutros sam ustao rano i pošao u grad. Video sam prijatelje na kafi.
    Razgovarali smo o filmu koji smo gledali sinoć. Prodavci su bili ljubazni.
    Kupovali smo hranu na pijaci. Vraćamo se kući autobusom.
    """,
    "news_style": """
    Predsednik je juče najavio nove mere. Građani su reagovali pozitivno.
    Ekonomisti smatraju da će se situacija poboljšati. Mere se primenjuju od sledeće nedelje.
    Ministri su održali konferenciju za novinare. Opozicija kritikuje vladine odluke.
    """,
}

# Expected infinitive conversions for verification
expected_conversions = {
    "radim": "raditi",
    "radio": "raditi",
    "kupujem": "kupovati",
    "kupio": "kupovati",
    "čitam": "čitati",
    "pročitao": "čitati",
    "ustao": "ustati",
    "pošao": "poći",
    "video": "videti",
    "razgovarali": "razgovarati",
    "gledali": "gledati",
    "kupovali": "kupovati",
    "vraćamo": "vraćati",
}


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
    settings_data = {"openai_api_key": "your-openai-api-key-here"}  # Replace with actual key

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
            print("📝 Note: You'll need to set a valid OpenAI API key to test the LLM processing")

    except Exception as e:
        print(f"⚠️  Settings error: {e}")

    # Test the new text processing with multiple test cases
    print("\n🧠 Testing LLM-based text processing with infinitive conversion...")

    for test_name, test_text in test_texts.items():
        print(f"\n📄 Testing {test_name}:")
        print(f"   Input: {test_text[:100]}...")

        try:
            process_response = requests.post(
                "http://localhost:3001/api/process-text",
                json={"text": test_text},
                headers={"Authorization": f"Bearer {token}"},
                timeout=60,  # Longer timeout for LLM processing
            )

            if process_response.status_code == 200:
                result = process_response.json()
                print("   ✅ Processing successful!")
                print(f"   📊 Results: {result.get('new_words', 0)} words extracted")

                translations = result.get("translations", [])
                if translations:
                    print("   🎯 Sample words (showing infinitive conversion):")
                    for i, word in enumerate(translations[:5]):  # Show first 5
                        original = word.get("original_form", "")
                        base = word["serbian_word"]
                        translation = word["english_translation"]

                        if original and original != base:
                            print(f"      {i + 1}. {original} → {base} ({translation})")
                        else:
                            print(f"      {i + 1}. {base} ({translation})")

                    # Verify some expected conversions
                    found_conversions = {}
                    for word in translations:
                        original = word.get("original_form", "")
                        base = word["serbian_word"]
                        if original and original in expected_conversions:
                            found_conversions[original] = base

                    if found_conversions:
                        print("   ✅ Verified conversions:")
                        for orig, converted in found_conversions.items():
                            expected = expected_conversions.get(orig, "unknown")
                            status = "✅" if converted == expected else "❌"
                            print(f"      {status} {orig} → {converted} (expected: {expected})")

            elif process_response.status_code == 400:
                error_data = process_response.json()
                if "OpenAI API key" in error_data.get("error", ""):
                    print(f"   ⚠️  OpenAI API key required for {test_name}")
                else:
                    print(f"   ❌ Processing failed for {test_name}: {error_data}")
            else:
                print(f"   ❌ Processing failed for {test_name}: {process_response.text}")

        except Exception as e:
            print(f"   ❌ Processing error for {test_name}: {e}")

    # Summary
    print("\n📝 Summary:")
    print(f"   • Tested {len(test_texts)} different text types")
    print(f"   • Expected infinitive conversions: {len(expected_conversions)}")
    print("   • To test with real API key, replace 'your-openai-api-key-here' with actual key")


if __name__ == "__main__":
    test_process_text()
