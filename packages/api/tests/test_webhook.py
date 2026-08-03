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


# ============================================================================
# Integration Tests: Webhook-Session Integration
# ============================================================================


def test_webhook_creates_session_for_new_chat(client, monkeypatch):
    """Test that webhook creates a new session for first message from chat_id."""
    from app.services.session_service import SessionService

    # Create a session service instance for testing
    session_service = SessionService()

    # Inject session service into main module
    import app.main

    monkeypatch.setattr(app.main, "session_service", session_service)

    # Send first message from a new chat
    payload = get_sample_telegram_update("First message", chat_id=12345)
    response = client.post("/webhook", json=payload)

    # Webhook should succeed
    assert response.status_code == 200

    # Session should be created for this chat_id
    session = session_service.get_session(12345)
    assert session is not None
    assert session["chat_id"] == 12345
    assert "intake_record" in session
    assert "conversation_history" in session


def test_webhook_retrieves_existing_session(client, monkeypatch):
    """Test that webhook reuses existing session for subsequent messages."""
    from app.services.session_service import SessionService

    session_service = SessionService()
    import app.main

    monkeypatch.setattr(app.main, "session_service", session_service)

    # Send first message
    payload1 = get_sample_telegram_update("First message", chat_id=12345)
    client.post("/webhook", json=payload1)
    session1 = session_service.get_session(12345)

    # Send second message from same chat
    payload2 = get_sample_telegram_update("Second message", chat_id=12345)
    client.post("/webhook", json=payload2)
    session2 = session_service.get_session(12345)

    # Should be the exact same session object (not a new one)
    assert session1 is session2


def test_webhook_logs_message_to_conversation_history(client, monkeypatch):
    """Test that webhook adds messages to conversation history."""
    from app.services.session_service import SessionService

    session_service = SessionService()
    import app.main

    monkeypatch.setattr(app.main, "session_service", session_service)

    # Send multiple messages from same chat
    messages = [
        "Hello, I completed a service call",
        "It was at 123 Main Street",
        "HVAC repair completed successfully",
    ]

    for msg in messages:
        payload = get_sample_telegram_update(msg, chat_id=99999)
        client.post("/webhook", json=payload)

    # Verify all messages are in conversation history
    session = session_service.get_session(99999)
    assert "conversation_history" in session
    assert len(session["conversation_history"]) == 3

    # Check message content
    assert session["conversation_history"][0]["message"] == messages[0]
    assert session["conversation_history"][1]["message"] == messages[1]
    assert session["conversation_history"][2]["message"] == messages[2]

    # Each message should have a timestamp
    for entry in session["conversation_history"]:
        assert "timestamp" in entry


def test_webhook_tracks_different_chats_separately(client, monkeypatch):
    """Test that webhook maintains separate sessions for different chat_ids."""
    from app.services.session_service import SessionService

    session_service = SessionService()
    import app.main

    monkeypatch.setattr(app.main, "session_service", session_service)

    # Send messages from two different chats
    payload1 = get_sample_telegram_update("Message from chat 1", chat_id=11111)
    payload2 = get_sample_telegram_update("Message from chat 2", chat_id=22222)

    client.post("/webhook", json=payload1)
    client.post("/webhook", json=payload2)

    # Each chat should have its own session
    session1 = session_service.get_session(11111)
    session2 = session_service.get_session(22222)

    assert session1 is not session2
    assert session1["chat_id"] == 11111
    assert session2["chat_id"] == 22222
    assert len(session1["conversation_history"]) == 1
    assert len(session2["conversation_history"]) == 1


def test_webhook_returns_message_count_in_response(client, monkeypatch):
    """Test that webhook response includes message count from session."""
    from app.services.session_service import SessionService

    session_service = SessionService()
    import app.main

    monkeypatch.setattr(app.main, "session_service", session_service)

    # Send first message
    payload1 = get_sample_telegram_update("First message", chat_id=55555)
    response1 = client.post("/webhook", json=payload1)
    data1 = response1.json()

    # Should return message count
    assert "message_count" in data1
    assert data1["message_count"] == 1

    # Send second message
    payload2 = get_sample_telegram_update("Second message", chat_id=55555)
    response2 = client.post("/webhook", json=payload2)
    data2 = response2.json()

    # Message count should increment
    assert data2["message_count"] == 2


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
