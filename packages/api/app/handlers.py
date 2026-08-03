"""FastAPI exception handlers."""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import MissingMessageError, MissingTextError, WebhookError

logger = logging.getLogger(__name__)


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
