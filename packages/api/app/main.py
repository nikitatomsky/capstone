"""Main FastAPI application for Field Intake Service."""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

# Load environment variables from .env file
load_dotenv()

from app import handlers
from app.constants import MAX_LOG_MESSAGE_LENGTH
from app.exceptions import MissingMessageError, MissingTextError, WebhookError
from app.routers import assignment, health, webhook
from app.services.extraction_service import ExtractionService
from app.services.intake_helpers import generate_followup_question, get_missing_fields
from app.services.llm_providers import AnthropicProvider
from app.services.session_service import SessionService
from app.services.telegram_client import TelegramClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Field Intake Service")

# Create singleton SessionService instance
session_service = SessionService()

# Initialize Telegram client
telegram_client = TelegramClient()

# Initialize extraction service with LLM provider
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# Only initialize if we have a valid API key (not placeholder or empty)
if ANTHROPIC_API_KEY and not ANTHROPIC_API_KEY.startswith("your-"):
    llm_provider = AnthropicProvider(ANTHROPIC_API_KEY)
    extraction_service = ExtractionService(llm_provider)
    logger.info("Extraction service initialized")
else:
    extraction_service = None
    logger.warning("ANTHROPIC_API_KEY not set - extraction disabled")


# Register exception handlers
app.add_exception_handler(RequestValidationError, handlers.validation_exception_handler)
app.add_exception_handler(MissingMessageError, handlers.missing_message_handler)
app.add_exception_handler(MissingTextError, handlers.missing_text_handler)
app.add_exception_handler(WebhookError, handlers.webhook_error_handler)


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


# Initialize webhook router with dependencies
webhook.init_dependencies(
    session_service,
    extraction_service,
    telegram_client,
    _truncate_for_log,
    get_missing_fields,
    generate_followup_question,
)

# Include routers
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(assignment.router)
