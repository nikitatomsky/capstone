"""Webhook endpoint router."""

import logging

from fastapi import APIRouter, HTTPException

from app.exceptions import MissingMessageError, MissingTextError, WebhookError
from app.models.telegram import TelegramUpdate

router = APIRouter(tags=["webhook"])
logger = logging.getLogger(__name__)

# Placeholders for dependencies - will be injected from main.py
session_service = None
extraction_service = None
telegram_client = None

# Helper functions - will be injected from main.py
_truncate_for_log = None
get_missing_fields = None
generate_followup_question = None


def init_dependencies(
    session_svc,
    extraction_svc,
    telegram_cl,
    truncate_fn,
    get_missing_fn,
    generate_followup_fn,
):
    """
    Initialize router dependencies.
    
    This is called from main.py to inject services and helper functions.
    """
    global session_service, extraction_service, telegram_client
    global _truncate_for_log, get_missing_fields, generate_followup_question
    
    session_service = session_svc
    extraction_service = extraction_svc
    telegram_client = telegram_cl
    _truncate_for_log = truncate_fn
    get_missing_fields = get_missing_fn
    generate_followup_question = generate_followup_fn


@router.post("/webhook")
async def webhook(update: TelegramUpdate):
    """
    Receive and process incoming Telegram webhook updates.

    Args:
        update: TelegramUpdate payload from Telegram Bot API

    Returns:
        dict: Acknowledgment response with session state

    Raises:
        HTTPException: 400 if payload is invalid or missing required fields
    """
    try:
        # Log incoming update
        logger.info(f"Received update {update.update_id}")

        # Check if update contains a message
        if not update.message:
            raise MissingMessageError(
                f"Update {update.update_id} has no message field"
            )

        # Extract message text and chat_id
        message_text = update.message.text
        chat_id = update.message.chat.id

        logger.info(
            f"Processing message from chat {chat_id}: "
            f"{_truncate_for_log(message_text)}"
        )

        # Get or create session for this chat
        session = session_service.get_or_create_session(chat_id)

        # Log message to conversation history
        session_service.add_message(chat_id, message_text)

        # Extract structured data if extraction service available
        extracted_data = {}
        if extraction_service:
            extracted_data = extraction_service.extract_from_message(message_text)
            logger.info(f"Extracted {len(extracted_data)} fields from message")

            # Update IntakeRecord with extracted data
            for field_name, value in extracted_data.items():
                if hasattr(session["intake_record"], field_name):
                    session_service.update_intake_field(chat_id, field_name, value)
                    logger.debug(f"Updated {field_name}={value} for chat_id={chat_id}")

        # Check if record is complete
        intake_record = session["intake_record"]
        missing_fields = get_missing_fields(intake_record)

        if not missing_fields:
            # Record is complete
            logger.info(f"Intake record complete for chat_id={chat_id}")

            # TODO: Persist to database and send notification (Step 1-6)
            response_text = (
                "Thank you! I have all the information I need. "
                "Your service report has been recorded."
            )
        else:
            # Ask follow-up question
            logger.debug(f"Missing fields for chat_id={chat_id}: {missing_fields}")
            response_text = generate_followup_question(missing_fields)

        # Send response via Telegram
        telegram_sent = await telegram_client.send_message(chat_id, response_text)

        # Log session state for debugging
        history_length = len(session["conversation_history"])
        is_complete = session["intake_record"].is_complete()
        logger.debug(
            f"Session state for chat_id={chat_id}: "
            f"history_length={history_length}, "
            f"record_complete={is_complete}"
        )

        # Return acknowledgment with session info
        return {
            "status": "processed",
            "chat_id": chat_id,
            "message_count": history_length,
            "received_text": message_text,
            "fields_extracted": len(extracted_data),
            "record_complete": len(missing_fields) == 0,
            "extraction_enabled": extraction_service is not None,
            "telegram_sent": telegram_sent,
            "message": "Message received",
        }

    except (MissingMessageError, MissingTextError, WebhookError):
        # Re-raise custom webhook exceptions (handled by exception handlers)
        raise
    except ValueError as e:
        # Handle validation errors from SessionService
        logger.error(f"Invalid input: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception:
        # Catch unexpected errors
        logger.exception("Unexpected error processing webhook")
        raise HTTPException(
            status_code=500, detail="Internal server error processing webhook"
        )
