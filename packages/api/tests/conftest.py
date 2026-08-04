"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _truncate_for_log(text: str | None, max_length: int = 100) -> str:
    """Mock truncate function for testing."""
    if not text:
        return "No text"
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."


def _get_missing_fields(intake_record):
    """Mock get_missing_fields for testing."""
    from app.services.intake_helpers import get_missing_fields
    return get_missing_fields(intake_record)


def _generate_followup_question(missing_fields):
    """Mock generate_followup_question for testing."""
    from app.services.intake_helpers import generate_followup_question
    return generate_followup_question(missing_fields)


@pytest.fixture
def client():
    """Create a FastAPI TestClient for testing."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_webhook_mocks(monkeypatch):
    """
    Automatically mock webhook dependencies for all tests.
    
    This prevents tests from calling the real Anthropic API
    and provides consistent mock implementations.
    """
    import app.routers.webhook
    from app.services.session_service import SessionService
    
    # Create fresh session service for each test
    session_service = SessionService()
    
    # Mock extraction service (returns empty dict by default)
    class MockExtractionService:
        def extract_from_message(self, text):
            return {}
    
    extraction_service = MockExtractionService()
    
    # Mock telegram client
    class MockTelegramClient:
        async def send_message(self, chat_id, text):
            pass
    
    telegram_client = MockTelegramClient()
    
    # Inject all dependencies
    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "extraction_service", extraction_service)
    monkeypatch.setattr(app.routers.webhook, "telegram_client", telegram_client)
    monkeypatch.setattr(app.routers.webhook, "_truncate_for_log", _truncate_for_log)
    monkeypatch.setattr(app.routers.webhook, "get_missing_fields", _get_missing_fields)
    monkeypatch.setattr(app.routers.webhook, "generate_followup_question", _generate_followup_question)
