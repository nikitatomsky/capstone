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
        "name": "Missing Phone"
        # Missing phone_number
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
