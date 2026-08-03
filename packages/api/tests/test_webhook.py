"""Tests for the Telegram webhook endpoint."""

from datetime import UTC, datetime


def get_sample_telegram_update(
    text: str = "Test message",
    chat_id: int = 999,
    user_id: int = 888,
    first_name: str = "Technician",
    message_id: int = 1,
    update_id: int = 123456789,
) -> dict:
    """
    Generate a sample Telegram Update payload for testing.

    Args:
        text: Message text content
        chat_id: Chat identifier
        user_id: User identifier
        first_name: User's first name
        message_id: Message identifier
        update_id: Update identifier

    Returns:
        Dictionary representing a Telegram Update payload
    """
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": first_name,
            },
            "chat": {
                "id": chat_id,
                "type": "private",
                "first_name": first_name,
            },
            "date": int(datetime.now(UTC).timestamp()),
            "text": text,
        },
    }


def test_webhook_accepts_valid_telegram_message(client):
    """Test that webhook accepts a properly formatted Telegram update."""
    payload = get_sample_telegram_update(
        text="Completed service call at 123 Main St",
        chat_id=999,
        user_id=888,
    )

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Message received"


def test_webhook_extracts_message_text_and_chat_id(client):
    """Test that webhook correctly extracts message text and chat_id."""
    test_text = "This is a test message from field technician"
    test_chat_id = 12345

    payload = get_sample_telegram_update(text=test_text, chat_id=test_chat_id)

    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data.get("received_text") == test_text
    assert data.get("chat_id") == test_chat_id


def test_webhook_rejects_payload_missing_message(client):
    """Test that webhook returns 400 for payload missing 'message' field."""
    invalid_payload = {
        "update_id": 123456789,
        # Missing 'message' field
    }

    response = client.post("/webhook", json=invalid_payload)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_webhook_rejects_payload_missing_update_id(client):
    """Test that webhook returns 400 for payload missing 'update_id' field."""
    invalid_payload = {
        # Missing 'update_id' field
        "message": {
            "message_id": 1,
            "from": {"id": 888, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 999, "type": "private", "first_name": "Test"},
            "date": int(datetime.now(UTC).timestamp()),
            "text": "Test",
        },
    }

    response = client.post("/webhook", json=invalid_payload)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_webhook_rejects_empty_payload(client):
    """Test that webhook returns 400 for empty JSON payload."""
    response = client.post("/webhook", json={})

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_webhook_rejects_message_without_text(client):
    """Test that webhook handles messages without text field."""
    payload = get_sample_telegram_update()
    del payload["message"]["text"]  # Remove text field

    response = client.post("/webhook", json=payload)

    # Should still return 200 but handle gracefully
    # (some Telegram messages don't have text, like photos)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_webhook_handles_various_message_types(client):
    """Test that webhook processes different message content appropriately."""
    test_cases = [
        "Simple message",
        "Service call at 123 Main St - HVAC repair completed",
        "Multi-line message\nWith line breaks\nAnd details",
        "Message with special chars: @#$%^&*()",
    ]

    for text in test_cases:
        payload = get_sample_telegram_update(text=text)
        response = client.post("/webhook", json=payload)

        assert response.status_code == 200, f"Failed for text: {text}"
        data = response.json()
        assert data.get("received_text") == text
