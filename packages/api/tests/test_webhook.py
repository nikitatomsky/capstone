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
    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)

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
    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)

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
    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)

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


# ============================================================================
# Integration Tests: Extraction Service Integration
# ============================================================================


def test_webhook_extracts_and_updates_intake_record(client, monkeypatch):
    """Webhook should extract data and update IntakeRecord."""
    from app.services.session_service import SessionService

    # Setup mocks
    session_service = SessionService()

    class MockExtraction:
        def extract_from_message(self, text):
            return {"location": "123 Main St", "service_type": "HVAC"}

    extraction_service = MockExtraction()

    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "extraction_service", extraction_service)

    # Send message
    payload = get_sample_telegram_update("I did HVAC work at 123 Main St", chat_id=12345)
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200

    # Check IntakeRecord was updated
    session = session_service.get_session(12345)
    assert session["intake_record"].location == "123 Main St"
    assert session["intake_record"].service_type == "HVAC"


def test_webhook_sends_followup_for_missing_fields(client, monkeypatch):
    """Webhook should ask for missing required fields."""
    from app.services.session_service import SessionService

    session_service = SessionService()

    class MockExtraction:
        def extract_from_message(self, text):
            return {"location": "456 Oak Ave"}  # Only location, missing others

    class MockTelegram:
        def __init__(self):
            self.sent_messages = []

        async def send_message(self, chat_id, text):
            self.sent_messages.append((chat_id, text))

    extraction_service = MockExtraction()
    telegram_client = MockTelegram()

    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "extraction_service", extraction_service)
    monkeypatch.setattr(app.routers.webhook, "telegram_client", telegram_client)

    # Send message
    payload = get_sample_telegram_update("Work done at 456 Oak Ave", chat_id=99999)
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200

    # Check follow-up was sent
    assert len(telegram_client.sent_messages) == 1
    chat_id, message_text = telegram_client.sent_messages[0]
    assert chat_id == 99999
    # Should ask about missing fields (employee_name, service_type, outcome)
    assert any(
        keyword in message_text.lower()
        for keyword in ["name", "type", "service", "outcome"]
    )


def test_webhook_completes_intake_when_all_fields_present(client, monkeypatch):
    """Webhook should detect completion and confirm with user."""
    from app.services.session_service import SessionService

    session_service = SessionService()

    class MockExtraction:
        def __init__(self):
            self.call_count = 0

        def extract_from_message(self, text):
            self.call_count += 1
            if self.call_count == 1:
                return {"employee_name": "John Doe", "location": "789 Elm St"}
            elif self.call_count == 2:
                return {"service_type": "Plumbing", "outcome": "completed"}
            return {}

    class MockTelegram:
        def __init__(self):
            self.sent_messages = []

        async def send_message(self, chat_id, text):
            self.sent_messages.append((chat_id, text))

    extraction_service = MockExtraction()
    telegram_client = MockTelegram()

    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "extraction_service", extraction_service)
    monkeypatch.setattr(app.routers.webhook, "telegram_client", telegram_client)

    # First message
    payload1 = get_sample_telegram_update("John Doe here, worked at 789 Elm St", chat_id=55555)
    client.post("/webhook", json=payload1)

    # Second message completes the record
    payload2 = get_sample_telegram_update("Plumbing job completed successfully", chat_id=55555)
    response = client.post("/webhook", json=payload2)

    assert response.status_code == 200

    # Check record is complete
    session = session_service.get_session(55555)
    assert session["intake_record"].is_complete()

    # Check confirmation message was sent
    assert len(telegram_client.sent_messages) >= 2
    last_message = telegram_client.sent_messages[-1][1]
    assert any(
        keyword in last_message.lower()
        for keyword in ["complete", "thank", "received", "confirmed", "recorded"]
    )


def test_multi_turn_conversation_progressively_fills_record(client, monkeypatch):
    """Multiple messages should progressively build IntakeRecord."""
    from app.services.session_service import SessionService

    session_service = SessionService()

    # Each message extracts different fields
    extractions = [
        {"employee_name": "Jane Smith"},
        {"location": "321 Pine Rd"},
        {"service_type": "Electrical"},
        {"outcome": "completed", "notes": "All outlets working"},
    ]

    class MockExtraction:
        def __init__(self):
            self.call_count = 0

        def extract_from_message(self, text):
            result = extractions[min(self.call_count, len(extractions) - 1)]
            self.call_count += 1
            return result

    class MockTelegram:
        def __init__(self):
            self.sent_messages = []

        async def send_message(self, chat_id, text):
            self.sent_messages.append((chat_id, text))

    extraction_service = MockExtraction()
    telegram_client = MockTelegram()

    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "extraction_service", extraction_service)
    monkeypatch.setattr(app.routers.webhook, "telegram_client", telegram_client)

    messages = [
        "This is Jane Smith",
        "I was at 321 Pine Rd",
        "Electrical work",
        "Everything completed, all outlets working",
    ]

    chat_id = 77777
    for msg in messages:
        payload = get_sample_telegram_update(msg, chat_id=chat_id)
        client.post("/webhook", json=payload)

    # Check final state
    session = session_service.get_session(chat_id)
    record = session["intake_record"]
    assert record.location == "321 Pine Rd"
    assert record.service_type == "Electrical"
    assert record.outcome == "completed"
    assert record.is_complete()

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
    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)

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
    import app.routers.webhook

    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)

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


# ============================================================================
# Integration Tests: Webhook-Assignment Integration (Step 2-3)
# ============================================================================


