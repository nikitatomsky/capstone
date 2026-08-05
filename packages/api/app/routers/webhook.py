"""Webhook endpoint router."""

import logging

from fastapi import APIRouter, HTTPException

from app.exceptions import MissingMessageError, MissingTextError, WebhookError
from app.models.telegram import TelegramUpdate
from app.services.sse_manager import sse_manager

router = APIRouter(tags=["webhook"])
logger = logging.getLogger(__name__)

# Placeholders for dependencies - will be injected from main.py
session_service = None
extraction_service = None
telegram_client = None
assignment_repository = None
technician_repository = None
invitation_service = None  # NEW: For Telegram invitation token validation

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
    assignment_repo=None,
    technician_repo=None,
    invitation_svc=None,  # NEW: Invitation service
):
    """
    Initialize router dependencies.

    This is called from main.py to inject services and helper functions.
    """
    global session_service, extraction_service, telegram_client
    global assignment_repository, technician_repository
    global _truncate_for_log, get_missing_fields, generate_followup_question
    global invitation_service  # NEW

    session_service = session_svc
    extraction_service = extraction_svc
    telegram_client = telegram_cl
    assignment_repository = assignment_repo
    technician_repository = technician_repo
    invitation_service = invitation_svc  # NEW
    _truncate_for_log = truncate_fn
    get_missing_fields = get_missing_fn
    generate_followup_question = generate_followup_fn


def _link_session_to_assignment(chat_id: int, session: dict) -> None:
    """
    Link session to active assignment and update assignment status.

    Args:
        chat_id: Telegram chat ID
        session: Session dictionary containing intake record
    """
    logger.info(
        f"Attempting to link session for chat_id={chat_id}: "
        f"assignment_repo={assignment_repository is not None}, "
        f"technician_repo={technician_repository is not None}, "
        f"current_assignment_id={session['intake_record'].assignment_id}"
    )

    if (not assignment_repository or not technician_repository
            or session["intake_record"].assignment_id):
        logger.info(
            f"Early return from _link_session_to_assignment: "
            f"repos_available="
            f"{assignment_repository is not None and technician_repository is not None}, "
            f"already_linked={session['intake_record'].assignment_id is not None}"
        )
        return

    # Look up technician by chat_id to get technician_id
    technician = technician_repository.get_technician_by_chat_id(chat_id)
    logger.info(f"Looked up technician for chat_id={chat_id}: {technician}")
    if not technician:
        logger.warning(f"No technician found for chat_id={chat_id}")
        return

    # Find active assignment for this technician
    logger.info(f"Looking up active assignment for technician_id={technician.technician_id}")
    active_assignment = (
        assignment_repository.get_active_assignment_by_technician_id(technician.technician_id)
    )
    logger.info(f"Active assignment lookup result: {active_assignment}")
    if not active_assignment:
        logger.warning(f"No active assignment found for technician {technician.technician_id}")
        return

    # Link intake record to assignment
    session_service.update_intake_field(
        chat_id, "assignment_id", active_assignment.assignment_id
    )
    logger.info(
        f"Linked session to assignment {active_assignment.assignment_id}"
    )

    # Update assignment status to "in_progress" if technician is starting work
    if active_assignment.status in ["pending", "assigned"]:
        assignment_repository.update_assignment_status(
            active_assignment.assignment_id, "in_progress"
        )
        logger.info(
            f"Updated assignment {active_assignment.assignment_id} "
            f"status to in_progress"
        )


def _process_extracted_data(chat_id: int, extracted_data: dict) -> None:
    """
    Update intake record fields with extracted data.

    Args:
        chat_id: Telegram chat ID
        extracted_data: Dictionary of extracted field names and values
    """
    session = session_service.get_session(chat_id)
    if not session:
        return

    for field_name, value in extracted_data.items():
        # Check if field exists on the intake record instance
        if hasattr(session["intake_record"], field_name):
            session_service.update_intake_field(chat_id, field_name, value)
            logger.debug(f"Updated {field_name}={value} for chat_id={chat_id}")


