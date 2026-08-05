"""
Technician Management API

Dedicated router for technician CRUD operations (Issue #30).

Endpoints:
- POST /api/technicians - Register new technician (with auto-generated UUID)
- GET /api/technicians - List all technicians
- GET /api/technicians/{technician_id} - Get technician by UUID
- DELETE /api/technicians/{technician_id} - Delete technician
- POST /api/technicians/{technician_id}/telegram-invitation - Send Telegram invitation (Issue #37)

Issue #30: Separated from assignment router for cleaner separation of concerns.
Uses technician_id (UUID) as primary identifier instead of chat_id.

Issue #37: Added Telegram invitation endpoint with SMS integration.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.technician import Technician, TechnicianCreate
from app.repositories.technician_repository import TechnicianRepository
from app.services.sms_service import SMSService
from app.services.telegram_invitation_service import TelegramInvitationService

router = APIRouter(prefix="/api/technicians", tags=["technicians"])
logger = logging.getLogger(__name__)

# Dependency injection for repository
# Using in-memory repository for local development
# Production should use DynamoDBTechnicianRepository
_technician_repository: TechnicianRepository | None = None
_invitation_service: TelegramInvitationService | None = None
_sms_service: SMSService | None = None
_email_service = None  # Type: SESEmailService or FakeEmailService


def get_technician_repo() -> TechnicianRepository:
    """Dependency injection for TechnicianRepository."""
    global _technician_repository

    if _technician_repository is None:
        # Use in-memory repository for local development
        from app.repositories.technician_repository import FakeTechnicianRepository
        _technician_repository = FakeTechnicianRepository()
        logger.info("Initialized FakeTechnicianRepository for local development")

    return _technician_repository


def set_invitation_service(service: TelegramInvitationService) -> None:
    """
    Set the shared invitation service instance (called from main.py).
    
    Args:
        service: Shared TelegramInvitationService instance
    """
    global _invitation_service
    _invitation_service = service


def get_invitation_service() -> TelegramInvitationService:
    """Dependency injection for invitation service (Issue #37)."""
    global _invitation_service
    if _invitation_service is None:
        # This should not happen if main.py properly initialized
        raise RuntimeError(
            "Invitation service not initialized. "
            "Call set_invitation_service() from main.py first."
        )
    return _invitation_service


def get_sms_service() -> SMSService:
    """Dependency injection for SMS service (Issue #37)."""
    global _sms_service
    if _sms_service is None:
        # Use fake service for local dev, SNS for production
        if os.getenv("USE_AWS_SNS", "false").lower() == "true":
            from app.services.sns_sms_service import SNSSMSService
            _sms_service = SNSSMSService()
            logger.info("Initialized SNSSMSService")
        else:
            from app.services.sms_service import FakeSMSService
            _sms_service = FakeSMSService()
            logger.info("Initialized FakeSMSService for local development")

    return _sms_service


def get_email_service():
    """Dependency injection for Email service (Issue #39)."""
    global _email_service
    if _email_service is None:
        # Use fake service for local dev, SES for production
        if os.getenv("USE_AWS_SES", "false").lower() == "true":
            from app.services.ses_email_service import SESEmailService
            _email_service = SESEmailService()
            logger.info("Initialized SESEmailService")
        else:
            from app.services.fake_email_service import FakeEmailService
            _email_service = FakeEmailService()
            logger.info("Initialized FakeEmailService for local development")

    return _email_service


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


@router.post(
    "/{technician_id}/telegram-invitation",
    status_code=status.HTTP_200_OK
)
async def create_telegram_invitation(
    technician_id: str,
    delivery_method: str = "email",  # Issue #39: Support multiple delivery methods (defaults to email with SES)
    repo: TechnicianRepository = Depends(get_technician_repo),
    invitation_service: TelegramInvitationService = Depends(get_invitation_service),
    sms_service: SMSService = Depends(get_sms_service),
    email_service=Depends(get_email_service),
):
    """
    Create Telegram invitation and deliver via specified method (Issue #37, #39).

    Args:
        technician_id: UUID of technician
        delivery_method: Delivery method ("sms" or "email", defaults to "email")
        repo: Technician repository (injected)
        invitation_service: Invitation service (injected)
        sms_service: SMS service (injected)
        email_service: Email service (injected)

    Returns:
        Invitation details with expiration and delivery information

    Raises:
        404: Technician not found
        400: Invalid delivery method or missing required field (phone/email)
    
    Note:
        - Email delivery uses AWS SES (production) or logs only (local dev)
        - SMS delivery uses AWS SNS (production) or FakeSMSService (local dev)
    """
    from app.services.invitation_delivery_service import (
        get_invitation_delivery_service,
    )

    # Get technician
    technician = repo.get_technician(technician_id)
    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technician {technician_id} not found"
        )

    # Get appropriate delivery service
    try:
        delivery_service = get_invitation_delivery_service(
            method=delivery_method,
            invitation_service=invitation_service,
            sms_service=sms_service,
            email_service=email_service,
        )
    except ValueError as e:
        logger.error(f"Invalid delivery method '{delivery_method}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported delivery method: {delivery_method}"
        ) from e

    # Deliver invitation
    result = await delivery_service.deliver(technician)

    # If delivery validation failed (no phone/email), return 400
    if not result.success:
        logger.warning(
            f"Delivery failed for {technician_id}: {result.error}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )

    # Return success with delivery details
    return {
        "success": result.success,
        "delivery_method": result.delivery_method,
        "destination": result.destination,
        "invitation_link": result.invitation_link,
        "expires_at": result.expires_at.isoformat() if result.expires_at else None,
        "delivery_attempted": result.delivery_attempted,
        "delivery_succeeded": result.delivery_succeeded,
    }
