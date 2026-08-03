"""Session management service for tracking conversation state."""

import logging
from datetime import UTC, datetime

from app.models.intake import IntakeRecord

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing conversation sessions.

    Tracks conversation state for each field employee by chat_id.
    Stores partial intake records, conversation history, and completion status.
    """

    def __init__(self):
        """Initialize the session service with empty in-memory storage."""
        self._sessions: dict[int, IntakeRecord] = {}
        logger.info("SessionService initialized")

    def get_or_create_session(self, chat_id: int) -> IntakeRecord:
        """
        Get an existing session or create a new one.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            IntakeRecord for the session
        """
        if chat_id not in self._sessions:
            logger.info(f"Creating new session for chat_id={chat_id}")
            self._sessions[chat_id] = IntakeRecord()
        else:
            logger.debug(f"Retrieved existing session for chat_id={chat_id}")

        return self._sessions[chat_id]

    def get_session(self, chat_id: int) -> IntakeRecord | None:
        """
        Get an existing session without creating a new one.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            IntakeRecord if session exists, None otherwise
        """
        session = self._sessions.get(chat_id)
        if session is None:
            logger.debug(f"No session found for chat_id={chat_id}")
        return session

    def update_intake_field(self, chat_id: int, field: str, value: str) -> None:
        """
        Update a specific field in the intake record.

        If the session doesn't exist, it will be created first.

        Args:
            chat_id: Telegram chat identifier
            field: Field name to update (e.g., 'employee_name', 'location')
            value: New value for the field
        """
        session = self.get_or_create_session(chat_id)

        if hasattr(session, field):
            setattr(session, field, value)
            logger.info(f"Updated field '{field}' for chat_id={chat_id} to '{value}'")
        else:
            logger.warning(
                f"Attempted to update invalid field '{field}' for chat_id={chat_id}"
            )

    def is_complete(self, chat_id: int) -> bool:
        """
        Check if the intake record for a session is complete.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            True if the record has all required fields, False otherwise
        """
        session = self.get_session(chat_id)
        if session is None:
            logger.debug(
                f"Session not found for chat_id={chat_id}, returning incomplete"
            )
            return False

        complete = session.is_complete()
        logger.debug(f"Session for chat_id={chat_id} is_complete={complete}")
        return complete

    def list_active_sessions(self) -> list[int]:
        """
        Get a list of all active session chat IDs.

        Returns:
            List of chat_id integers for active sessions
        """
        active_sessions = list(self._sessions.keys())
        logger.debug(f"Active sessions: {len(active_sessions)} total")
        return active_sessions

    def complete_session(self, chat_id: int) -> IntakeRecord | None:
        """
        Mark a session as complete and remove it from active sessions.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            The completed IntakeRecord, or None if session doesn't exist
        """
        session = self.get_session(chat_id)
        if session is None:
            logger.warning(
                f"Attempted to complete non-existent session for chat_id={chat_id}"
            )
            return None

        # Add timestamp if not already set
        if session.timestamp is None:
            session.timestamp = datetime.now(UTC)

        # Remove from active sessions
        completed_record = self._sessions.pop(chat_id)
        logger.info(
            f"Completed and removed session for chat_id={chat_id}, "
            f"employee={completed_record.employee_name}"
        )

        return completed_record
