"""
Tests for Technician model - Following TDD RED-GREEN-REFACTOR cycle.

Test what the Technician model should do:
- Create technician profiles with required fields
- Set default timestamp for registered_at
- Validate phone number format
- Link technician to Telegram chat_id
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


def test_technician_creation():
    """Test valid technician registration with all required fields."""
    from app.models.technician import Technician

    technician = Technician(
        chat_id=12345678,
        name="John Smith",
        phone_number="+1-555-0123"
    )

    assert technician.chat_id == 12345678
    assert technician.name == "John Smith"
    assert technician.phone_number == "+1-555-0123"


def test_technician_registered_at_default():
    """Test that registered_at is auto-set to current time."""
    from app.models.technician import Technician

    technician = Technician(
        chat_id=12345678,
        name="John Smith",
        phone_number="+1-555-0123"
    )

    assert technician.registered_at is not None
    assert isinstance(technician.registered_at, datetime)
    # Verify it's recent (within last minute)
    time_diff = datetime.now(UTC) - technician.registered_at
    assert time_diff.total_seconds() < 60


def test_technician_with_explicit_registered_at():
    """Test Technician creation with explicit registered_at timestamp."""
    from app.models.technician import Technician

    custom_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    technician = Technician(
        chat_id=12345678,
        name="John Smith",
        phone_number="+1-555-0123",
        registered_at=custom_time
    )

    assert technician.registered_at == custom_time


def test_technician_phone_validation_valid_formats():
    """Test that various valid phone number formats are accepted."""
    from app.models.technician import Technician

    valid_phone_numbers = [
        "+1-555-0123",
        "+1 555 0123",
        "555-0123",
        "(555) 012-3456",
        "+44 20 7946 0958",
        "555.012.3456"
    ]

    for phone in valid_phone_numbers:
        technician = Technician(
            chat_id=12345678,
            name="John Smith",
            phone_number=phone
        )
        assert technician.phone_number == phone


def test_technician_missing_required_fields():
    """Test that missing required fields raise validation errors."""
    from app.models.technician import Technician

    # Missing all required fields
    with pytest.raises(ValidationError) as exc_info:
        Technician()

    errors = exc_info.value.errors()
    # Issue #30: Only name and phone_number are required now
    # (technician_id auto-generated, chat_id optional)
    assert len(errors) >= 2  # At least 2 required fields

    # Check that all required fields are in the error list
    error_fields = {e["loc"][0] for e in errors}
    assert "name" in error_fields
    assert "phone_number" in error_fields


# ============================================================================
# NEW TESTS FOR UUID-BASED TECHNICIAN MODEL (Issue #30)
# ============================================================================


def test_technician_creation_with_uuid():
    """Test technician created with auto-generated UUID (Issue #30)."""
    from app.models.technician import Technician

    technician = Technician(
        name="John Doe",
        phone_number="+1234567890"
    )

    # Verify UUID was auto-generated
    assert technician.technician_id is not None
    assert isinstance(technician.technician_id, str)
    assert len(technician.technician_id) == 36  # UUID format: 8-4-4-4-12
    assert "-" in technician.technician_id  # UUIDs contain hyphens


def test_technician_chat_id_optional():
    """Test chat_id is optional (Issue #30)."""
    from app.models.technician import Technician

    technician = Technician(
        name="Jane Doe",
        phone_number="+0987654321",
        chat_id=None
    )

    assert technician.chat_id is None
    assert technician.technician_id is not None  # UUID still generated


def test_technician_with_chat_id():
    """Test technician can have chat_id for Telegram integration (Issue #30)."""
    from app.models.technician import Technician

    technician = Technician(
        name="Bob Smith",
        phone_number="+1112223333",
        chat_id=123456789
    )

    assert technician.chat_id == 123456789
    assert technician.technician_id is not None


def test_technician_phone_number_can_be_uuid():
    """Test phone number accepts UUID string (placeholder) (Issue #30)."""
    import uuid

    from app.models.technician import Technician

    phone_uuid = str(uuid.uuid4())
    technician = Technician(
        name="Test User",
        phone_number=phone_uuid
    )

    assert technician.phone_number == phone_uuid
    # Verify it's a valid UUID format
    assert len(phone_uuid) == 36
    assert phone_uuid.count("-") == 4


def test_technician_create_model():
    """Test TechnicianCreate request model (Issue #30)."""
    from app.models.technician import TechnicianCreate

    technician_data = TechnicianCreate(
        name="Alice Johnson",
        phone_number="+9998887777"
    )

    assert technician_data.name == "Alice Johnson"
    assert technician_data.phone_number == "+9998887777"
    assert technician_data.chat_id is None  # Default to None


def test_technician_create_model_with_chat_id():
    """Test TechnicianCreate with optional chat_id (Issue #30)."""
    from app.models.technician import TechnicianCreate

    technician_data = TechnicianCreate(
        name="Charlie Brown",
        phone_number="+5556667777",
        chat_id=987654321
    )

    assert technician_data.chat_id == 987654321
    assert technician_data.name == "Charlie Brown"
    assert technician_data.phone_number == "+5556667777"


def test_technician_invalid_chat_id_type():
    """Test that chat_id must be an integer."""
    from app.models.technician import Technician

    with pytest.raises(ValidationError) as exc_info:
        Technician(
            chat_id="not_an_integer",  # Invalid type
            name="John Smith",
            phone_number="+1-555-0123"
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("chat_id",) for e in errors)


def test_technician_empty_name():
    """Test that name cannot be empty string."""
    from app.models.technician import Technician

    with pytest.raises(ValidationError) as exc_info:
        Technician(
            chat_id=12345678,
            name="",  # Empty string
            phone_number="+1-555-0123"
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)


def test_technician_empty_phone_number():
    """Test that phone_number cannot be empty string."""
    from app.models.technician import Technician

    with pytest.raises(ValidationError) as exc_info:
        Technician(
            chat_id=12345678,
            name="John Smith",
            phone_number=""  # Empty string
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("phone_number",) for e in errors)
