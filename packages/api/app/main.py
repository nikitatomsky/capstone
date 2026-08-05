"""Main FastAPI application for Field Intake Service."""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
# Must be called before importing app modules that depend on env vars
load_dotenv()

# noqa: E402 - imports after load_dotenv() to ensure env vars are available
from app import handlers  # noqa: E402
from app.constants import MAX_LOG_MESSAGE_LENGTH  # noqa: E402
from app.exceptions import (  # noqa: E402
    MissingMessageError,
    MissingTextError,
    WebhookError,
)
from app.repositories.telegram_invitation_repository import (  # noqa: E402
    TelegramInvitationRepository,
)
from app.routers import assignment, health, sse, technician, webhook  # noqa: E402
from app.services.extraction_service import ExtractionService  # noqa: E402
from app.services.intake_helpers import (  # noqa: E402
    generate_followup_question,
    get_missing_fields,
)
from app.services.llm_providers import AnthropicProvider  # noqa: E402
from app.services.session_service import SessionService  # noqa: E402
from app.services.telegram_client import TelegramClient  # noqa: E402
from app.services.telegram_invitation_service import TelegramInvitationService  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Field Intake Service")

# CORS middleware for SPA integration
# Allows cross-origin requests from React frontend
# Local dev: localhost:5173 (Vite default), localhost:3000 (alternative React port)
# Production: CloudFront domain (update when deployed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Initialize Telegram invitation service (Step 4-2)
invitation_repo = TelegramInvitationRepository()
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "field_intake_bot")
TELEGRAM_INVITATION_TTL = int(os.getenv("TELEGRAM_INVITATION_TTL_SECONDS", "3600"))
invitation_service = TelegramInvitationService(
    repository=invitation_repo,
    bot_username=TELEGRAM_BOT_USERNAME,
    ttl_seconds=TELEGRAM_INVITATION_TTL,
)
logger.info(f"Invitation service initialized (TTL: {TELEGRAM_INVITATION_TTL}s)")


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
# Import after app initialization to avoid circular dependency
from app.routers.assignment import (  # noqa: E402
    get_assignment_repo,
)
from app.routers.technician import (  # noqa: E402
    get_technician_repo,
)

# Initialize repositories (ensures they're not None for webhook)
assignment_repo = get_assignment_repo()
technician_repo = get_technician_repo()

# Inject shared invitation service into technician router (Issue #39)
# This ensures both webhook and technician router use the SAME repository instance
from app.routers.technician import set_invitation_service  # noqa: E402

set_invitation_service(invitation_service)

webhook.init_dependencies(
    session_service,
    extraction_service,
    telegram_client,
    _truncate_for_log,
    get_missing_fields,
    generate_followup_question,
    assignment_repo,  # Pass the assignment repository
    technician_repo,  # Pass the initialized technician repository (Step 2-3)
    invitation_service,  # NEW: Pass the invitation service (Step 4-2)
)

# Initialize health router with dependencies
health.init_dependencies(session_service)

# Initialize assignment router with dependencies
assignment.init_dependencies(telegram_client)

# Include routers
# IMPORTANT: Register SSE router before assignment router
# to prevent /api/assignments/stream from matching /api/assignments/{assignment_id}
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(sse.router)  # Register BEFORE assignment router
app.include_router(technician.router)  # Issue #30: Dedicated technician router
app.include_router(assignment.router)
