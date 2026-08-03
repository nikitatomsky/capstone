"""Main FastAPI application for Field Intake Service."""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models.telegram import TelegramUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Field Intake Service")


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(update: TelegramUpdate):
    """
    Receive and process incoming Telegram webhook updates.

    Args:
        update: TelegramUpdate payload from Telegram Bot API

    Returns:
        dict: Acknowledgment response with extracted data

    Raises:
        HTTPException: 400 if payload is invalid or missing required fields
    """
    try:
        # Log incoming update
        logger.info(f"Received update {update.update_id}")

        # Check if update contains a message
        if not update.message:
            logger.warning(f"Update {update.update_id} has no message")
            raise HTTPException(
                status_code=400, detail="Update must contain a message field"
            )

        # Extract message text and chat_id
        message_text = update.message.text
        chat_id = update.message.chat.id

        logger.info(
            f"Processing message from chat {chat_id}: "
            f"{message_text[:50] if message_text else 'No text'}"
        )

        # Return success response with extracted data
        return {
            "message": "Message received",
            "received_text": message_text,
            "chat_id": chat_id,
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
