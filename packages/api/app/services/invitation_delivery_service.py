"""
Abstract invitation delivery service for multi-channel invitation delivery (Issue #39).

This module provides an abstraction layer for delivering Telegram bot invitations
through multiple channels (SMS, Email, etc.). It decouples invitation generation
from delivery mechanism, making it easy to add new delivery channels.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.models.technician import Technician
from app.services.sms_service import SMSService
from app.services.telegram_invitation_service import TelegramInvitationService

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    """Result of invitation delivery attempt."""

    success: bool
    technician_id: str
    delivery_method: str
    destination: str | None = None
    invitation_link: str | None = None
    expires_at: datetime | None = None
    error: str | None = None
    delivery_attempted: bool = False
    delivery_succeeded: bool = False


class InvitationDeliveryService(ABC):
    """Abstract base class for invitation delivery services."""

    def __init__(self, invitation_service: TelegramInvitationService):
        """
        Initialize delivery service.

        Args:
            invitation_service: Service for generating invitation tokens
        """
        self.invitation_service = invitation_service

    @abstractmethod
    async def deliver(self, technician: Technician) -> DeliveryResult:
        """
        Generate and deliver invitation to technician.

        Args:
            technician: Technician to receive invitation

        Returns:
            DeliveryResult with success status and details
        """


class SMSInvitationDelivery(InvitationDeliveryService):
    """SMS-based invitation delivery."""

    def __init__(
        self,
        invitation_service: TelegramInvitationService,
        sms_service: SMSService,
    ):
        """
        Initialize SMS delivery service.

        Args:
            invitation_service: Service for generating invitation tokens
            sms_service: SMS service for sending messages
        """
        super().__init__(invitation_service)
        self.sms_service = sms_service

    async def deliver(self, technician: Technician) -> DeliveryResult:
        """
        Generate invitation and deliver via SMS.

        Args:
            technician: Technician to receive invitation

        Returns:
            DeliveryResult with SMS delivery details
        """
        # Validate phone number exists
        if not technician.phone_number:
            logger.warning(
                f"Cannot deliver SMS invitation to {technician.technician_id}: "
                "no phone number"
            )
            return DeliveryResult(
                success=False,
                technician_id=technician.technician_id,
                delivery_method="sms",
                error="Technician has no phone number",
            )

        # Generate invitation
        try:
            invitation = self.invitation_service.generate_invitation(
                technician.technician_id
            )
        except Exception as e:
            logger.error(
                f"Failed to generate invitation for {technician.technician_id}: {e}",
                exc_info=True
            )
            return DeliveryResult(
                success=False,
                technician_id=technician.technician_id,
                delivery_method="sms",
                destination=technician.phone_number,
                error=f"Failed to generate invitation: {str(e)}",
            )

        # Attempt SMS delivery (non-blocking pattern)
        delivery_attempted = True
        delivery_succeeded = False

        try:
            sms_sent = await self.sms_service.send_telegram_invitation(
                phone_number=technician.phone_number,
                technician_name=technician.name,
                telegram_link=invitation.telegram_link,
            )

            delivery_succeeded = sms_sent

            if not sms_sent:
                logger.error(
                    f"SMS service returned False for {technician.technician_id} "
                    f"at {technician.phone_number}"
                )
        except Exception as e:
            logger.error(
                f"Exception sending SMS to {technician.technician_id}: {e}",
                exc_info=True
            )

        # Return success (invitation created, even if SMS failed)
        # This follows the non-blocking notification pattern
        return DeliveryResult(
            success=True,
            technician_id=technician.technician_id,
            delivery_method="sms",
            destination=technician.phone_number,
            invitation_link=invitation.telegram_link,
            expires_at=invitation.expires_at,
            delivery_attempted=delivery_attempted,
            delivery_succeeded=delivery_succeeded,
        )


class EmailInvitationDelivery(InvitationDeliveryService):
    """Email-based invitation delivery using AWS SES or fake service."""

    def __init__(
        self,
        invitation_service: TelegramInvitationService,
        email_service,  # Type: SESEmailService or FakeEmailService
    ):
        """
        Initialize Email delivery service.

        Args:
            invitation_service: Service for generating invitation tokens
            email_service: Email service for sending messages (SES or fake)
        """
        super().__init__(invitation_service)
        self.email_service = email_service

    async def deliver(self, technician: Technician) -> DeliveryResult:
        """
        Generate invitation and deliver via Email.

        Args:
            technician: Technician to receive invitation

        Returns:
            DeliveryResult with email delivery details
        """
        # Validate email exists
        if not technician.email:
            logger.warning(
                f"Cannot deliver Email invitation to {technician.technician_id}: "
                "no email address"
            )
            return DeliveryResult(
                success=False,
                technician_id=technician.technician_id,
                delivery_method="email",
                error="Technician has no email address",
            )

        # Generate invitation
        try:
            invitation = self.invitation_service.generate_invitation(
                technician.technician_id
            )
        except Exception as e:
            logger.error(
                f"Failed to generate invitation for {technician.technician_id}: {e}",
                exc_info=True
            )
            return DeliveryResult(
                success=False,
                technician_id=technician.technician_id,
                delivery_method="email",
                destination=technician.email,
                error=f"Failed to generate invitation: {str(e)}",
            )

        # Attempt email delivery (non-blocking pattern)
        delivery_attempted = True
        delivery_succeeded = False

        try:
            email_sent = await self.email_service.send_telegram_invitation(
                email=technician.email,
                technician_name=technician.name,
                telegram_link=invitation.telegram_link,
            )

            delivery_succeeded = email_sent

            if not email_sent:
                logger.error(
                    f"Email service returned False for {technician.technician_id} "
                    f"at {technician.email}"
                )
        except Exception as e:
            logger.error(
                f"Exception sending email to {technician.technician_id}: {e}",
                exc_info=True
            )

        # Return success (invitation created, even if email failed)
        # This follows the non-blocking notification pattern
        return DeliveryResult(
            success=True,
            technician_id=technician.technician_id,
            delivery_method="email",
            destination=technician.email,
            invitation_link=invitation.telegram_link,
            expires_at=invitation.expires_at,
            delivery_attempted=delivery_attempted,
            delivery_succeeded=delivery_succeeded,
        )


def get_invitation_delivery_service(
    method: str,
    invitation_service: TelegramInvitationService,
    sms_service: SMSService | None = None,
    email_service=None,  # Type: SESEmailService or FakeEmailService
) -> InvitationDeliveryService:
    """
    Factory function for creating invitation delivery services.

    Args:
        method: Delivery method ("sms" or "email")
        invitation_service: Invitation token generation service
        sms_service: SMS service (required for "sms" method)
        email_service: Email service (required for "email" method)

    Returns:
        Appropriate InvitationDeliveryService implementation

    Raises:
        ValueError: If method is unsupported or required service is missing
    """
    if method == "sms":
        if not sms_service:
            raise ValueError("sms_service is required for SMS delivery")
        return SMSInvitationDelivery(
            invitation_service=invitation_service,
            sms_service=sms_service,
        )
    elif method == "email":
        if not email_service:
            raise ValueError("email_service is required for Email delivery")
        return EmailInvitationDelivery(
            invitation_service=invitation_service,
            email_service=email_service,
        )
    else:
        raise ValueError(f"Unsupported delivery method: {method}")
