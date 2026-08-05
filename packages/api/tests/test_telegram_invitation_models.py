"""Tests for Telegram invitation Pydantic models."""
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.telegram_invitation import TelegramInvitation, TelegramInvitationCreate


def test_telegram_invitation_create_valid():
    """Test creating invitation with all required fields."""
    invitation = TelegramInvitationCreate(
        token_hash="a" * 64,  # SHA-256 produces 64 hex chars
        technician_id="tech-uuid-123",
        telegram_link="https://t.me/mybot?start=abc123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    assert invitation.token_hash == "a" * 64
    assert invitation.technician_id == "tech-uuid-123"
    assert invitation.telegram_link.startswith("https://t.me/")


def test_telegram_invitation_with_defaults():
    """Test invitation with optional fields using defaults."""
    invitation = TelegramInvitation(
        token_hash="a" * 64,
        technician_id="tech-uuid-123",
        telegram_link="https://t.me/mybot?start=abc123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
    )
    assert invitation.used_at is None


def test_telegram_invitation_used():
    """Test invitation marked as used."""
    invitation = TelegramInvitation(
        token_hash="a" * 64,
        technician_id="tech-uuid-123",
        telegram_link="https://t.me/mybot?start=abc123",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
        used_at=datetime.now(UTC),
    )
    assert invitation.used_at is not None


def test_telegram_invitation_create_invalid_hash_length():
    """Test that token_hash must be exactly 64 characters."""
    with pytest.raises(ValidationError) as exc_info:
        TelegramInvitationCreate(
            token_hash="too_short",  # Not 64 characters
            technician_id="tech-uuid-123",
            telegram_link="https://t.me/mybot?start=abc123",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("token_hash",) for e in errors)


def test_telegram_invitation_create_missing_required_field():
    """Test that all required fields must be provided."""
    with pytest.raises(ValidationError) as exc_info:
        TelegramInvitationCreate(
            token_hash="a" * 64,
            technician_id="tech-uuid-123",
            # Missing telegram_link and expires_at
        )

    errors = exc_info.value.errors()
    assert len(errors) == 2  # Two missing fields
