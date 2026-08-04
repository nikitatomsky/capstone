"""Tests for TelegramInvitationRepository."""
from datetime import datetime, timedelta

import pytest

from app.models.telegram_invitation import TelegramInvitation
from app.repositories.telegram_invitation_repository import TelegramInvitationRepository


@pytest.fixture
def repo():
    """Create in-memory repository for testing."""
    return TelegramInvitationRepository(table_name="test-invitations")


def test_create_invitation(repo):
    """Test creating invitation in repository."""
    invitation = TelegramInvitation(
        token_hash="a" * 64,
        technician_id="tech-123",
        telegram_link="https://t.me/bot?start=abc",
        expires_at=datetime.now() + timedelta(hours=1),
        created_at=datetime.now(),
        expires_at_ttl=int((datetime.now() + timedelta(hours=1)).timestamp()),
    )

    repo.create_invitation(invitation)

    # Verify can retrieve it
    retrieved = repo.get_invitation_by_hash("a" * 64)
    assert retrieved is not None
    assert retrieved.technician_id == "tech-123"
    assert retrieved.telegram_link == "https://t.me/bot?start=abc"


def test_get_invitation_by_hash_not_found(repo):
    """Test retrieving non-existent invitation returns None."""
    invitation = repo.get_invitation_by_hash("nonexistent")
    assert invitation is None


def test_mark_invitation_used(repo):
    """Test marking invitation as used."""
    invitation = TelegramInvitation(
        token_hash="b" * 64,
        technician_id="tech-456",
        telegram_link="https://t.me/bot?start=xyz",
        expires_at=datetime.now() + timedelta(hours=1),
        created_at=datetime.now(),
        expires_at_ttl=int((datetime.now() + timedelta(hours=1)).timestamp()),
    )

    repo.create_invitation(invitation)

    # Mark as used
    result = repo.mark_invitation_used("b" * 64)
    assert result is True

    # Verify used_at is set
    retrieved = repo.get_invitation_by_hash("b" * 64)
    assert retrieved.used_at is not None


def test_mark_nonexistent_invitation_used(repo):
    """Test marking non-existent invitation returns False."""
    result = repo.mark_invitation_used("nonexistent")
    assert result is False


def test_create_multiple_invitations(repo):
    """Test creating and retrieving multiple invitations."""
    invitation1 = TelegramInvitation(
        token_hash="c" * 64,
        technician_id="tech-111",
        telegram_link="https://t.me/bot?start=token1",
        expires_at=datetime.now() + timedelta(hours=1),
        created_at=datetime.now(),
        expires_at_ttl=int((datetime.now() + timedelta(hours=1)).timestamp()),
    )

    invitation2 = TelegramInvitation(
        token_hash="d" * 64,
        technician_id="tech-222",
        telegram_link="https://t.me/bot?start=token2",
        expires_at=datetime.now() + timedelta(hours=1),
        created_at=datetime.now(),
        expires_at_ttl=int((datetime.now() + timedelta(hours=1)).timestamp()),
    )

    repo.create_invitation(invitation1)
    repo.create_invitation(invitation2)

    # Verify both can be retrieved
    retrieved1 = repo.get_invitation_by_hash("c" * 64)
    retrieved2 = repo.get_invitation_by_hash("d" * 64)

    assert retrieved1.technician_id == "tech-111"
    assert retrieved2.technician_id == "tech-222"


def test_invitation_initially_unused(repo):
    """Test that new invitations have used_at as None."""
    invitation = TelegramInvitation(
        token_hash="e" * 64,
        technician_id="tech-333",
        telegram_link="https://t.me/bot?start=token3",
        expires_at=datetime.now() + timedelta(hours=1),
        created_at=datetime.now(),
        expires_at_ttl=int((datetime.now() + timedelta(hours=1)).timestamp()),
    )

    repo.create_invitation(invitation)
    retrieved = repo.get_invitation_by_hash("e" * 64)

    assert retrieved.used_at is None
