"""Abstract SMS service for sending messages."""
from abc import ABC, abstractmethod


class SMSService(ABC):
    """Abstract base class for SMS sending services."""

    @abstractmethod
    async def send_telegram_invitation(
        self,
        phone_number: str,
        technician_name: str,
        telegram_link: str,
    ) -> bool:
        """
        Send Telegram invitation via SMS.

        Args:
            phone_number: Recipient phone number (E.164 format recommended)
            technician_name: Technician's name for personalization
            telegram_link: Telegram deeplink with invitation token

        Returns:
            True if SMS sent successfully, False otherwise
        """


class FakeSMSService(SMSService):
    """In-memory SMS service for testing."""

    def __init__(self):
        self.sent_messages: list[dict] = []

    async def send_telegram_invitation(
        self,
        phone_number: str,
        technician_name: str,
        telegram_link: str,
    ) -> bool:
        """Record message in memory instead of sending."""
        self.sent_messages.append({
            "phone_number": phone_number,
            "technician_name": technician_name,
            "telegram_link": telegram_link,
        })
        return True

    def get_last_message(self) -> dict | None:
        """Get last sent message for testing."""
        return self.sent_messages[-1] if self.sent_messages else None

    def clear(self) -> None:
        """Clear sent messages."""
        self.sent_messages.clear()
