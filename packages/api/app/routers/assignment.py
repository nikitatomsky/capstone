"""
Assignment REST API router.

Provides endpoints for managing assignments:
- POST /api/assignments - Create new assignment
- GET /api/assignments - List all assignments (with optional status filter)
- GET /api/assignments/{id} - Get assignment by ID

Note (Issue #30): Technician endpoints moved to dedicated technician router
(see app.routers.technician)
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.assignment import Assignment, AssignmentCreate
from app.repositories.assignment_repository import (
    AssignmentRepository,
    FakeAssignmentRepository,
)
from app.services.sse_manager import sse_manager

router = APIRouter(tags=["assignments"])
logger = logging.getLogger(__name__)

# Dependency injection for repository
# Using in-memory repository for local development
# Production should use DynamoDBAssignmentRepository
_repository_instance: AssignmentRepository | None = None

# Telegram client for sending notifications
telegram_client = None


def init_dependencies(telegram_cl):
    """Initialize router dependencies (called from main.py)."""
    global telegram_client
    telegram_client = telegram_cl


def get_assignment_repo() -> AssignmentRepository:
    """Dependency that provides assignment repository."""
    global _repository_instance
    if _repository_instance is None:
        # Use in-memory repository for local development
        repo = FakeAssignmentRepository()

        # Add sample technicians for testing (Issue #30: using new model with UUID)
        from app.models.technician import TechnicianCreate
        from app.routers.technician import get_technician_repo

        tech_repo = get_technician_repo()

        sample_tech_1 = tech_repo.create_technician(TechnicianCreate(
            name="John Smith",
            phone_number="+1234567890",
            chat_id=123456789,
            email="nikita.tomsky@gmail.com"
        ))
        tech_repo.create_technician(TechnicianCreate(
            name="Jane Doe",
            phone_number="+1987654321",
            chat_id=987654321
        ))

        # Add sample assignments for testing (Issue #30: using technician_id)
        sample_assignment_1 = Assignment(
            assignment_id="assign-001",
            technician_id=sample_tech_1.technician_id,
            technician_name="John Smith",
            title="Delivering Coca-Cola to Downtown Office",
            description=(
                "People are thirsty. "
                "Put the Coca-Cola bottles in the fridge and make sure they are cold. "
            ),
            priority="high",
            status="assigned",
            created_at=datetime.now(UTC),
            assigned_at=datetime.now(UTC),
            completed_at=None,
            intake_record_id=None
        )
        repo.create_assignment(sample_assignment_1)

        _repository_instance = repo
    return _repository_instance


def get_technician_repo():
    """Dependency that provides technician repository."""
    from app.routers.technician import get_technician_repo as get_tech_repo
    return get_tech_repo()


@router.post("/api/assignments", status_code=status.HTTP_201_CREATED, response_model=Assignment)
async def create_assignment(
    assignment_data: AssignmentCreate,
    repo: AssignmentRepository = Depends(get_assignment_repo),
    tech_repo = Depends(get_technician_repo)
) -> Assignment:
    """
    Create a new assignment and notify the technician via Telegram.

    Args:
        assignment_data: Assignment creation data (technician_id, title, description, priority)
        repo: Assignment repository (injected)
        tech_repo: Technician repository (injected) - for looking up technician details

    Returns:
        Created assignment with generated assignment_id and timestamps

    Note (Issue #30):
        - Uses technician_id (UUID) to identify the technician
        - Looks up technician name and chat_id from TechnicianRepository
        - Sends Telegram notification if technician has chat_id configured
    """
    # Look up technician to get name and chat_id
    technician = tech_repo.get_technician(assignment_data.technician_id)
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician {assignment_data.technician_id} not found"
        )

    # Convert create model to full Assignment model
    assignment = Assignment(
        technician_id=assignment_data.technician_id,
        technician_name=technician.name,
        title=assignment_data.title,
        description=assignment_data.description,
        priority=assignment_data.priority
    )

    created_assignment = repo.create_assignment(assignment)

    # Send Telegram notification to technician (Step 2-2) - only if they have chat_id configured
    if telegram_client and technician.chat_id:
        notification_message = (
            f"🔔 **New Assignment**\n\n"
            f"**Title**: {created_assignment.title}\n"
            f"**Description**: {created_assignment.description}\n"
            f"**Priority**: {created_assignment.priority}\n\n"
            f"Please respond when you start working on this task."
        )
        try:
            await telegram_client.send_message(
                technician.chat_id,
                notification_message
            )
            logger.info(
                f"Sent assignment notification to chat_id={technician.chat_id} "
                f"for assignment_id={created_assignment.assignment_id}"
            )
        except Exception as e:
            logger.error(
                f"Failed to send Telegram notification for assignment "
                f"{created_assignment.assignment_id}: {e}"
            )
            # Don't fail the request if notification fails
    elif not technician.chat_id:
        logger.info(
            f"Technician {technician.technician_id} has no chat_id configured - "
            f"skipping Telegram notification"
        )
    else:
        logger.warning("Telegram client not available - notification not sent")

    # Broadcast assignment creation event via SSE (Step 3-0)
    await sse_manager.broadcast(
        "assignment_update",
        {
            "assignment_id": created_assignment.assignment_id,
            "status": created_assignment.status,
            "technician_name": created_assignment.technician_name,
            "title": created_assignment.title,
            "priority": created_assignment.priority,
        }
    )

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


# NOTE (Issue #30): Technician endpoints moved to dedicated technician router
# Old endpoints removed:
# - POST /api/technicians (now in app.routers.technician)
# - GET /api/technicians (now in app.routers.technician)
