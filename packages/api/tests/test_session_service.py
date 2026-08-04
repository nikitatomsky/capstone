"""Tests for the Session Service."""

import pytest

from app.models.intake import IntakeRecord
from app.services.session_service import SessionService


@pytest.fixture
def session_service():
    """Create a fresh SessionService instance for each test."""
    return SessionService()


def test_create_new_session(session_service):
    """Test that creating a new session initializes an empty IntakeRecord."""
    chat_id = 12345

    session = session_service.get_or_create_session(chat_id)

    assert session is not None
    assert isinstance(session, dict)
    assert "intake_record" in session
    assert "conversation_history" in session
    assert "chat_id" in session

    intake_record = session["intake_record"]
    assert isinstance(intake_record, IntakeRecord)
    assert intake_record.location is None
    assert intake_record.service_type is None
    assert intake_record.outcome is None
    assert intake_record.notes is None
    assert intake_record.timestamp is None
    assert not intake_record.is_complete()


def test_retrieve_existing_session(session_service):
    """Test that retrieving an existing session returns the same instance."""
    chat_id = 12345

    # Create initial session
    first_session = session_service.get_or_create_session(chat_id)
    first_session["intake_record"].notes = "Test notes"

    # Retrieve the same session
    second_session = session_service.get_or_create_session(chat_id)

    assert second_session is not None
    assert second_session["intake_record"].notes == "Test notes"


def test_update_partial_intake_data(session_service):
    """Test incremental updates to intake record fields."""
    chat_id = 12345

    # Create session
    session_service.get_or_create_session(chat_id)

    # Update fields incrementally
    session_service.update_intake_field(chat_id, "notes", "Jane Smith notes")
    session_service.update_intake_field(chat_id, "location", "123 Main St")

    # Verify updates
    session = session_service.get_session(chat_id)
    assert session is not None
    intake_record = session["intake_record"]
    assert intake_record.notes == "Jane Smith notes"
    assert intake_record.location == "123 Main St"
    assert intake_record.service_type is None  # Still empty
    assert not session_service.is_complete(chat_id)  # Not yet complete


def test_get_nonexistent_session_returns_none(session_service):
    """Test that getting a non-existent session returns None."""
    chat_id = 99999

    session = session_service.get_session(chat_id)

    assert session is None


def test_check_record_completion(session_service):
    """Test detection of complete intake records."""
    chat_id = 12345

    # Create session
    session_service.get_or_create_session(chat_id)

    # Initially incomplete
    assert not session_service.is_complete(chat_id)

    # Fill required fields
    session_service.update_intake_field(chat_id, "location", "456 Oak Ave")
    session_service.update_intake_field(chat_id, "service_type", "HVAC Repair")
    session_service.update_intake_field(chat_id, "outcome", "completed")

    # Now complete
    assert session_service.is_complete(chat_id)

    # Optional fields don't affect completion
    session = session_service.get_session(chat_id)
    intake_record = session["intake_record"]
    assert intake_record.notes is None
    assert intake_record.timestamp is None
    assert intake_record.is_complete()


def test_list_active_sessions(session_service):
    """Test listing all active sessions."""
    # Initially empty
    assert len(session_service.list_active_sessions()) == 0

    # Create multiple sessions
    session_service.get_or_create_session(111)
    session_service.get_or_create_session(222)
    session_service.get_or_create_session(333)

    # Verify all are listed
    active_sessions = session_service.list_active_sessions()
    assert len(active_sessions) == 3
    assert 111 in active_sessions
    assert 222 in active_sessions
    assert 333 in active_sessions


def test_complete_session(session_service):
    """Test marking a session as complete and removing it."""
    chat_id = 12345

    # Create and populate session
    session_service.get_or_create_session(chat_id)
    session_service.update_intake_field(chat_id, "notes", "Sarah Lee notes")
    session_service.update_intake_field(chat_id, "location", "789 Pine Rd")
    session_service.update_intake_field(chat_id, "service_type", "Plumbing")
    session_service.update_intake_field(chat_id, "outcome", "completed")

    # Verify session exists and is complete
    assert session_service.get_session(chat_id) is not None
    assert session_service.is_complete(chat_id)

    # Complete and remove session
    completed_record = session_service.complete_session(chat_id)

    # Verify returned record has correct data
    assert completed_record is not None
    assert completed_record.notes == "Sarah Lee notes"
    assert completed_record.location == "789 Pine Rd"

    # Verify session is removed
    assert session_service.get_session(chat_id) is None
    assert chat_id not in session_service.list_active_sessions()


def test_complete_nonexistent_session_returns_none(session_service):
    """Test that completing a non-existent session returns None."""
    chat_id = 99999

    result = session_service.complete_session(chat_id)

    assert result is None


def test_update_nonexistent_session_creates_it(session_service):
    """Test that updating a non-existent session creates it first."""
    chat_id = 12345

    # Update should create session if it doesn't exist
    session_service.update_intake_field(chat_id, "notes", "Auto Created")

    # Verify session was created
    session = session_service.get_session(chat_id)
    assert session is not None
    assert session["intake_record"].notes == "Auto Created"


