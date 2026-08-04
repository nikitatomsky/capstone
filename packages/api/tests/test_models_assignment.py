"""
Tests for Assignment model - Following TDD RED-GREEN-REFACTOR cycle.

Test what the Assignment model should do:
- Create assignments with required fields
- Set default values for status and timestamps
- Validate priority and status enum values
- Generate UUID for assignment_id if not provided
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


def test_assignment_creation_with_required_fields():
    """Test minimal valid assignment creation with all required fields."""
    from app.models.assignment import Assignment

    assignment = Assignment(
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="HVAC Repair - Building 5",
        description="Check heating system in Building 5, Room 203",
        priority="high"
    )

    assert assignment.technician_chat_id == 12345678
    assert assignment.technician_name == "John Smith"
    assert assignment.title == "HVAC Repair - Building 5"
    assert assignment.description == "Check heating system in Building 5, Room 203"
    assert assignment.priority == "high"


def test_assignment_defaults():
    """Test that Assignment sets correct default values."""
    from app.models.assignment import Assignment

    assignment = Assignment(
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="Test Assignment",
        description="Test description",
        priority="low"
    )

    # Default status should be "pending"
    assert assignment.status == "pending"

    # created_at should be auto-set to current time
    assert assignment.created_at is not None
    assert isinstance(assignment.created_at, datetime)

    # assignment_id should be auto-generated UUID string
    assert assignment.assignment_id is not None
    assert isinstance(assignment.assignment_id, str)
    assert len(assignment.assignment_id) > 0

    # Optional timestamps should be None by default
    assert assignment.assigned_at is None
    assert assignment.completed_at is None
    assert assignment.intake_record_id is None


def test_assignment_invalid_priority():
    """Test that Assignment validates priority enum values."""
    from app.models.assignment import Assignment

    with pytest.raises(ValidationError) as exc_info:
        Assignment(
            technician_chat_id=12345678,
            technician_name="John Smith",
            title="Test Assignment",
            description="Test description",
            priority="invalid_priority"  # Invalid value
        )

    errors = exc_info.value.errors()
    assert len(errors) > 0
    # Check that the error is about the priority field
    assert any(e["loc"] == ("priority",) for e in errors)


def test_assignment_invalid_status():
    """Test that Assignment validates status enum values."""
    from app.models.assignment import Assignment

    with pytest.raises(ValidationError) as exc_info:
        Assignment(
            technician_chat_id=12345678,
            technician_name="John Smith",
            title="Test Assignment",
            description="Test description",
            priority="low",
            status="invalid_status"  # Invalid value
        )

    errors = exc_info.value.errors()
    assert len(errors) > 0
    # Check that the error is about the status field
    assert any(e["loc"] == ("status",) for e in errors)


def test_assignment_with_all_fields():
    """Test Assignment creation with all fields including optional ones."""
    from app.models.assignment import Assignment

    now = datetime.now(UTC)

    assignment = Assignment(
        assignment_id="test-uuid-123",
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="Complete Assignment",
        description="Full test description",
        priority="urgent",
        status="completed",
        created_at=now,
        assigned_at=now,
        completed_at=now,
        intake_record_id="intake-uuid-456"
    )

    assert assignment.assignment_id == "test-uuid-123"
    assert assignment.status == "completed"
    assert assignment.assigned_at == now
    assert assignment.completed_at == now
    assert assignment.intake_record_id == "intake-uuid-456"


def test_assignment_valid_priorities():
    """Test all valid priority values are accepted."""
    from app.models.assignment import Assignment

    valid_priorities = ["low", "medium", "high", "urgent"]

    for priority in valid_priorities:
        assignment = Assignment(
            technician_chat_id=12345678,
            technician_name="John Smith",
            title="Test",
            description="Test",
            priority=priority
        )
        assert assignment.priority == priority


def test_assignment_valid_statuses():
    """Test all valid status values are accepted."""
    from app.models.assignment import Assignment

    valid_statuses = ["pending", "assigned", "in_progress", "completed", "cancelled"]

    for status in valid_statuses:
        assignment = Assignment(
            technician_chat_id=12345678,
            technician_name="John Smith",
            title="Test",
            description="Test",
            priority="low",
            status=status
        )
        assert assignment.status == status


def test_assignment_missing_required_fields():
    """Test that missing required fields raise validation errors."""
    from app.models.assignment import Assignment

    # Missing all required fields
    with pytest.raises(ValidationError) as exc_info:
        Assignment()

    errors = exc_info.value.errors()
    assert len(errors) >= 5  # At least 5 required fields

    # Check that all required fields are in the error list
    error_fields = {e["loc"][0] for e in errors}
    assert "technician_chat_id" in error_fields
    assert "technician_name" in error_fields
    assert "title" in error_fields
    assert "description" in error_fields
    assert "priority" in error_fields
