"""Tests for LLM extraction service."""

import json

import pytest

from app.exceptions import LLMParseError
from app.services.extraction_service import ExtractionService, LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response: str):
        self.response = response
        self.called_with = []

    def generate(self, prompt: str, system_message: str) -> str:
        """Return predefined response and track calls."""
        self.called_with.append((prompt, system_message))
        return self.response


@pytest.fixture
def extraction_service_complete():
    """ExtractionService with mock that returns complete data."""
    mock_response = json.dumps(
        {
            "employee_name": "John Doe",
            "location": "123 Main Street",
            "service_type": "HVAC Repair",
            "outcome": "completed",
            "notes": "Replaced air filter, system running normally",
        }
    )
    mock_provider = MockLLMProvider(mock_response)
    return ExtractionService(mock_provider)


@pytest.fixture
def extraction_service_partial():
    """ExtractionService with mock that returns partial data."""
    mock_response = json.dumps({"location": "456 Oak Avenue", "service_type": "Plumbing"})
    mock_provider = MockLLMProvider(mock_response)
    return ExtractionService(mock_provider)


@pytest.fixture
def extraction_service_empty():
    """ExtractionService with mock that returns empty data."""
    mock_response = json.dumps({})
    mock_provider = MockLLMProvider(mock_response)
    return ExtractionService(mock_provider)


@pytest.fixture
def extraction_service_malformed():
    """ExtractionService with mock that returns malformed JSON."""
    mock_provider = MockLLMProvider("This is not valid JSON at all!")
    return ExtractionService(mock_provider)


def test_extract_complete_record(extraction_service_complete):
    """Should extract all fields from comprehensive message."""
    message = "Hi, this is John Doe. I completed an HVAC repair at 123 Main Street. Replaced air filter, system running normally now."

    result = extraction_service_complete.extract_from_message(message)

    assert result["employee_name"] == "John Doe"
    assert result["location"] == "123 Main Street"
    assert result["service_type"] == "HVAC Repair"
    assert result["outcome"] == "completed"
    assert result["notes"] == "Replaced air filter, system running normally"


def test_extract_partial_record(extraction_service_partial):
    """Should extract only available fields."""
    message = "Just finished a plumbing job at 456 Oak Avenue"

    result = extraction_service_partial.extract_from_message(message)

    assert result["location"] == "456 Oak Avenue"
    assert result["service_type"] == "Plumbing"
    assert "employee_name" not in result
    assert "outcome" not in result


def test_extract_no_data(extraction_service_empty):
    """Should return empty dict when no data can be extracted."""
    message = "Hello there!"

    result = extraction_service_empty.extract_from_message(message)

    assert result == {}


def test_extract_handles_malformed_json(extraction_service_malformed):
    """Should raise LLMParseError when LLM response is not valid JSON."""
    message = "Some message"

    with pytest.raises(LLMParseError, match="invalid JSON format"):
        extraction_service_malformed.extract_from_message(message)


def test_extraction_calls_llm_provider():
    """Should call LLM provider with message and system prompt."""
    mock_provider = MockLLMProvider(json.dumps({"location": "Test St"}))
    service = ExtractionService(mock_provider)

    message = "Completed work at Test St"
    service.extract_from_message(message)

    assert len(mock_provider.called_with) == 1
    prompt, system_message = mock_provider.called_with[0]
    assert message in prompt
    assert "extract" in system_message.lower()


def test_extract_rejects_empty_message():
    """Should raise ValueError for empty message text."""
    mock_provider = MockLLMProvider(json.dumps({}))
    service = ExtractionService(mock_provider)

    with pytest.raises(ValueError, match="cannot be empty"):
        service.extract_from_message("")

    with pytest.raises(ValueError, match="cannot be empty"):
        service.extract_from_message("   ")


def test_extract_rejects_non_string_message():
    """Should raise TypeError for non-string message text."""
    mock_provider = MockLLMProvider(json.dumps({}))
    service = ExtractionService(mock_provider)

    with pytest.raises(TypeError, match="must be string"):
        service.extract_from_message(123)  # type: ignore

    with pytest.raises(TypeError, match="must be string"):
        service.extract_from_message(None)  # type: ignore


def test_extract_truncates_long_messages():
    """Should truncate messages exceeding maximum length."""
    mock_response = json.dumps({"location": "Test"})
    mock_provider = MockLLMProvider(mock_response)
    service = ExtractionService(mock_provider)

    # Create message longer than MAX_MESSAGE_LENGTH (4096)
    long_message = "A" * 5000
    result = service.extract_from_message(long_message)

    # Should still process successfully
    assert "location" in result
    
    # Check that truncated message was passed to provider
    prompt, _ = mock_provider.called_with[0]
    # The prompt includes the message, so check it's not the full 5000 chars
    assert len(prompt) < 5000