def test_update_invalid_field_raises_error(session_service):
    """Test that updating an invalid field name raises ValueError."""
    chat_id = 12345

    # Create session
    session_service.get_or_create_session(chat_id)

    # Attempt to update non-existent field
    with pytest.raises(ValueError, match="Unknown field"):
        session_service.update_intake_field(chat_id, "invalid_field_name", "value")


def test_negative_chat_id_raises_error(session_service):
    """Test that negative chat_id raises ValueError."""
    with pytest.raises(ValueError, match="Invalid chat_id.*must be positive"):
        session_service.get_or_create_session(-123)


def test_zero_chat_id_raises_error(session_service):
    """Test that zero chat_id raises ValueError."""
    with pytest.raises(ValueError, match="Invalid chat_id.*must be positive"):
        session_service.get_or_create_session(0)


def test_invalid_chat_id_in_all_methods(session_service):
    """Test that all methods validate chat_id."""
    invalid_chat_id = -999

    # Test get_session
    with pytest.raises(ValueError, match="Invalid chat_id"):
        session_service.get_session(invalid_chat_id)

    # Test add_message
    with pytest.raises(ValueError, match="Invalid chat_id"):
        session_service.add_message(invalid_chat_id, "test message")

    # Test update_intake_field
    with pytest.raises(ValueError, match="Invalid chat_id"):
        session_service.update_intake_field(invalid_chat_id, "notes", "Test")

    # Test is_complete
    with pytest.raises(ValueError, match="Invalid chat_id"):
        session_service.is_complete(invalid_chat_id)

    # Test complete_session
    with pytest.raises(ValueError, match="Invalid chat_id"):
        session_service.complete_session(invalid_chat_id)


# ============================================================================
# Conversation History Tests
# ============================================================================


def test_session_includes_conversation_history(session_service):
    """Test that new sessions include conversation_history field."""
    chat_id = 12345

    session = session_service.get_or_create_session(chat_id)

    # Session should be a dict with conversation_history
    assert isinstance(session, dict)
    assert "conversation_history" in session
    assert isinstance(session["conversation_history"], list)
    assert len(session["conversation_history"]) == 0
    assert "chat_id" in session
    assert session["chat_id"] == chat_id
    assert "intake_record" in session


def test_add_message_logs_to_conversation_history(session_service):
    """Test that add_message method logs messages with timestamps."""
    chat_id = 12345

    # Create session
    session_service.get_or_create_session(chat_id)

    # Add a message
    message_text = "Completed service call at 123 Main St"
    session_service.add_message(chat_id, message_text)

    # Verify message is logged
    session = session_service.get_session(chat_id)
    assert len(session["conversation_history"]) == 1

    # Check message structure
    logged_message = session["conversation_history"][0]
    assert "message" in logged_message
    assert logged_message["message"] == message_text
    assert "timestamp" in logged_message
    assert isinstance(logged_message["timestamp"], str)  # ISO format


def test_add_multiple_messages_preserves_order(session_service):
    """Test that multiple messages are tracked in order."""
    chat_id = 12345

    session_service.get_or_create_session(chat_id)

    # Add multiple messages
    messages = [
        "First message",
        "Second message",
        "Third message",
    ]

    for msg in messages:
        session_service.add_message(chat_id, msg)

    # Verify all messages are logged in order
    session = session_service.get_session(chat_id)
    assert len(session["conversation_history"]) == 3

    for i, expected_msg in enumerate(messages):
        assert session["conversation_history"][i]["message"] == expected_msg


def test_add_message_creates_session_if_needed(session_service):
    """Test that add_message creates session if it doesn't exist."""
    chat_id = 99999

    # Session doesn't exist yet
    assert session_service.get_session(chat_id) is None

    # Add message should create session
    session_service.add_message(chat_id, "Auto-created message")

    # Verify session was created
    session = session_service.get_session(chat_id)
    assert session is not None
    assert len(session["conversation_history"]) == 1
    assert session["conversation_history"][0]["message"] == "Auto-created message"


def test_conversation_history_trimming(session_service):
    """Test that conversation history is trimmed when exceeding MAX_CONVERSATION_HISTORY."""
    from app.constants import MAX_CONVERSATION_HISTORY

    chat_id = 12345
    max_history = MAX_CONVERSATION_HISTORY

    # Add more messages than the limit
    num_messages = max_history + 10
    for i in range(num_messages):
        session_service.add_message(chat_id, f"Message {i + 1}")

    # Verify history is trimmed to max limit
    session = session_service.get_session(chat_id)
    assert len(session["conversation_history"]) == max_history

    # Verify oldest messages were removed (only last MAX_CONVERSATION_HISTORY remain)
    first_message = session["conversation_history"][0]
    expected_first_message_number = num_messages - max_history + 1
    assert first_message["message"] == f"Message {expected_first_message_number}"

    # Verify most recent message is still present
    last_message = session["conversation_history"][-1]
    assert last_message["message"] == f"Message {num_messages}"

