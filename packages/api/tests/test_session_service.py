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
    assert isinstance(session, IntakeRecord)
    assert session.employee_name is None
    assert session.location is None
    assert session.service_type is None
    assert session.outcome is None
    assert session.notes is None
    assert session.timestamp is None
    assert not session.is_complete()


def test_retrieve_existing_session(session_service):
    """Test that retrieving an existing session returns the same instance."""
    chat_id = 12345

    # Create initial session
    first_session = session_service.get_or_create_session(chat_id)
    first_session.employee_name = "John Doe"

    # Retrieve the same session
    second_session = session_service.get_or_create_session(chat_id)

    assert second_session is not None
    assert second_session.employee_name == "John Doe"


def test_update_partial_intake_data(session_service):
    """Test incremental updates to intake record fields."""
    chat_id = 12345

    # Create session
    session_service.get_or_create_session(chat_id)

    # Update fields incrementally
    session_service.update_intake_field(chat_id, "employee_name", "Jane Smith")
    session_service.update_intake_field(chat_id, "location", "123 Main St")

    # Verify updates
    session = session_service.get_session(chat_id)
    assert session is not None
    assert session.employee_name == "Jane Smith"
    assert session.location == "123 Main St"
    assert session.service_type is None  # Still empty
    assert not session.is_complete()  # Not yet complete


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
    session_service.update_intake_field(chat_id, "employee_name", "Mike Johnson")
    session_service.update_intake_field(chat_id, "location", "456 Oak Ave")
    session_service.update_intake_field(chat_id, "service_type", "HVAC Repair")
    session_service.update_intake_field(chat_id, "outcome", "completed")

    # Now complete
    assert session_service.is_complete(chat_id)

    # Optional fields don't affect completion
    session = session_service.get_session(chat_id)
    assert session.notes is None
    assert session.timestamp is None
    assert session.is_complete()


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
    session_service.update_intake_field(chat_id, "employee_name", "Sarah Lee")
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
    assert completed_record.employee_name == "Sarah Lee"
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
    session_service.update_intake_field(chat_id, "employee_name", "Auto Created")

    # Verify session was created
    session = session_service.get_session(chat_id)
    assert session is not None
    assert session.employee_name == "Auto Created"