def test_webhook_links_session_to_active_assignment(client, monkeypatch):
    """Test that webhook finds and links technician's session to their active assignment."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    from app.services.session_service import SessionService

    # Create repository and session service
    repo = FakeAssignmentRepository()
    session_service = SessionService()

    # Create an active assignment for a technician
    assignment = Assignment(
        technician_chat_id=12345,
        technician_name="John Technician",
        title="Fix HVAC at Building A",
        description="Check and repair HVAC system",
        priority="high",
        status="assigned"
    )
    repo.create_assignment(assignment)

    # Inject dependencies
    import app.routers.webhook
    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "assignment_repository", repo)

    # Technician sends a message
    payload = get_sample_telegram_update("Starting work on HVAC", chat_id=12345)
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200

    # Session should be linked to the assignment
    session = session_service.get_session(12345)
    assert session is not None
    assert session["intake_record"].assignment_id == assignment.assignment_id


def test_webhook_updates_assignment_status_to_in_progress(client, monkeypatch):
    """Test that webhook updates assignment status to 'in_progress' when technician responds."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    from app.services.session_service import SessionService

    repo = FakeAssignmentRepository()
    session_service = SessionService()

    # Create assignment in "assigned" status
    assignment = Assignment(
        technician_chat_id=67890,
        technician_name="Jane Worker",
        title="Plumbing repair",
        description="Fix leaking pipe",
        priority="urgent",
        status="assigned"  # Initial status
    )
    created = repo.create_assignment(assignment)

    # Inject dependencies
    import app.routers.webhook
    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "assignment_repository", repo)

    # Technician responds (first message)
    payload = get_sample_telegram_update("I'm at the site now", chat_id=67890)
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200

    # Assignment status should be updated to "in_progress"
    updated_assignment = repo.get_assignment(created.assignment_id)
    assert updated_assignment is not None
    assert updated_assignment.status == "in_progress"


def test_webhook_links_completed_intake_to_assignment(client, monkeypatch):
    """Test that webhook updates assignment with intake_record_id when intake is complete."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    from app.services.session_service import SessionService

    repo = FakeAssignmentRepository()
    session_service = SessionService()

    # Create assignment
    assignment = Assignment(
        technician_chat_id=11111,
        technician_name="Bob Technician",
        title="Electrical work",
        description="Install new outlets",
        priority="medium",
        status="in_progress"
    )
    created = repo.create_assignment(assignment)

    # Mock extraction that provides all required fields
    class MockExtraction:
        def extract_from_message(self, text):
            return {
                "location": "456 Oak Ave",
                "service_type": "Electrical",
                "outcome": "completed"
            }

    class MockTelegram:
        async def send_message(self, chat_id, text):
            pass

    extraction_service = MockExtraction()
    telegram_client = MockTelegram()

    # Inject dependencies
    import app.routers.webhook
    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "assignment_repository", repo)
    monkeypatch.setattr(app.routers.webhook, "extraction_service", extraction_service)
    monkeypatch.setattr(app.routers.webhook, "telegram_client", telegram_client)

    # Technician sends message that completes the intake
    payload = get_sample_telegram_update(
        "Electrical work at 456 Oak Ave completed successfully",
        chat_id=11111
    )
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200

    # Assignment should be updated with intake_record_id and status "completed"
    updated_assignment = repo.get_assignment(created.assignment_id)
    assert updated_assignment is not None
    assert updated_assignment.status == "completed"
    assert updated_assignment.intake_record_id is not None
    assert updated_assignment.completed_at is not None


def test_webhook_works_without_assignment(client, monkeypatch):
    """Test that webhook still works when technician has no active assignment (backwards compat)."""
    from app.repositories.assignment_repository import FakeAssignmentRepository
    from app.services.session_service import SessionService

    repo = FakeAssignmentRepository()
    session_service = SessionService()

    # Inject dependencies (repository is empty - no assignments)
    import app.routers.webhook
    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "assignment_repository", repo)

    # Technician sends message without having an assignment
    payload = get_sample_telegram_update("Random message", chat_id=99999)
    response = client.post("/webhook", json=payload)

    # Should still work (for backwards compatibility)
    assert response.status_code == 200

    # Session should be created but without assignment link
    session = session_service.get_session(99999)
    assert session is not None
    assert session["intake_record"].assignment_id is None


def test_webhook_handles_multiple_assignments_correctly(client, monkeypatch):
    """Test that webhook links to the most recent active assignment if multiple exist."""
    import time

    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    from app.services.session_service import SessionService

    repo = FakeAssignmentRepository()
    session_service = SessionService()

    # Create two assignments for the same technician
    assignment1 = Assignment(
        technician_chat_id=33333,
        technician_name="Multi Worker",
        title="Old task",
        description="Older assignment",
        priority="low",
        status="assigned"
    )
    repo.create_assignment(assignment1)

    # Small delay to ensure different timestamps
    time.sleep(0.01)

    assignment2 = Assignment(
        technician_chat_id=33333,
        technician_name="Multi Worker",
        title="New task",
        description="Newer assignment",
        priority="high",
        status="assigned"
    )
    created2 = repo.create_assignment(assignment2)

    # Inject dependencies
    import app.routers.webhook
    monkeypatch.setattr(app.routers.webhook, "session_service", session_service)
    monkeypatch.setattr(app.routers.webhook, "assignment_repository", repo)

    # Technician sends message
    payload = get_sample_telegram_update("Working on it", chat_id=33333)
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200

    # Should link to the most recent assignment
    session = session_service.get_session(33333)
    assert session["intake_record"].assignment_id == created2.assignment_id
