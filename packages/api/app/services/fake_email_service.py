"""Fake email service for testing (similar to FakeSMSService)."""


class FakeEmailService:
    """In-memory email service for testing."""

    def __init__(self):
        self.sent_emails: list[dict] = []

    async def send_telegram_invitation(
        self,
        email: str,
        technician_name: str,
        telegram_link: str,
    ) -> bool:
        """Record email in memory instead of sending."""
        self.sent_emails.append({
            "email": email,
            "technician_name": technician_name,
            "telegram_link": telegram_link,
        })
        return True

    def get_last_email(self) -> dict | None:
        """Get last sent email for testing."""
        return self.sent_emails[-1] if self.sent_emails else None

    def clear(self) -> None:
        """Clear sent emails."""
        self.sent_emails.clear()
