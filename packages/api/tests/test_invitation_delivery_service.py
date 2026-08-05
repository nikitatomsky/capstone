"""Tests for InvitationDeliveryService abstraction (Issue #39)."""
import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.technician import Technician
from app.models.telegram_invitation import TelegramInvitation


@pytest.fixture
def mock_invitation_service():
    """Mock TelegramInvitationService."""
    service = Mock()
    service.generate_invitation = Mock(return_value=TelegramInvitation(
        token_hash=hashlib.sha256(b"test-token").hexdigest(),
        technician_id="tech-123",
        telegram_link="https://t.me/test_bot?start=abc123xyz",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        created_at=datetime.now(UTC),
        used_at=None,
        expires_at_ttl=int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
    ))
    return service


@pytest.fixture
def sample_technician():
    """Create sample technician."""
    return Technician(
        technician_id="tech-123",
        name="John Doe",
        phone_number="+1-555-0123",
        chat_id=None,
    )


class TestSMSInvitationDelivery:
    """Tests for SMS-based invitation delivery."""

    @pytest.mark.asyncio
    async def test_deliver_invitation_via_sms_success(
        self, mock_invitation_service, sample_technician
    ):
        """Test successful SMS invitation delivery."""
        # Import here to avoid circular dependencies during test collection
        from app.services.invitation_delivery_service import SMSInvitationDelivery
        from app.services.sms_service import FakeSMSService

        sms_service = FakeSMSService()
        delivery_service = SMSInvitationDelivery(
            invitation_service=mock_invitation_service,
            sms_service=sms_service,
        )

        result = await delivery_service.deliver(sample_technician)

        # Should succeed
        assert result.success is True
        assert result.technician_id == "tech-123"
        assert result.delivery_method == "sms"
        assert result.destination == "+1-555-0123"
        assert "t.me/test_bot?start=" in result.invitation_link

        # Should generate invitation
        mock_invitation_service.generate_invitation.assert_called_once_with("tech-123")

        # Should send SMS
        assert len(sms_service.sent_messages) == 1
        sent = sms_service.get_last_message()
        assert sent["phone_number"] == "+1-555-0123"
        assert sent["technician_name"] == "John Doe"
        assert "abc123xyz" in sent["telegram_link"]

    @pytest.mark.asyncio
    async def test_deliver_invitation_via_sms_no_phone(
        self, mock_invitation_service
    ):
        """Test SMS delivery fails when technician has no phone."""
        from app.services.invitation_delivery_service import SMSInvitationDelivery
        from app.services.sms_service import FakeSMSService

        technician = Technician(
            technician_id="tech-456",
            name="Jane Doe",
            phone_number=None,  # No phone
            chat_id=None,
        )

        sms_service = FakeSMSService()
        delivery_service = SMSInvitationDelivery(
            invitation_service=mock_invitation_service,
            sms_service=sms_service,
        )

        result = await delivery_service.deliver(technician)

        # Should fail
        assert result.success is False
        assert result.error == "Technician has no phone number"
        assert result.delivery_method == "sms"

        # Should NOT generate invitation or send SMS
        mock_invitation_service.generate_invitation.assert_not_called()
        assert len(sms_service.sent_messages) == 0

    @pytest.mark.asyncio
    async def test_deliver_invitation_via_sms_send_failure(
        self, mock_invitation_service, sample_technician
    ):
        """Test SMS delivery handles SMS send failures gracefully."""
        from app.services.invitation_delivery_service import SMSInvitationDelivery
        from app.services.sms_service import SMSService

        # Mock SMS service that fails
        failing_sms_service = AsyncMock(spec=SMSService)
        failing_sms_service.send_telegram_invitation = AsyncMock(return_value=False)

        delivery_service = SMSInvitationDelivery(
            invitation_service=mock_invitation_service,
            sms_service=failing_sms_service,
        )

        result = await delivery_service.deliver(sample_technician)

        # Should still succeed (non-blocking notification pattern)
        # Invitation was created, SMS failed but that's logged
        assert result.success is True
        assert result.delivery_attempted is True
        assert result.delivery_succeeded is False

        # Should have generated invitation
        mock_invitation_service.generate_invitation.assert_called_once()


