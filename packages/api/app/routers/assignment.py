"""
Assignment REST API router.

Provides endpoints for managing assignments and technicians:
- POST /api/assignments - Create new assignment
- GET /api/assignments - List all assignments (with optional status filter)
- GET /api/assignments/{id} - Get assignment by ID
- POST /api/technicians - Register new technician
- GET /api/technicians - List all technicians
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.assignment import Assignment, AssignmentCreate
from app.models.technician import Technician, TechnicianCreate
from app.repositories.assignment_repository import (
    AssignmentRepository,
    FakeAssignmentRepository,
)

router = APIRouter(tags=["assignments"])
logger = logging.getLogger(__name__)

# Dependency injection for repository
# In production, this would use DynamoDBAssignmentRepository
# For now, use Fake for testing and local development
_repository_instance = FakeAssignmentRepository()

# Telegram client for sending notifications
telegram_client = None


def init_dependencies(telegram_cl):
    """Initialize router dependencies (called from main.py)."""
    global telegram_client
    telegram_client = telegram_cl


def get_assignment_repo() -> AssignmentRepository:
    """Dependency that provides assignment repository."""
    return _repository_instance


@router.post("/api/assignments", status_code=status.HTTP_201_CREATED, response_model=Assignment)
async def create_assignment(
    assignment_data: AssignmentCreate,
    repo: AssignmentRepository = Depends(get_assignment_repo)
) -> Assignment:
    """
    Create a new assignment and notify the technician via Telegram.

    Args:
        assignment_data: Assignment creation data (technician, title, description, priority)
        repo: Assignment repository (injected)

    Returns:
        Created assignment with generated assignment_id and timestamps
    """
    # Convert create model to full Assignment model
    assignment = Assignment(
        technician_chat_id=assignment_data.technician_chat_id,
        technician_name=assignment_data.technician_name,
        title=assignment_data.title,
        description=assignment_data.description,
        priority=assignment_data.priority
    )

    created_assignment = repo.create_assignment(assignment)
    
    # Send Telegram notification to technician (Step 2-2)
    if telegram_client:
        notification_message = (
            f"🔔 **New Assignment**\n\n"
            f"**Title**: {created_assignment.title}\n"
            f"**Description**: {created_assignment.description}\n"
            f"**Priority**: {created_assignment.priority}\n\n"
            f"Please respond when you start working on this task."
        )
        try:
            await telegram_client.send_message(
                created_assignment.technician_chat_id,
                notification_message
            )
            logger.info(
                f"Sent assignment notification to chat_id={created_assignment.technician_chat_id} "
                f"for assignment_id={created_assignment.assignment_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to send Telegram notification for assignment {created_assignment.assignment_id}: {e}"
            )
            # Don't fail the request if notification fails
    else:
        logger.warning("Telegram client not available - notification not sent")
    
    return created_assignment


@router.get("/api/assignments", response_model=list[Assignment])
async def list_assignments(
    status: str | None = None,
    repo: AssignmentRepository = Depends(get_assignment_repo)
) -> list[Assignment]:
    """
    List all assignments, optionally filtered by status.

    Args:
        status: Optional status filter (pending, assigned, in_progress, completed, cancelled)
        repo: Assignment repository (injected)

    Returns:
        List of assignments matching the filter criteria
    """
    assignments = repo.list_assignments(status=status)
    return assignments


@router.get("/api/assignments/{assignment_id}", response_model=Assignment)
async def get_assignment(
    assignment_id: str,
    repo: AssignmentRepository = Depends(get_assignment_repo)
) -> Assignment:
    """
    Get assignment by ID.

    Args:
        assignment_id: UUID of the assignment to retrieve
        repo: Assignment repository (injected)

    Returns:
        Assignment details

    Raises:
        HTTPException: 404 if assignment not found
    """
    assignment = repo.get_assignment(assignment_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assignment with id '{assignment_id}' not found"
        )

    return assignment


@router.post("/api/technicians", status_code=status.HTTP_201_CREATED, response_model=Technician)
async def register_technician(
    technician_data: TechnicianCreate,
    repo: AssignmentRepository = Depends(get_assignment_repo)
) -> Technician:
    """
    Register a new technician.

    Args:
        technician_data: Technician registration data (chat_id, name, phone_number)
        repo: Assignment repository (injected)

    Returns:
        Registered technician with generated registered_at timestamp

    Note:
        To get the technician's chat_id, have them message the bot first.
        The phone_number should match their Telegram account for verification.
    """
    # Convert create model to full Technician model
    technician = Technician(
        chat_id=technician_data.chat_id,
        name=technician_data.name,
        phone_number=technician_data.phone_number
    )

    created_technician = repo.create_technician(technician)
    return created_technician


@router.get("/api/technicians", response_model=list[Technician])
async def list_technicians(
    repo: AssignmentRepository = Depends(get_assignment_repo)
) -> list[Technician]:
    """
    List all registered technicians.

    Args:
        repo: Assignment repository (injected)

    Returns:
        List of all registered technicians
    """
    technicians = repo.list_technicians()
    return technicians