async def _complete_intake_with_assignment(
    chat_id: int, intake_record
) -> None:
    """
    Complete assignment linked to intake record.

    Args:
        chat_id: Telegram chat ID
        intake_record: Complete IntakeRecord instance
    """
    logger.info(
        f"Attempting to complete assignment: "
        f"assignment_repo={assignment_repository is not None}, "
        f"intake_record.assignment_id={intake_record.assignment_id}"
    )

    if not assignment_repository or not intake_record.assignment_id:
        logger.warning(
            f"Cannot complete assignment: "
            f"repo_available={assignment_repository is not None}, "
            f"assignment_id={intake_record.assignment_id}"
        )
        return

    from datetime import UTC, datetime

    # Generate intake_record_id (in future, this will come from DB persistence)
    intake_record_id = (
        f"intake_{chat_id}_{int(datetime.now(UTC).timestamp())}"
    )

    # Complete the assignment with intake record link
    updated_assignment = assignment_repository.complete_assignment(
        intake_record.assignment_id,
        intake_record_id,
    )
    if updated_assignment:
        logger.info(
            f"Completed assignment {intake_record.assignment_id} "
            f"with intake_record_id={intake_record_id}"
        )

        # Broadcast assignment completion event via SSE
        await sse_manager.broadcast(
            "assignment_update",
            {
                "assignment_id": updated_assignment.assignment_id,
                "status": updated_assignment.status,
                "technician_name": updated_assignment.technician_name,
                "title": updated_assignment.title,
                "priority": updated_assignment.priority,
                "intake_record_id": updated_assignment.intake_record_id,
                "completed_at": (
                    updated_assignment.completed_at.isoformat()
                    if updated_assignment.completed_at else None
                ),
            }
        )
        logger.info(
            f"Broadcasted assignment completion event for {updated_assignment.assignment_id}"
        )
    else:
        logger.error(
            f"Failed to complete assignment {intake_record.assignment_id} in database"
        )


async def _handle_start_command(chat_id: int, message_text: str) -> None:
    """
    Handle /start command with optional invitation token.

    This function processes Telegram /start commands for the invitation flow.
    When a technician taps an invitation deeplink, Telegram sends a /start command
    with the token as a parameter. This function validates the token and links
    the chat_id to the technician's record.

    Args:
        chat_id: Telegram chat ID from the user who sent /start
        message_text: Full message text (e.g., "/start abc123xyz" or just "/start")
    """
    # Extract token from command (if present)
    parts = message_text.split(maxsplit=1)

    if len(parts) == 1:
        # Just "/start" without token - send welcome message
        await telegram_client.send_message(
            chat_id,
            "Welcome! If you have an invitation link, please tap it to connect your account."
        )
        return

    token = parts[1]

    # Validate invitation service is available
    if not invitation_service or not technician_repository:
        logger.error("Invitation service not configured")
        await telegram_client.send_message(
            chat_id,
            "Service temporarily unavailable. Please try again later."
        )
        return

    # Validate token
    technician_id = invitation_service.validate_token(token)

    if not technician_id:
        # Token invalid, expired, or already used
        await telegram_client.send_message(
            chat_id,
            "This invitation link is invalid, expired, or has already been used. "
            "Please contact your administrator for a new invitation."
        )
        return

    # Link chat_id to technician
    success = technician_repository.update_technician_chat_id(
        technician_id, chat_id
    )

    if not success:
        logger.error(f"Failed to update chat_id for technician {technician_id}")
        await telegram_client.send_message(
            chat_id,
            "Failed to connect your account. Please contact your administrator."
        )
        return

    # Get technician details for personalized message
    technician = technician_repository.get_technician(technician_id)
    name = technician.name if technician else "there"

    # Send success confirmation
    await telegram_client.send_message(
        chat_id,
        f"✅ Hi {name}! Your Telegram account is now connected. "
        f"You'll receive assignment notifications here."
    )

    logger.info(
        f"Successfully linked chat_id {chat_id} to technician {technician_id}"
    )


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

        # NEW: Handle /start command for invitation flow (early return)
        if message_text and message_text.startswith("/start"):
            await _handle_start_command(chat_id, message_text)
            return {"status": "ok", "message": "Start command processed"}

        # Get or create session for this chat
        session = session_service.get_or_create_session(chat_id)

        # Link session to active assignment if available (Step 2-3)
        _link_session_to_assignment(chat_id, session)

        # Log message to conversation history
        session_service.add_message(chat_id, message_text)

        # Extract structured data if extraction service available
        extracted_data = {}
        if extraction_service:
            extracted_data = extraction_service.extract_from_message(message_text)
            logger.info(f"Extracted {len(extracted_data)} fields from message")

            # Update IntakeRecord with extracted data
            _process_extracted_data(chat_id, extracted_data)

        # Check if record is complete
        intake_record = session["intake_record"]
        missing_fields = get_missing_fields(intake_record)

        if not missing_fields:
            # Record is complete
            logger.info(f"Intake record complete for chat_id={chat_id}")

            # Update linked assignment if exists (Step 2-3)
            await _complete_intake_with_assignment(chat_id, intake_record)

            # Complete and remove session to prevent reprocessing
            session_service.complete_session(chat_id)
            logger.info(f"Session closed for chat_id={chat_id}")

            # Note: Manager notifications are intentionally skipped when assignments
            # reach completed state. Assignment status is updated in DynamoDB,
            # and managers can poll the API or use real-time dashboard updates.
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
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception:
        # Catch unexpected errors
        logger.exception("Unexpected error processing webhook")
        raise HTTPException(
            status_code=500, detail="Internal server error processing webhook"
        ) from None
