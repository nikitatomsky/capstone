"""Service for generating and validating Telegram bot invitation tokens."""
import hashlib
import secrets
from datetime import datetime, timedelta

from app.models.telegram_invitation import TelegramInvitation
from app.repositories.telegram_invitation_repository import TelegramInvitationRepository


class TelegramInvitationService:
    """Service for managing Telegram bot invitations."""

    def __init__(
        self,
        repository: TelegramInvitationRepository,
        bot_username: str,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize invitation service.

        Args:
            repository: Repository for persisting invitations
            bot_username: Telegram bot username (e.g., "my_field_bot")
            ttl_seconds: Token expiration time in seconds (default: 1 hour)
        """
        self.repository = repository
        self.bot_username = bot_username
        self.ttl_seconds = ttl_seconds

    def generate_invitation(self, technician_id: str) -> TelegramInvitation:
        """
        Generate secure invitation token and deeplink.

        Args:
            technician_id: UUID of technician receiving invitation

        Returns:
            TelegramInvitation with token hash and deeplink
        """
        # Generate cryptographically secure token (32 bytes = 43 base64url chars)
        token = secrets.token_urlsafe(32)

        # Hash token with SHA-256 before storing
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Generate Telegram deeplink
        telegram_link = f"https://t.me/{self.bot_username}?start={token}"

        # Set expiration
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        expires_at_ttl = int(expires_at.timestamp())

        # Create invitation object
        invitation = TelegramInvitation(
            token_hash=token_hash,
            technician_id=technician_id,
            telegram_link=telegram_link,
            expires_at=expires_at,
            created_at=now,
            used_at=None,
            expires_at_ttl=expires_at_ttl,
        )

        # Persist to DynamoDB (via repository)
        self.repository.create_invitation(invitation)

        return invitation

    def validate_token(self, token: str) -> str | None:
        """
        Validate invitation token and return technician_id if valid.

        Args:
            token: Raw invitation token from Telegram /start command

        Returns:
            technician_id if token is valid, unused, and not expired
            None if token is invalid, used, or expired
        """
        # Hash the token to look up in DynamoDB
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Retrieve invitation from repository
        invitation = self.repository.get_invitation_by_hash(token_hash)

        if not invitation:
            return None  # Token not found

        # Check if already used
        if invitation.used_at is not None:
            return None  # Token already used

        # Check if expired
        if datetime.now() > invitation.expires_at:
            return None  # Token expired

        # Mark as used
        self.repository.mark_invitation_used(token_hash)

        return invitation.technician_id

    def cleanup_expired(self) -> int:
        """
        Remove expired invitations (optional cleanup job).

        Returns:
            Number of expired invitations removed

        Note: DynamoDB TTL handles this automatically, but this method
        can be used for manual cleanup if needed.
        """
        # Implementation deferred (DynamoDB TTL handles auto-cleanup)
        return 0
