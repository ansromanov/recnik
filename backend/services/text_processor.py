"""
Serbian Text Processing Service with LLM-based infinitive conversion
"""

import json
from typing import Any, Optional

import openai


class SerbianTextProcessor:
    """
    Service for processing Serbian text and extracting vocabulary words
    with proper infinitive/base form conversion using LLM.
    """

    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the text processor.

        Args:
            openai_api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.api_key = openai_api_key
        self.model = model

    def process_text(
        self,
        text: str,
        categories: list[dict[str, Any]],
        max_words: int = 20,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """
        Process Serbian text and extract vocabulary words with proper base forms.

        Args:
            text: Input Serbian text
            categories: Available word categories
            max_words: Maximum number of words to extract
            temperature: OpenAI temperature setting

        Returns:
            Dictionary with processed words and filtering summary
        """
        if not text or not text.strip():
            return {
                "processed_words": [],
                "filtering_summary": {
                    "total_raw_words": 0,
                    "filtered_out": 0,
                    "processed_words": 0,
                    "exclusion_reasons": ["Empty text"],
                },
            }

        # Prepare category names for the prompt
        category_names = ", ".join([c.get("name", "") for c in categories])

        # Enhanced system prompt with focus on infinitive conversion
        system_prompt = f"""You are an expert Serbian linguist and vocabulary teacher. Your primary task is to extract meaningful Serbian words from text and convert them to their proper base forms (infinitive for verbs, nominative singular for nouns, etc.).

CRITICAL REQUIREMENT - INFINITIVE CONVERSION:
For verbs, you MUST convert all forms to infinitive:
- Present tense forms: "radim, radiš, radi, radimo, radite, rade" → "raditi"
- Past tense forms: "radio, radila, radilo" → "raditi"
- Aorist forms: "radih, radi, radismo" → "raditi"
- Imperative forms: "radi, radite" → "raditi"
- Common verb patterns:
  * -m/-š/-mo/-te endings → find infinitive (-ti, -ći, -ši)
  * -ao/-ala/-alo → infinitive
  * -em/-eš → infinitive (-eti, -nuti)
  * -am/-aš → infinitive (-ati)

For nouns, convert to nominative singular:
- "kuće, kućama" → "kuća"
- "automobila, automobilom" → "automobil"
- "gradova, gradovima" → "grad"
- "ljudi, ljudima" → "čovek" (person/human)

For adjectives, convert to masculine nominative singular:
- "velika, veliko, velikog" → "velik"
- "lepa, lepo, lepom" → "lep"
- "dobra, dobro, dobrog" → "dobar"

FILTERING RULES:
- ONLY Latin Serbian script (a-z, č, ć, ž, š, đ)
- EXCLUDE Cyrillic, English, URLs, numbers, special characters
- EXCLUDE proper names except major cities (Beograd, Novi Sad, Niš, etc.)
- EXCLUDE common function words: je, su, da, ne, i, u, na, za, od, do, se, će, bi, što, kako, kada, gde, koji, koja, koje, mi, ti, vi, oni, ono, ta, to, te
- EXCLUDE words shorter than 3 characters after processing
- LIMIT to {max_words} BEST vocabulary words

VERB INFINITIVE EXAMPLES:
Input: "kupujem, kupuje, kupovao" → Output: "kupovati" (to buy)
Input: "ide, idem, išao" → Output: "ići" (to go)
Input: "voli, volim, voleo" → Output: "voleti" (to love)
Input: "radi, radim, radio" → Output: "raditi" (to work)
Input: "piše, pišem, pisao" → Output: "pisati" (to write)
Input: "čita, čitam, čitao" → Output: "čitati" (to read)

NOUN/ADJECTIVE EXAMPLES:
Input: "kuće, kućama" → Output: "kuća" (house)
Input: "gradovi, gradova" → Output: "grad" (city)
Input: "velika, velikog" → Output: "velik" (big)

OUTPUT FORMAT (JSON):
{{
  "processed_words": [
    {{
      "serbian_word": "INFINITIVE or base form",
      "english_translation": "english translation of base form",
      "category": "category from: {category_names}",
      "original_form": "original inflected form from text"
    }}
  ],
  "filtering_summary": {{
    "total_raw_words": number,
    "filtered_out": number,
    "processed_words": number,
    "exclusion_reasons": ["reasons for filtering"]
  }}
}}

IMPORTANT: Always convert to proper base forms. This is critical for vocabulary learning!"""

        user_prompt = (
            f"Extract and convert to infinitive/base forms from this Serbian text:\n\n{text[:2500]}"
        )

        try:
            completion = openai.ChatCompletion.create(
                api_key=self.api_key,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=2000,
            )

            response = completion.choices[0].message["content"].strip()

            try:
                parsed_response = json.loads(response)
                return self._process_llm_response(parsed_response, categories)
            except json.JSONDecodeError as json_err:
                print(f"JSON decode error: {json_err}")
                print(f"Raw response: {response}")
                return {
                    "error": "Failed to parse LLM response",
                    "raw_response": response[:500],
                    "processed_words": [],
                }

        except Exception as api_error:
            print(f"OpenAI API error: {api_error}")
            return {
                "error": f"OpenAI API error: {api_error!s}",
                "processed_words": [],
            }

    def _process_llm_response(
        self, parsed_response: dict[str, Any], categories: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Process the LLM response and format it for the application.

        Args:
            parsed_response: Parsed JSON response from LLM
            categories: Available categories

        Returns:
            Formatted response dictionary
        """
        processed_words_data = parsed_response.get("processed_words", [])
        filtering_summary = parsed_response.get("filtering_summary", {})

        # Convert to expected format and map categories
        processed_words = []
        seen_words = set()

        for word_data in processed_words_data:
            serbian_word = word_data.get("serbian_word", "").lower().strip()

            # Skip if already seen or empty
            if not serbian_word or serbian_word in seen_words:
                continue
            seen_words.add(serbian_word)

            # Find matching category
            category = self._find_category(word_data.get("category", ""), categories)

            processed_words.append(
                {
                    "serbian_word": serbian_word,
                    "english_translation": word_data.get(
                        "english_translation", "Translation unavailable"
                    ).strip(),
                    "category_id": category.get("id", 1) if category else 1,
                    "category_name": (
                        category.get("name", "Common Words") if category else "Common Words"
                    ),
                    "original_form": word_data.get("original_form", "").strip(),
                }
            )

        return {
            "total_words": filtering_summary.get("total_raw_words", len(processed_words)),
            "existing_words": 0,  # Always 0 since we're not checking for existing words
            "new_words": len(processed_words),
            "translations": processed_words,
            "filtering_summary": filtering_summary,
        }

    def _find_category(
        self, category_name: str, categories: list[dict[str, Any]]
    ) -> Optional[dict[str, Any]]:
        """
        Find a matching category from the category name.

        Args:
            category_name: Category name from LLM
            categories: Available categories

        Returns:
            Matching category dictionary or None
        """
        if not category_name or not categories:
            return categories[0] if categories else None

        category_name_lower = category_name.lower().strip()

        # Try exact match first
        for category in categories:
            if category.get("name", "").lower() == category_name_lower:
                return category

        # Try partial match
        for category in categories:
            cat_name = category.get("name", "").lower()
            if category_name_lower in cat_name or cat_name in category_name_lower:
                return category

        # Return first category as default
        return categories[0] if categories else None

    def test_infinitive_conversion(self) -> dict[str, Any]:
        """
        Test the infinitive conversion functionality with sample Serbian text.

        Returns:
            Test results dictionary
        """
        test_text = """
        Danas radim u gradu. Kupio sam hleb i mleko. Deca se igraju u parku.
        Čitam zanimljivu knjiga. Pisao sam pisma. Volim da slušam muziku.
        Gradovi su veliki. Kuće su lepe. Automobili voze brzo.
        """

        # Mock categories for testing
        test_categories = [
            {"id": 1, "name": "Common Words"},
            {"id": 2, "name": "Verbs"},
            {"id": 3, "name": "Nouns"},
            {"id": 4, "name": "Adjectives"},
        ]

        return self.process_text(test_text, test_categories, max_words=15)


# Example usage and testing function
def test_text_processor():
    """Test function for the text processor (requires OpenAI API key)"""
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return

    processor = SerbianTextProcessor(api_key)

    # Test categories
    categories = [
        {"id": 1, "name": "Common Words"},
        {"id": 2, "name": "Verbs"},
        {"id": 3, "name": "Nouns"},
        {"id": 4, "name": "Adjectives"},
    ]

    # Test text
    test_text = """
    Jutros sam ustao rano i pošao u grad. Kupovao sam hranu na pijaci.
    Prodavci su bili ljubazni. Video sam prijatelje na kafi.
    Razgovarali smo o filmu koji smo gledali sinoć.
    Vratио sam se kući autobusom koji vozi svakoga dana.
    """

    print("🧠 Testing Serbian Text Processor...")
    print(f"📄 Input text: {test_text[:100]}...")

    result = processor.process_text(test_text, categories)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    print("✅ Text processing successful!")
    print("📊 Results:")
    print(f"   • Total words: {result.get('total_words', 0)}")
    print(f"   • New words: {result.get('new_words', 0)}")

    translations = result.get("translations", [])
    if translations:
        print("\n🎯 Processed words (showing infinitive/base forms):")
        for i, word in enumerate(translations[:10]):  # Show first 10
            original = word.get("original_form")
            base_form = word["serbian_word"]
            translation = word["english_translation"]
            category = word["category_name"]

            if original and original != base_form:
                print(f"   {i + 1}. {original} → {base_form} ({translation}) [{category}]")
            else:
                print(f"   {i + 1}. {base_form} ({translation}) [{category}]")


if __name__ == "__main__":
    test_text_processor()
