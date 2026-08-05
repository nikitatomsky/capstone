"""Tests for TelegramInvitationService."""
import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from app.models.telegram_invitation import TelegramInvitation
from app.services.telegram_invitation_service import TelegramInvitationService


@pytest.fixture
def mock_repo():
    """Mock invitation repository."""
    return Mock()


@pytest.fixture
def service(mock_repo):
    """Create service with mock repository."""
    return TelegramInvitationService(
        repository=mock_repo,
        bot_username="test_bot",
        ttl_seconds=3600,
    )


def test_generate_invitation_creates_secure_token(service, mock_repo):
    """Test that generated tokens are URL-safe and sufficiently random."""
    mock_repo.create_invitation.return_value = None

    invitation = service.generate_invitation(technician_id="tech-123")

    # Token should be embedded in deeplink
    assert "https://t.me/test_bot?start=" in invitation.telegram_link
    token = invitation.telegram_link.split("start=")[1]

    # Token should be URL-safe (base64url)
    assert len(token) > 20  # Sufficiently long
    assert all(c.isalnum() or c in "-_" for c in token)  # URL-safe chars


def test_generate_invitation_stores_hash_only(service, mock_repo):
    """Test that only SHA-256 hash is stored, not raw token."""
    mock_repo.create_invitation.return_value = None

    invitation = service.generate_invitation(technician_id="tech-123")

    # Token hash should be 64 hex characters (SHA-256)
    assert len(invitation.token_hash) == 64
    assert all(c in "0123456789abcdef" for c in invitation.token_hash)

    # Hash should not match the token (hash is one-way)
    token = invitation.telegram_link.split("start=")[1]
    assert invitation.token_hash != token


def test_generate_invitation_sets_expiration(service, mock_repo):
    """Test that invitation has correct expiration."""
    mock_repo.create_invitation.return_value = None

    before = datetime.now(UTC)
    invitation = service.generate_invitation(technician_id="tech-123")
    datetime.now(UTC)

    # Expiration should be ~1 hour from now (3600 seconds)
    expected_expiry = before + timedelta(seconds=3600)
    assert invitation.expires_at > expected_expiry - timedelta(seconds=5)
    assert invitation.expires_at < expected_expiry + timedelta(seconds=5)


def test_generate_invitation_persists_to_repo(service, mock_repo):
    """Test that invitation is saved via repository."""
    mock_repo.create_invitation.return_value = None

    invitation = service.generate_invitation(technician_id="tech-123")

    # Repository should be called once
    mock_repo.create_invitation.assert_called_once()
    call_args = mock_repo.create_invitation.call_args[0][0]

    # Check persisted data
    assert call_args.technician_id == "tech-123"
    assert call_args.token_hash == invitation.token_hash
    assert call_args.expires_at == invitation.expires_at


def test_validate_token_with_valid_token(service, mock_repo):
    """Test validating a valid, unexpired, unused token."""
    # Generate a token
    token = "test-token-abc123"
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Mock repository to return valid invitation
    mock_repo.get_invitation_by_hash.return_value = TelegramInvitation(
        token_hash=token_hash,
        technician_id="tech-123",
        telegram_link="https://t.me/bot?start=" + token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
        used_at=None,
    )
    mock_repo.mark_invitation_used.return_value = True

    # Validate token
    technician_id = service.validate_token(token)

    assert technician_id == "tech-123"
    mock_repo.mark_invitation_used.assert_called_once_with(token_hash)


def test_validate_token_with_expired_token(service, mock_repo):
    """Test validating an expired token returns None."""
    token = "expired-token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Mock repository to return expired invitation
    mock_repo.get_invitation_by_hash.return_value = TelegramInvitation(
        token_hash=token_hash,
        technician_id="tech-123",
        telegram_link="https://t.me/bot?start=" + token,
        expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired
        created_at=datetime.now(UTC) - timedelta(hours=2),
        used_at=None,
    )

    technician_id = service.validate_token(token)

    assert technician_id is None
    mock_repo.mark_invitation_used.assert_not_called()


def test_validate_token_with_already_used_token(service, mock_repo):
    """Test validating an already-used token returns None."""
    token = "used-token"
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Mock repository to return used invitation
    mock_repo.get_invitation_by_hash.return_value = TelegramInvitation(
        token_hash=token_hash,
        technician_id="tech-123",
        telegram_link="https://t.me/bot?start=" + token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
        used_at=datetime.now(UTC) - timedelta(minutes=5),  # Already used
    )

    technician_id = service.validate_token(token)

    assert technician_id is None
    mock_repo.mark_invitation_used.assert_not_called()


def test_validate_token_with_invalid_token(service, mock_repo):
    """Test validating a non-existent token returns None."""
    token = "invalid-token"

    # Mock repository to return None (token not found)
    mock_repo.get_invitation_by_hash.return_value = None

    technician_id = service.validate_token(token)

    assert technician_id is None
    mock_repo.mark_invitation_used.assert_not_called()


def test_cleanup_expired_returns_zero(service):
    """Test cleanup method exists but returns 0 (DynamoDB TTL handles cleanup)."""
    result = service.cleanup_expired()
    assert result == 0
