"""Repository for Telegram invitation persistence."""
from datetime import UTC, datetime

from app.models.telegram_invitation import TelegramInvitation


class TelegramInvitationRepository:
    """In-memory repository for Telegram invitations (test/dev)."""

    def __init__(self, table_name: str = "telegram-invitations"):
        """
        Initialize repository.

        Args:
            table_name: DynamoDB table name (for future AWS integration)
        """
        self.table_name = table_name
        self._invitations: dict[str, TelegramInvitation] = {}

    def create_invitation(self, invitation: TelegramInvitation) -> None:
        """
        Create new invitation.

        Args:
            invitation: Invitation to create
        """
        self._invitations[invitation.token_hash] = invitation

    def get_invitation_by_hash(self, token_hash: str) -> TelegramInvitation | None:
        """
        Get invitation by token hash.

        Args:
            token_hash: SHA-256 hash of invitation token

        Returns:
            Invitation if found, None otherwise
        """
        return self._invitations.get(token_hash)

    def mark_invitation_used(self, token_hash: str) -> bool:
        """
        Mark invitation as used.

        Args:
            token_hash: SHA-256 hash of invitation token

        Returns:
            True if invitation was marked, False if not found
        """
        invitation = self._invitations.get(token_hash)
        if not invitation:
            return False

        # Update used_at timestamp
        invitation.used_at = datetime.now(UTC)
        self._invitations[token_hash] = invitation
        return True
