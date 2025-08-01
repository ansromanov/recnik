"""
Unit tests for Serbian Text Processor service
"""

import pytest
import json
from unittest.mock import Mock, patch
from services.text_processor import SerbianTextProcessor


@pytest.mark.unit
class TestSerbianTextProcessor:
    """Test cases for SerbianTextProcessor"""

    def test_init(self):
        """Test processor initialization"""
        processor = SerbianTextProcessor("test-api-key", "gpt-4")

        assert processor.api_key == "test-api-key"
        assert processor.model == "gpt-4"

    def test_init_default_model(self):
        """Test processor initialization with default model"""
        processor = SerbianTextProcessor("test-api-key")

        assert processor.api_key == "test-api-key"
        assert processor.model == "gpt-3.5-turbo"

    def test_process_text_empty_input(self, text_processor, sample_categories):
        """Test processing empty text"""
        result = text_processor.process_text("", sample_categories)

        assert result["processed_words"] == []
        assert result["filtering_summary"]["total_raw_words"] == 0
        assert result["filtering_summary"]["filtered_out"] == 0
        assert result["filtering_summary"]["processed_words"] == 0
        assert "Empty text" in result["filtering_summary"]["exclusion_reasons"]

    def test_process_text_whitespace_only(self, text_processor, sample_categories):
        """Test processing whitespace-only text"""
        result = text_processor.process_text("   \n\t  ", sample_categories)

        assert result["processed_words"] == []
        assert result["filtering_summary"]["total_raw_words"] == 0

    @patch("openai.ChatCompletion.create")
    def test_process_text_successful_response(self, mock_create, sample_categories):
        """Test successful text processing with valid OpenAI response"""
        # Mock OpenAI response
        mock_response_content = {
            "processed_words": [
                {
                    "serbian_word": "raditi",
                    "english_translation": "to work",
                    "category": "Verbs",
                    "original_form": "radim",
                },
                {
                    "serbian_word": "kuća",
                    "english_translation": "house",
                    "category": "Nouns",
                    "original_form": "kuće",
                },
            ],
            "filtering_summary": {
                "total_raw_words": 10,
                "filtered_out": 8,
                "processed_words": 2,
                "exclusion_reasons": ["function words", "proper names"],
            },
        }

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = {
            "content": json.dumps(mock_response_content)
        }
        mock_create.return_value = mock_completion

        processor = SerbianTextProcessor("test-api-key")
        result = processor.process_text("Radim u kući.", sample_categories)

        assert result["total_words"] == 10
        assert result["new_words"] == 2
        assert result["existing_words"] == 0
        assert len(result["translations"]) == 2

        # Check first word
        first_word = result["translations"][0]
        assert first_word["serbian_word"] == "raditi"
        assert first_word["english_translation"] == "to work"
        assert first_word["category_id"] == 2  # Verbs category
        assert first_word["original_form"] == "radim"

    @patch("openai.ChatCompletion.create")
    def test_process_text_openai_api_error(self, mock_create, sample_categories):
        """Test handling of OpenAI API errors"""
        mock_create.side_effect = Exception("API rate limit exceeded")

        processor = SerbianTextProcessor("test-api-key")
        result = processor.process_text("Test text", sample_categories)

        assert "error" in result
        assert "API rate limit exceeded" in result["error"]
        assert result["processed_words"] == []

    @patch("openai.ChatCompletion.create")
    def test_process_text_invalid_json_response(self, mock_create, sample_categories):
        """Test handling of invalid JSON in OpenAI response"""
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = {"content": "Invalid JSON response"}
        mock_create.return_value = mock_completion

        processor = SerbianTextProcessor("test-api-key")
        result = processor.process_text("Test text", sample_categories)

        assert "error" in result
        assert "Failed to parse LLM response" in result["error"]
        assert "raw_response" in result
        assert result["processed_words"] == []

    def test_find_category_exact_match(self, text_processor, sample_categories):
        """Test finding category with exact name match"""
        category = text_processor._find_category("Verbs", sample_categories)

        assert category is not None
        assert category["name"] == "Verbs"
        assert category["id"] == 2

    def test_find_category_partial_match(self, text_processor, sample_categories):
        """Test finding category with partial name match"""
        category = text_processor._find_category("Verb", sample_categories)

        assert category is not None
        assert category["name"] == "Verbs"

    def test_find_category_case_insensitive(self, text_processor, sample_categories):
        """Test finding category with case insensitive match"""
        category = text_processor._find_category("VERBS", sample_categories)

        assert category is not None
        assert category["name"] == "Verbs"

    def test_find_category_no_match(self, text_processor, sample_categories):
        """Test finding category when no match exists"""
        category = text_processor._find_category("NonExistent", sample_categories)

        # Should return first category as default
        assert category is not None
        assert category["id"] == 1
        assert category["name"] == "Common Words"

    def test_find_category_empty_name(self, text_processor, sample_categories):
        """Test finding category with empty name"""
        category = text_processor._find_category("", sample_categories)

        # Should return first category as default
        assert category is not None
        assert category["id"] == 1

    def test_find_category_no_categories(self, text_processor):
        """Test finding category when no categories provided"""
        category = text_processor._find_category("Verbs", [])

        assert category is None

    def test_process_llm_response_basic(self, text_processor, sample_categories):
        """Test processing basic LLM response"""
        llm_response = {
            "processed_words": [
                {
                    "serbian_word": "ići",
                    "english_translation": "to go",
                    "category": "Verbs",
                    "original_form": "idem",
                }
            ],
            "filtering_summary": {
                "total_raw_words": 5,
                "filtered_out": 4,
                "processed_words": 1,
            },
        }

        result = text_processor._process_llm_response(llm_response, sample_categories)

        assert result["total_words"] == 5
        assert result["new_words"] == 1
        assert result["existing_words"] == 0
        assert len(result["translations"]) == 1

        word = result["translations"][0]
        assert word["serbian_word"] == "ići"
        assert word["english_translation"] == "to go"
        assert word["category_id"] == 2
        assert word["original_form"] == "idem"

    def test_process_llm_response_duplicate_words(
        self, text_processor, sample_categories
    ):
        """Test processing LLM response with duplicate words"""
        llm_response = {
            "processed_words": [
                {
                    "serbian_word": "raditi",
                    "english_translation": "to work",
                    "category": "Verbs",
                    "original_form": "radim",
                },
                {
                    "serbian_word": "raditi",  # Duplicate
                    "english_translation": "to work",
                    "category": "Verbs",
                    "original_form": "radi",
                },
            ],
            "filtering_summary": {"total_raw_words": 2, "processed_words": 2},
        }

        result = text_processor._process_llm_response(llm_response, sample_categories)

        # Should only include unique words
        assert len(result["translations"]) == 1
        assert result["translations"][0]["serbian_word"] == "raditi"

    def test_process_llm_response_empty_words(self, text_processor, sample_categories):
        """Test processing LLM response with empty/invalid words"""
        llm_response = {
            "processed_words": [
                {
                    "serbian_word": "",  # Empty word
                    "english_translation": "empty",
                    "category": "Verbs",
                },
                {
                    "serbian_word": "   ",  # Whitespace only
                    "english_translation": "whitespace",
                    "category": "Verbs",
                },
                {
                    "serbian_word": "valid",
                    "english_translation": "valid word",
                    "category": "Common Words",
                },
            ],
            "filtering_summary": {"total_raw_words": 3, "processed_words": 3},
        }

        result = text_processor._process_llm_response(llm_response, sample_categories)

        # Should only include valid words
        assert len(result["translations"]) == 1
        assert result["translations"][0]["serbian_word"] == "valid"

    def test_process_llm_response_missing_fields(
        self, text_processor, sample_categories
    ):
        """Test processing LLM response with missing fields"""
        llm_response = {
            "processed_words": [
                {
                    "serbian_word": "incomplete"
                    # Missing english_translation, category, original_form
                }
            ],
            "filtering_summary": {},
        }

        result = text_processor._process_llm_response(llm_response, sample_categories)

        assert len(result["translations"]) == 1
        word = result["translations"][0]
        assert word["serbian_word"] == "incomplete"
        assert word["english_translation"] == "Translation unavailable"
        assert word["category_id"] == 1  # Default category
        assert word["original_form"] == ""

    @patch("openai.ChatCompletion.create")
    def test_process_text_max_words_limit(self, mock_create, sample_categories):
        """Test that max_words parameter is respected"""
        # Create a response with many words
        many_words = []
        for i in range(50):
            many_words.append(
                {
                    "serbian_word": f"reč{i}",
                    "english_translation": f"word{i}",
                    "category": "Common Words",
                    "original_form": f"reč{i}",
                }
            )

        mock_response_content = {
            "processed_words": many_words,
            "filtering_summary": {"total_raw_words": 100, "processed_words": 50},
        }

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = {
            "content": json.dumps(mock_response_content)
        }
        mock_create.return_value = mock_completion

        processor = SerbianTextProcessor("test-api-key")
        result = processor.process_text("Long text", sample_categories, max_words=10)

        # Check that max_words is passed to the prompt (indirectly tested)
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args

        # Check that the system prompt contains the max_words limit
        system_message = kwargs["messages"][0]["content"]
        assert "10 BEST vocabulary words" in system_message

    @patch("openai.ChatCompletion.create")
    def test_process_text_temperature_parameter(self, mock_create, sample_categories):
        """Test that temperature parameter is passed correctly"""
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message = {
            "content": '{"processed_words": [], "filtering_summary": {}}'
        }
        mock_create.return_value = mock_completion

        processor = SerbianTextProcessor("test-api-key")
        processor.process_text("Test text", sample_categories, temperature=0.7)

        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        assert kwargs["temperature"] == 0.7

    def test_test_infinitive_conversion(self, text_processor):
        """Test the test_infinitive_conversion method"""
        # This method should return a result from process_text
        result = text_processor.test_infinitive_conversion()

        # Should return a dictionary with expected structure
        assert isinstance(result, dict)
        assert "processed_words" in result or "error" in result
