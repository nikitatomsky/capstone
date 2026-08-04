"""
Technician Management API

Dedicated router for technician CRUD operations (Issue #30).

Endpoints:
- POST /api/technicians - Register new technician (with auto-generated UUID)
- GET /api/technicians - List all technicians
- GET /api/technicians/{technician_id} - Get technician by UUID
- DELETE /api/technicians/{technician_id} - Delete technician

Issue #30: Separated from assignment router for cleaner separation of concerns.
Uses technician_id (UUID) as primary identifier instead of chat_id.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.technician import Technician, TechnicianCreate
from app.repositories.technician_repository import TechnicianRepository

router = APIRouter(prefix="/api/technicians", tags=["technicians"])
logger = logging.getLogger(__name__)

# Dependency injection for repository
# Using in-memory repository for local development
# Production should use DynamoDBTechnicianRepository
_technician_repository: TechnicianRepository | None = None


def get_technician_repo() -> TechnicianRepository:
    """Dependency injection for TechnicianRepository."""
    global _technician_repository

    if _technician_repository is None:
        # Use in-memory repository for local development
        from app.repositories.technician_repository import FakeTechnicianRepository
        _technician_repository = FakeTechnicianRepository()
        logger.info("Initialized FakeTechnicianRepository for local development")

    return _technician_repository


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Technician)
async def create_technician(
    technician_data: TechnicianCreate,
    repo: TechnicianRepository = Depends(get_technician_repo)
) -> Technician:
    """
    Register a new technician with auto-generated UUID.

    Args:
        technician_data: Technician registration data (name, phone_number, optional chat_id)
        repo: Technician repository (injected)

    Returns:
        Created technician with auto-generated technician_id (UUID)

    Note (Issue #30):
        - technician_id (UUID) is auto-generated and serves as primary key
        - chat_id is optional (only needed for Telegram integration)
        - phone_number can be actual phone or UUID placeholder for now
    """
    logger.info(f"Creating technician: {technician_data.name}")
    technician = repo.create_technician(technician_data)
    logger.info(f"Created technician with ID: {technician.technician_id}")
    return technician


@router.get("/", response_model=list[Technician])
async def list_technicians(
    repo: TechnicianRepository = Depends(get_technician_repo)
) -> list[Technician]:
    """
    Get all registered technicians.

    Args:
        repo: Technician repository (injected)

    Returns:
        List of all registered technicians
    """
    logger.info("Listing all technicians")
    technicians = repo.list_technicians()
    logger.info(f"Found {len(technicians)} technicians")
    return technicians


@router.get("/{technician_id}", response_model=Technician)
async def get_technician(
    technician_id: str,
    repo: TechnicianRepository = Depends(get_technician_repo)
) -> Technician:
    """
    Get technician by UUID.

    Args:
        technician_id: UUID of the technician
        repo: Technician repository (injected)

    Returns:
        Technician

    Raises:
        HTTPException: 404 if technician not found
    """
    logger.info(f"Getting technician: {technician_id}")
    technician = repo.get_technician(technician_id)

    if not technician:
        logger.warning(f"Technician not found: {technician_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician {technician_id} not found"
        )

    return technician


@router.delete("/{technician_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technician(
    technician_id: str,
    repo: TechnicianRepository = Depends(get_technician_repo)
):
    """
    Delete a technician.

    Args:
        technician_id: UUID of the technician to delete
        repo: Technician repository (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if technician not found
        HTTPException: 409 if technician has active assignments
    """
    logger.info(f"Deleting technician: {technician_id}")

    try:
        deleted = repo.delete_technician(technician_id)

        if not deleted:
            logger.warning(f"Technician not found: {technician_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technician {technician_id} not found"
            )

        logger.info(f"Successfully deleted technician: {technician_id}")
    except ValueError as e:
        # Has active assignments
        logger.warning(f"Cannot delete technician {technician_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        ) from e
