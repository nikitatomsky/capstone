"""
Tests for Technician API endpoints - Following TDD RED-GREEN-REFACTOR cycle.

Tests the dedicated /api/technicians router (Issue #30).

Test coverage:
- POST /api/technicians - Create technician with auto-generated UUID
- GET /api/technicians - List all technicians
- GET /api/technicians/{technician_id} - Get specific technician
- DELETE /api/technicians/{technician_id} - Delete technician
- DELETE validation - Cannot delete technician with active assignments
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_technician_returns_201_with_uuid():
    """Test creating technician returns UUID (Issue #30)."""
    response = client.post("/api/technicians", json={
        "name": "John Doe",
        "phone_number": "+1234567890",
        "chat_id": 123456
    })

    assert response.status_code == 201
    technician = response.json()
    assert "technician_id" in technician
    assert len(technician["technician_id"]) == 36  # UUID format
    assert technician["name"] == "John Doe"
    assert technician["phone_number"] == "+1234567890"
    assert technician["chat_id"] == 123456


def test_post_technician_without_chat_id():
    """Test creating technician without chat_id (Issue #30)."""
    response = client.post("/api/technicians", json={
        "name": "Jane Doe",
        "phone_number": "+0987654321"
    })

    assert response.status_code == 201
    technician = response.json()
    assert technician["chat_id"] is None
    assert "technician_id" in technician


def test_post_technician_with_uuid_phone_placeholder():
    """Test phone number can be UUID placeholder (Issue #30)."""
    import uuid
    phone_uuid = str(uuid.uuid4())

    response = client.post("/api/technicians", json={
        "name": "Test User",
        "phone_number": phone_uuid
    })

    assert response.status_code == 201
    technician = response.json()
    assert technician["phone_number"] == phone_uuid


def test_get_technicians_returns_list():
    """Test listing all technicians (Issue #30)."""
    # Create test technicians
    client.post("/api/technicians", json={"name": "Tech 1", "phone_number": "111"})
    client.post("/api/technicians", json={"name": "Tech 2", "phone_number": "222"})

    response = client.get("/api/technicians")

    assert response.status_code == 200
    technicians = response.json()
    assert isinstance(technicians, list)
    assert len(technicians) >= 2


def test_get_technician_by_id_returns_200():
    """Test getting specific technician by UUID (Issue #30)."""
    # Create technician
    create_response = client.post("/api/technicians", json={
        "name": "Test Tech",
        "phone_number": "555"
    })
    technician_id = create_response.json()["technician_id"]

    # Get by ID
    response = client.get(f"/api/technicians/{technician_id}")

    assert response.status_code == 200
    technician = response.json()
    assert technician["technician_id"] == technician_id
    assert technician["name"] == "Test Tech"


def test_get_technician_by_id_not_found_returns_404():
    """Test getting non-existent technician returns 404 (Issue #30)."""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

    response = client.get(f"/api/technicians/{fake_uuid}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_technician_returns_204():
    """Test deleting technician (Issue #30)."""
    # Create technician
    create_response = client.post("/api/technicians", json={
        "name": "To Delete",
        "phone_number": "999"
    })
    technician_id = create_response.json()["technician_id"]

    # Delete
    response = client.delete(f"/api/technicians/{technician_id}")

    assert response.status_code == 204

    # Verify deleted
    get_response = client.get(f"/api/technicians/{technician_id}")
    assert get_response.status_code == 404


def test_delete_technician_not_found_returns_404():
    """Test deleting non-existent technician returns 404 (Issue #30)."""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"

    response = client.delete(f"/api/technicians/{fake_uuid}")

    assert response.status_code == 404


def test_delete_technician_with_assignments_returns_409():
    """Test cannot delete technician with active assignments (Issue #30)."""
    # Create technician
    tech_response = client.post("/api/technicians", json={
        "name": "Assigned Tech",
        "phone_number": "777"
    })
    technician_id = tech_response.json()["technician_id"]

    # Create assignment for this technician
    client.post("/api/assignments", json={
        "technician_id": technician_id,
        "title": "Test Assignment",
        "description": "Test",
        "priority": "medium"
    })

    # Try to delete
    response = client.delete(f"/api/technicians/{technician_id}")

    assert response.status_code == 409
    assert "active assignments" in response.json()["detail"].lower()


def test_post_technician_validates_required_fields():
    """Test that required fields are validated (Issue #30)."""
    response = client.post("/api/technicians", json={
        "phone_number": "+1234567890"
        # Missing name (required)
    })

    # Custom validation handler returns 400, not 422
    assert response.status_code == 400


def test_post_technician_validates_empty_name():
    """Test that empty name is rejected (Issue #30)."""
    response = client.post("/api/technicians", json={
        "name": "",
        "phone_number": "123"
    })

    # Custom validation handler returns 400, not 422
    assert response.status_code == 400


# Telegram Invitation Tests (Issue #37)


def test_post_telegram_invitation_success(monkeypatch):
    """Test sending invitation to valid technician (Issue #37)."""
    from app.repositories.telegram_invitation_repository import TelegramInvitationRepository
    from app.services.sms_service import FakeSMSService
    from app.services.telegram_invitation_service import TelegramInvitationService

    # Create technician first
    tech_data = {
        "name": "John Smith",
        "phone_number": "+1-555-0123",
        "chat_id": None
    }
    create_response = client.post("/api/technicians/", json=tech_data)
    assert create_response.status_code == 201
    technician_id = create_response.json()["technician_id"]

    # Mock services
    sms_service = FakeSMSService()
    invitation_repo = TelegramInvitationRepository()
    invitation_service = TelegramInvitationService(
        invitation_repo, "test_bot", 3600
    )

    # Inject services into router
    import app.routers.technician as tech_router
    monkeypatch.setattr(tech_router, "_invitation_service", invitation_service)
    monkeypatch.setattr(tech_router, "_sms_service", sms_service)

    # Send invitation
    response = client.post(
        f"/api/technicians/{technician_id}/telegram-invitation"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "expires_at" in data
    assert data["phone_number"] == "+1-555-0123"

    # Verify SMS sent
    assert len(sms_service.sent_messages) == 1
    message = sms_service.get_last_message()
    assert message["phone_number"] == "+1-555-0123"
    assert message["technician_name"] == "John Smith"
    assert "t.me/test_bot?start=" in message["telegram_link"]


def test_post_telegram_invitation_technician_not_found():
    """Test invitation for non-existent technician returns 404 (Issue #37)."""
    response = client.post(
        "/api/technicians/nonexistent-id/telegram-invitation"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_post_telegram_invitation_no_phone_number(monkeypatch):
    """Test invitation for technician without phone number returns 400 (Issue #37)."""
    from app.repositories.telegram_invitation_repository import TelegramInvitationRepository
    from app.services.sms_service import FakeSMSService
    from app.services.telegram_invitation_service import TelegramInvitationService

    # Create technician without phone number
    tech_data = {
        "name": "Jane Doe",
        "phone_number": None,
        "chat_id": 12345
    }
    create_response = client.post("/api/technicians/", json=tech_data)
    technician_id = create_response.json()["technician_id"]

    # Mock services
    sms_service = FakeSMSService()
    invitation_repo = TelegramInvitationRepository()
    invitation_service = TelegramInvitationService(
        invitation_repo, "test_bot", 3600
    )

    # Inject services into router
    import app.routers.technician as tech_router
    monkeypatch.setattr(tech_router, "_invitation_service", invitation_service)
    monkeypatch.setattr(tech_router, "_sms_service", sms_service)

    # Try to send invitation
    response = client.post(
        f"/api/technicians/{technician_id}/telegram-invitation"
    )

    assert response.status_code == 400
    assert "phone number" in response.json()["detail"].lower()


def test_post_telegram_invitation_sms_failure_still_creates_invitation(monkeypatch):
    """Test that invitation is created even if SMS fails (Issue #37)."""
    from app.repositories.telegram_invitation_repository import TelegramInvitationRepository
    from app.services.sms_service import SMSService
    from app.services.telegram_invitation_service import TelegramInvitationService

    # Create failing SMS service
    class FailingSMSService(SMSService):
        async def send_telegram_invitation(self, phone_number, technician_name, telegram_link):
            return False  # Simulate SMS failure

    # Create technician
    tech_data = {
        "name": "Bob Johnson",
        "phone_number": "+1-555-9999",
        "chat_id": None
    }
    create_response = client.post("/api/technicians/", json=tech_data)
    technician_id = create_response.json()["technician_id"]

    # Mock services
    sms_service = FailingSMSService()
    invitation_repo = TelegramInvitationRepository()
    invitation_service = TelegramInvitationService(
        invitation_repo, "test_bot", 3600
    )

    # Inject services into router
    import app.routers.technician as tech_router
    monkeypatch.setattr(tech_router, "_invitation_service", invitation_service)
    monkeypatch.setattr(tech_router, "_sms_service", sms_service)

    # Send invitation (should succeed despite SMS failure)
    response = client.post(
        f"/api/technicians/{technician_id}/telegram-invitation"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Invitation created even though SMS failed