@pytest.mark.skip(reason="Integration test - requires real API key")
def test_anthropic_integration():
    """Integration test with real Anthropic API (skipped by default)."""
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    from app.services.llm_providers import AnthropicProvider

    provider = AnthropicProvider(api_key)
    service = ExtractionService(provider)

    message = "Hi, I'm Jane Smith. Completed electrical work at 789 Pine Rd. Everything is working perfectly."
    result = service.extract_from_message(message)

    # Real API should extract fields
    assert "employee_name" in result or "location" in result
    print(f"Extracted: {result}")


# ============================================================================
# Advanced Test Cases (Priority 3)
# ============================================================================


def test_extract_with_utf8_characters():
    """Should handle UTF-8 characters (non-ASCII) correctly."""
    mock_response = json.dumps({
        "employee_name": "José García",
        "location": "123 Rue de la Paix, Montréal",
        "notes": "Réparation complète ✓"
    })
    mock_provider = MockLLMProvider(mock_response)
    service = ExtractionService(mock_provider)

    message = "Réparé par José García à 123 Rue de la Paix, Montréal ✓"
    result = service.extract_from_message(message)

    assert result["employee_name"] == "José García"
    assert result["location"] == "123 Rue de la Paix, Montréal"
    assert "✓" in result["notes"]


def test_extract_with_special_json_characters():
    """Should handle messages with quotes and special characters."""
    mock_response = json.dumps({
        "location": '123 "Main" Street',
        "notes": "Customer said: \"Works great!\"\nNew line test"
    })
    mock_provider = MockLLMProvider(mock_response)
    service = ExtractionService(mock_provider)

    message = 'Customer at 123 "Main" Street said: "Works great!"'
    result = service.extract_from_message(message)

    assert result["location"] == '123 "Main" Street'
    assert "Works great!" in result["notes"]


def test_extract_with_invalid_field_types():
    """Should log warning but not fail when extracted data has invalid types."""
    # LLM returns wrong type for a field (string instead of valid outcome)
    mock_response = json.dumps({
        "location": "123 Main St",
        "outcome": "invalid_outcome_value"  # Not one of: completed, needs_followup, etc.
    })
    mock_provider = MockLLMProvider(mock_response)
    service = ExtractionService(mock_provider)

    message = "Work done at 123 Main St"
    
    # Should still return data even if validation fails
    result = service.extract_from_message(message)
    
    assert "location" in result
    assert result["location"] == "123 Main St"


def test_extract_with_extra_fields():
    """Should handle LLM returning fields not in IntakeRecord schema."""
    mock_response = json.dumps({
        "location": "123 Main St",
        "extra_field": "This field doesn't exist in schema",
        "another_unknown": "Should be ignored"
    })
    mock_provider = MockLLMProvider(mock_response)
    service = ExtractionService(mock_provider)

    message = "Work at 123 Main St"
    result = service.extract_from_message(message)

    # Should still return all data, including extra fields
    assert result["location"] == "123 Main St"
    assert "extra_field" in result  # Returned but will be ignored when creating IntakeRecord


def test_llm_provider_factory():
    """Should create providers using factory pattern."""
    from app.services.llm_factory import create_llm_provider

    # Test with mock API key to avoid requiring real key
    provider = create_llm_provider("anthropic", api_key="test-key-123")
    
    assert provider is not None
    assert hasattr(provider, "generate")


def test_llm_factory_unknown_provider():
    """Should raise ValueError for unknown provider type."""
    from app.services.llm_factory import create_llm_provider

    with pytest.raises(ValueError, match="Unknown provider type"):
        create_llm_provider("unknown_provider")


def test_llm_factory_openai_not_implemented():
    """Should raise NotImplementedError for OpenAI (not yet supported)."""
    from app.services.llm_factory import create_llm_provider

    with pytest.raises(NotImplementedError, match="OpenAI provider not yet implemented"):
        create_llm_provider("openai")


def test_extraction_service_factory():
    """Should create ExtractionService using convenience factory."""
    from app.services.llm_factory import create_extraction_service

    service = create_extraction_service("anthropic", api_key="test-key-123")
    
    assert service is not None
    assert hasattr(service, "extract_from_message")
