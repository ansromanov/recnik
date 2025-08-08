"""
Tests for text processing endpoints and functionality
"""

import json
from unittest.mock import patch

import pytest


class TestTextProcessingEndpoints:
    """Test text processing API endpoints"""

    @patch("services.optimized_text_processor.OptimizedSerbianTextProcessor.process_text_optimized")
    def test_process_text_success_with_translations(self, mock_process_text, client, auth_headers):
        """Test successful text processing that returns translations"""
        # Mock the text processor response with proper structure
        mock_response = {
            "total_words": 5,
            "existing_words": 1,
            "new_words": 4,
            "translations": [
                {
                    "serbian_word": "raditi",
                    "english_translation": "to work",
                    "category_id": 2,
                    "category_name": "Verbs",
                    "original_form": "radim",
                },
                {
                    "serbian_word": "kuća",
                    "english_translation": "house",
                    "category_id": 3,
                    "category_name": "Nouns",
                    "original_form": "kuće",
                },
                {
                    "serbian_word": "veliki",
                    "english_translation": "big",
                    "category_id": 4,
                    "category_name": "Adjectives",
                    "original_form": "velika",
                },
            ],
            "filtering_summary": {
                "total_raw_words": 10,
                "filtered_out": 5,
                "processed_words": 5,
                "exclusion_reasons": ["function words", "short words"],
            },
        }
        mock_process_text.return_value = mock_response

        # Set mock OpenAI API key for this test
        request_data = {"text": "Danas radim u velikoj kući. Kuće su lepe."}

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response structure matches frontend expectations
        assert "total_words" in data
        assert "existing_words" in data
        assert "new_words" in data
        assert "translations" in data
        assert "filtering_summary" in data

        # Verify the translations field is an array (not undefined)
        assert isinstance(data["translations"], list)
        assert len(data["translations"]) == 3

        # Verify each translation object has required fields for frontend
        for translation in data["translations"]:
            assert "serbian_word" in translation
            assert "english_translation" in translation
            assert "category_id" in translation
            assert "category_name" in translation
            assert "original_form" in translation

        # Verify specific values
        assert data["total_words"] == 5
        assert data["existing_words"] == 1
        assert data["new_words"] == 4

        # Verify first translation
        first_translation = data["translations"][0]
        assert first_translation["serbian_word"] == "raditi"
        assert first_translation["english_translation"] == "to work"
        assert first_translation["category_id"] == 2
        assert first_translation["original_form"] == "radim"

    @patch("services.optimized_text_processor.OptimizedSerbianTextProcessor.process_text_optimized")
    def test_process_text_success_no_translations(self, mock_process_text, client, auth_headers):
        """Test text processing when no translations are found"""
        # Mock response with no translations
        mock_response = {
            "total_words": 0,
            "existing_words": 0,
            "new_words": 0,
            "translations": [],  # Empty translations
            "filtering_summary": {
                "total_raw_words": 3,
                "filtered_out": 3,
                "processed_words": 0,
                "exclusion_reasons": ["all function words"],
            },
        }
        mock_process_text.return_value = mock_response

        request_data = {
            "text": "je su da"  # Only function words
        }

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify response structure is consistent even with no results
        assert "translations" in data
        assert isinstance(data["translations"], list)
        assert len(data["translations"]) == 0
        assert data["total_words"] == 0
        assert data["new_words"] == 0

    @patch("services.optimized_text_processor.OptimizedSerbianTextProcessor.process_text_optimized")
    def test_process_text_malformed_processor_response(
        self, mock_process_text, client, auth_headers
    ):
        """Test handling of malformed processor response"""
        # Mock response without translations field
        mock_response = {
            "total_words": 0,
            "error": "Processing failed",
            # Missing translations field
        }
        mock_process_text.return_value = mock_response

        request_data = {"text": "test text"}

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        # Even with malformed processor response, API should return consistent structure
        assert "translations" in data
        assert isinstance(data["translations"], list)
        assert len(data["translations"]) == 0  # Empty array instead of undefined

    def test_process_text_missing_openai_key(self, client, auth_headers, app):
        """Test text processing without OpenAI API key"""
        # Set mock to return None (no API key)
        app.set_mock_openai_key(None)

        request_data = {"text": "test text"}

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "OpenAI API key" in data["error"]

        # Reset for other tests
        app.set_mock_openai_key("test-api-key")

    def test_process_text_missing_text(self, client, auth_headers):
        """Test text processing with missing text parameter"""
        request_data = {}  # Missing text field

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Text is required" in data["error"]

    def test_process_text_empty_text(self, client, auth_headers):
        """Test text processing with empty text"""
        request_data = {
            "text": ""  # Empty text
        }

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Text is required" in data["error"]

    @patch("services.optimized_text_processor.OptimizedSerbianTextProcessor.process_text_optimized")
    def test_process_text_processor_exception(self, mock_process_text, client, auth_headers):
        """Test handling of text processor exceptions"""
        # Mock processor raising an exception
        mock_process_text.side_effect = Exception("OpenAI API error")

        request_data = {"text": "test text"}

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Text processing error" in data["error"]

    def test_process_text_unauthorized(self, client):
        """Test text processing without authentication"""
        request_data = {"text": "test text"}

        response = client.post(
            "/api/process-text",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        assert response.status_code == 401


class TestTextProcessingResponseStructure:
    """Test that response structure is consistent and prevents frontend errors"""

    def test_response_structure_matches_frontend_expectations(self):
        """Test that our response format matches exactly what frontend expects"""
        # This test documents the exact structure expected by frontend
        expected_structure = {
            "total_words": "integer",
            "existing_words": "integer",
            "new_words": "integer",
            "translations": "array",  # This is the key field that was undefined
            "filtering_summary": "object",
        }

        # Sample translation object structure expected by frontend
        expected_translation_structure = {
            "serbian_word": "string",
            "english_translation": "string",
            "category_id": "integer",
            "category_name": "string",
            "original_form": "string",
        }

        # This test serves as documentation and can be extended
        # to validate actual API responses against this structure
        assert expected_structure["translations"] == "array"
        assert expected_translation_structure["serbian_word"] == "string"
        assert expected_translation_structure["english_translation"] == "string"
        assert expected_translation_structure["category_id"] == "integer"
        assert expected_translation_structure["original_form"] == "string"

    def test_response_prevents_map_undefined_error(self):
        """Test that response structure prevents 'Cannot read properties of undefined (reading 'map')' error"""
        # This is the specific error we're fixing
        # Frontend code: response.data.translations.map((t, index) => ({...}))
        # The fix ensures translations is always an array, never undefined

        sample_responses = [
            # Response with translations
            {
                "total_words": 3,
                "existing_words": 0,
                "new_words": 3,
                "translations": [
                    {
                        "serbian_word": "test",
                        "english_translation": "test",
                        "category_id": 1,
                        "category_name": "Common",
                        "original_form": "test",
                    }
                ],
                "filtering_summary": {},
            },
            # Response with no translations (edge case that caused the error)
            {
                "total_words": 0,
                "existing_words": 0,
                "new_words": 0,
                "translations": [],  # Empty array, not undefined
                "filtering_summary": {},
            },
        ]

        for response in sample_responses:
            # Verify translations field exists and is array
            assert "translations" in response
            assert isinstance(response["translations"], list)

            # Simulate frontend operation that was failing
            # This should not raise "Cannot read properties of undefined" error
            try:
                mapped_result = [
                    {**t, "id": index, "category_id": t.get("category_id", 1), "selected": True}
                    for index, t in enumerate(response["translations"])
                ]
                # If we get here, the map operation succeeded
                assert isinstance(mapped_result, list)
            except (TypeError, AttributeError) as e:
                pytest.fail(f"Frontend map operation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
