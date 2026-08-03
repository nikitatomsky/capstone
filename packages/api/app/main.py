"""Main FastAPI application for Field Intake Service."""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import MissingMessageError, MissingTextError, WebhookError
from app.models.telegram import TelegramUpdate
from app.services.session_service import SessionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_LOG_MESSAGE_LENGTH = 50  # Characters to show in logs

app = FastAPI(title="Field Intake Service")

# Create singleton SessionService instance
session_service = SessionService()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convert Pydantic validation errors (422) to Bad Request (400).

    This ensures the API returns 400 for invalid payloads instead of 422.
    """
    logger.error(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


@app.exception_handler(MissingMessageError)
async def missing_message_handler(request: Request, exc: MissingMessageError):
    """
    Handle updates that have no message field.

    Returns 400 Bad Request with clear error message.
    """
    logger.warning(f"Missing message in update: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(MissingTextError)
async def missing_text_handler(request: Request, exc: MissingTextError):
    """
    Handle messages that have no text content.

    Returns 400 Bad Request with clear error message.
    """
    logger.warning(f"Missing text in message: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(WebhookError)
async def webhook_error_handler(request: Request, exc: WebhookError):
    """
    Handle generic webhook errors.

    Returns 400 Bad Request for webhook-specific errors.
    """
    logger.error(f"Webhook error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def _truncate_for_log(text: str | None, max_length: int = MAX_LOG_MESSAGE_LENGTH) -> str:
    """
    Safely truncate message text for logging.

    Args:
        text: Message text to truncate
        max_length: Maximum characters to include

    Returns:
        Truncated text with ellipsis if cut off, or "No text" if None
    """
    if not text:
        return "No text"
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."


@app.post("/webhook")
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
            "status": "received",
            "chat_id": chat_id,
            "message_count": history_length,
            "received_text": message_text,
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