class TestEmailInvitationDelivery:
    """Tests for Email-based invitation delivery."""

    @pytest.mark.asyncio
    async def test_deliver_invitation_via_email_success(
        self, mock_invitation_service
    ):
        """Test successful Email invitation delivery."""
        from app.services.fake_email_service import FakeEmailService
        from app.services.invitation_delivery_service import EmailInvitationDelivery

        technician = Technician(
            technician_id="tech-789",
            name="Bob Smith",
            phone_number="+1-555-9999",
            chat_id=None,
            email="bob.smith@example.com",
        )

        email_service = FakeEmailService()
        delivery_service = EmailInvitationDelivery(
            invitation_service=mock_invitation_service,
            email_service=email_service,
        )

        result = await delivery_service.deliver(technician)

        # Should succeed
        assert result.success is True
        assert result.technician_id == "tech-789"
        assert result.delivery_method == "email"
        assert result.destination == "bob.smith@example.com"

        # Should generate invitation
        mock_invitation_service.generate_invitation.assert_called_once_with("tech-789")

        # Should send email
        assert len(email_service.sent_emails) == 1
        sent = email_service.get_last_email()
        assert sent["email"] == "bob.smith@example.com"
        assert sent["technician_name"] == "Bob Smith"
        assert "abc123xyz" in sent["telegram_link"]

    @pytest.mark.asyncio
    async def test_deliver_invitation_via_email_no_email(
        self, mock_invitation_service
    ):
        """Test Email delivery fails when technician has no email."""
        from app.services.fake_email_service import FakeEmailService
        from app.services.invitation_delivery_service import EmailInvitationDelivery

        technician = Technician(
            technician_id="tech-999",
            name="Alice Brown",
            phone_number="+1-555-1111",
            chat_id=None,
            email=None,  # No email
        )

        email_service = FakeEmailService()
        delivery_service = EmailInvitationDelivery(
            invitation_service=mock_invitation_service,
            email_service=email_service,
        )

        result = await delivery_service.deliver(technician)

        # Should fail
        assert result.success is False
        assert result.error == "Technician has no email address"
        assert result.delivery_method == "email"

        # Should NOT generate invitation
        mock_invitation_service.generate_invitation.assert_not_called()


class TestInvitationDeliveryFactory:
    """Tests for delivery service factory/selection."""

    @pytest.mark.asyncio
    async def test_get_delivery_service_for_sms(
        self, mock_invitation_service
    ):
        """Test getting SMS delivery service from factory."""
        from app.services.invitation_delivery_service import (
            SMSInvitationDelivery,
            get_invitation_delivery_service,
        )
        from app.services.sms_service import FakeSMSService

        sms_service = FakeSMSService()

        delivery_service = get_invitation_delivery_service(
            method="sms",
            invitation_service=mock_invitation_service,
            sms_service=sms_service,
        )

        assert isinstance(delivery_service, SMSInvitationDelivery)

    @pytest.mark.asyncio
    async def test_get_delivery_service_for_email(
        self, mock_invitation_service
    ):
        """Test getting Email delivery service from factory."""
        from app.services.fake_email_service import FakeEmailService
        from app.services.invitation_delivery_service import (
            EmailInvitationDelivery,
            get_invitation_delivery_service,
        )

        email_service = FakeEmailService()

        delivery_service = get_invitation_delivery_service(
            method="email",
            invitation_service=mock_invitation_service,
            email_service=email_service,
        )

        assert isinstance(delivery_service, EmailInvitationDelivery)

    @pytest.mark.asyncio
    async def test_get_delivery_service_invalid_method(
        self, mock_invitation_service
    ):
        """Test factory rejects invalid delivery methods."""
        from app.services.invitation_delivery_service import (
            get_invitation_delivery_service,
        )

        with pytest.raises(ValueError, match="Unsupported delivery method: invalid"):
            get_invitation_delivery_service(
                method="invalid",
                invitation_service=mock_invitation_service,
            )
