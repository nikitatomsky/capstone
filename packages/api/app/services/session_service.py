"""Session management service for tracking conversation state."""

import logging
from datetime import UTC, datetime
from typing import Any

from app.constants import MAX_CONVERSATION_HISTORY
from app.models.intake import IntakeRecord

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing conversation sessions.

    Tracks conversation state for each field employee by chat_id.
    Stores partial intake records, conversation history, and completion status.

    Session structure:
        {
            "chat_id": int,
            "intake_record": IntakeRecord,
            "conversation_history": list[dict],
            "created_at": datetime
        }
    """

    def __init__(self):
        """Initialize the session service with empty in-memory storage."""
        self._sessions: dict[int, dict[str, Any]] = {}
        logger.debug("SessionService initialized")

    def _validate_chat_id(self, chat_id: int) -> None:
        """
        Validate that chat_id is a positive integer.

        Args:
            chat_id: Telegram chat identifier

        Raises:
            ValueError: If chat_id is not positive
        """
        if chat_id <= 0:
            raise ValueError(f"Invalid chat_id: {chat_id} (must be positive)")

    def get_or_create_session(self, chat_id: int) -> dict[str, Any]:
        """
        Get an existing session or create a new one.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            Session dict containing intake_record and conversation_history

        Raises:
            ValueError: If chat_id is not positive
        """
        self._validate_chat_id(chat_id)
        if chat_id not in self._sessions:
            logger.info(f"Creating new session for chat_id={chat_id}")
            self._sessions[chat_id] = {
                "chat_id": chat_id,
                "intake_record": IntakeRecord(),
                "conversation_history": [],
                "created_at": datetime.now(UTC),
            }
        else:
            logger.debug(f"Retrieved existing session for chat_id={chat_id}")

        return self._sessions[chat_id]

    def get_session(self, chat_id: int) -> dict[str, Any] | None:
        """
        Get an existing session without creating a new one.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            Session dict if session exists, None otherwise

        Raises:
            ValueError: If chat_id is not positive
        """
        self._validate_chat_id(chat_id)
        session = self._sessions.get(chat_id)
        if session is None:
            logger.debug(f"No session found for chat_id={chat_id}")
        return session

    def add_message(self, chat_id: int, message_text: str) -> None:
        """
        Log a message to the conversation history.

        If the session doesn't exist, it will be created first.
        Automatically trims history if it exceeds MAX_CONVERSATION_HISTORY.

        Args:
            chat_id: Telegram chat identifier
            message_text: The message text to log

        Raises:
            ValueError: If chat_id is not positive
        """
        session = self.get_or_create_session(chat_id)
        history = session["conversation_history"]

        history.append(
            {
                "message": message_text,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Trim old messages if exceeding limit
        if len(history) > MAX_CONVERSATION_HISTORY:
            removed = len(history) - MAX_CONVERSATION_HISTORY
            session["conversation_history"] = history[-MAX_CONVERSATION_HISTORY:]
            logger.warning(
                f"Trimmed {removed} old messages for chat_id={chat_id} "
                f"(limit={MAX_CONVERSATION_HISTORY})"
            )

        logger.debug(
            f"Added message to conversation history for chat_id={chat_id}, "
            f"total messages={len(session['conversation_history'])}"
        )

    def update_intake_field(self, chat_id: int, field: str, value: str) -> None:
        """
        Update a specific field in the intake record with Pydantic validation.

        If the session doesn't exist, it will be created first.

        Args:
            chat_id: Telegram chat identifier
            field: Field name to update (e.g., 'employee_name', 'location')
            value: New value for the field

        Raises:
            ValueError: If chat_id is not positive, field name is invalid,
                       or value fails validation
        """
        from pydantic import ValidationError

        session = self.get_or_create_session(chat_id)
        intake_record = session["intake_record"]

        # Validate that the field exists on the model
        if field not in IntakeRecord.model_fields:
            logger.warning(
                f"Attempted to update invalid field '{field}' for chat_id={chat_id}"
            )
            raise ValueError(f"Unknown field '{field}'")

        # Use Pydantic's model validation to ensure data integrity
        try:
            updated_record = intake_record.model_copy(update={field: value})
            session["intake_record"] = updated_record
            logger.info(f"Updated field '{field}' for chat_id={chat_id}")
        except ValidationError as e:
            logger.error(
                f"Validation failed for field '{field}' with value '{value}': {e}"
            )
            raise ValueError(f"Invalid value for field '{field}'") from e

    def is_complete(self, chat_id: int) -> bool:
        """
        Check if the intake record for a session is complete.

        Args:
            chat_id: Telegram chat identifier

        Returns:
            True if the record has all required fields, False otherwise

        Raises:
            ValueError: If chat_id is not positive
        """
        session = self.get_session(chat_id)
        if session is None:
            logger.debug(
                f"Session not found for chat_id={chat_id}, returning incomplete"
            )
            return False

        complete = session["intake_record"].is_complete()
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

        Raises:
            ValueError: If chat_id is not positive
        """
        session = self.get_session(chat_id)
        if session is None:
            logger.warning(
                f"Attempted to complete non-existent session for chat_id={chat_id}"
            )
            return None

        intake_record = session["intake_record"]

        # Add timestamp if not already set
        if intake_record.timestamp is None:
            intake_record.timestamp = datetime.now(UTC)

        # Remove from active sessions
        completed_session = self._sessions.pop(chat_id)
        completed_record = completed_session["intake_record"]

        logger.info(
            f"Completed and removed session for chat_id={chat_id}, "
            f"location={completed_record.location}"
        )

        return completed_record
