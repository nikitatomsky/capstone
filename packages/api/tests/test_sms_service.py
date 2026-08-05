"""Tests for SMS service."""
import pytest

from app.services.sms_service import FakeSMSService


@pytest.fixture
def sms_service():
    """Create fake SMS service."""
    return FakeSMSService()


@pytest.mark.asyncio
async def test_fake_sms_service_sends_message(sms_service):
    """Test fake SMS service records messages."""
    result = await sms_service.send_telegram_invitation(
        phone_number="+1-555-0123",
        technician_name="John Smith",
        telegram_link="https://t.me/test_bot?start=abc123"
    )

    assert result is True
    assert len(sms_service.sent_messages) == 1

    message = sms_service.get_last_message()
    assert message["phone_number"] == "+1-555-0123"
    assert message["technician_name"] == "John Smith"
    assert "abc123" in message["telegram_link"]


@pytest.mark.asyncio
async def test_fake_sms_service_clear(sms_service):
    """Test clearing sent messages."""
    await sms_service.send_telegram_invitation(
        "+1-555-0123", "John", "https://t.me/bot?start=xyz"
    )

    sms_service.clear()
    assert len(sms_service.sent_messages) == 0
    assert sms_service.get_last_message() is None
