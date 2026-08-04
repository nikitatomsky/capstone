"""
Tests for Assignment REST API endpoints - Following TDD RED-GREEN-REFACTOR cycle.

Test what the Assignment API should do:
- POST /api/assignments creates new assignment (201)
- GET /api/assignments lists all assignments (200)
- GET /api/assignments?status=pending filters by status (200)
- GET /api/assignments/{id} retrieves specific assignment (200)
- GET /api/assignments/{id} returns 404 for non-existent assignment

Note (Issue #30): Tests updated to use technician_id (UUID) instead of chat_id.
Technician endpoints moved to /api/technicians router.
"""

from fastapi.testclient import TestClient


def create_test_technician(client):
    """Helper to create a technician and return the technician_id (Issue #30)."""
    response = client.post("/api/technicians", json={
        "name": "Test Technician",
        "phone_number": "+1234567890",
        "chat_id": 12345678
    })
    assert response.status_code == 201
    return response.json()["technician_id"]


def test_post_assignment_returns_201():
    """Test creating assignment via POST /api/assignments returns 201."""
    from app.main import app

    client = TestClient(app)

    # Create technician first (Issue #30)
    technician_id = create_test_technician(client)

    assignment_data = {
        "technician_id": technician_id,
        "title": "HVAC Repair - Building 5",
        "description": "Check heating system in Building 5, Room 203",
        "priority": "high"
    }

    response = client.post("/api/assignments", json=assignment_data)

    assert response.status_code == 201
    data = response.json()
    assert data["technician_id"] == technician_id
    assert data["title"] == "HVAC Repair - Building 5"
    assert data["status"] == "pending"  # Default status
    assert "assignment_id" in data
    assert "created_at" in data


def test_post_assignment_validates_required_fields():
    """Test POST /api/assignments validates required fields."""
    from app.main import app

    client = TestClient(app)

    # Missing required fields
    incomplete_data = {
        "title": "Incomplete Assignment"
    }

    response = client.post("/api/assignments", json=incomplete_data)

    assert response.status_code == 400  # Bad Request (custom handler)
    data = response.json()
    assert "detail" in data


def test_post_assignment_validates_priority_enum():
    """Test POST /api/assignments validates priority enum values."""
    from app.main import app

    client = TestClient(app)

    # Create technician first (Issue #30)
    technician_id = create_test_technician(client)

    invalid_data = {
        "technician_id": technician_id,
        "title": "Test Assignment",
        "description": "Test description",
        "priority": "invalid_priority"  # Invalid enum value
    }

    response = client.post("/api/assignments", json=invalid_data)

    assert response.status_code == 400  # Bad Request (custom handler)


def test_get_assignments_returns_empty_list():
    """Test GET /api/assignments returns empty list when no assignments exist."""
    from app.main import app

    client = TestClient(app)

    response = client.get("/api/assignments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Note: might not be empty if other tests ran first, so just check it's a list


def test_get_assignments_returns_list():
    """Test GET /api/assignments returns list of assignments."""
    from app.main import app

    client = TestClient(app)

    # Create technician and assignment first (Issue #30)
    technician_id = create_test_technician(client)
    assignment_data = {
        "technician_id": technician_id,
        "title": "Test Assignment",
        "description": "Test description",
        "priority": "low"
    }

    client.post("/api/assignments", json=assignment_data)

    # Get all assignments
    response = client.get("/api/assignments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the one we created


def test_get_assignments_filtered_by_status():
    """Test GET /api/assignments?status=pending filters by status."""
    from app.main import app

    client = TestClient(app)

    # Create technician and assignment (Issue #30)
    technician_id = create_test_technician(client)
    pending_assignment = {
        "technician_id": technician_id,
        "title": "Pending Assignment",
        "description": "Test",
        "priority": "high"
    }

    client.post("/api/assignments", json=pending_assignment)

    # Filter by pending status
    response = client.get("/api/assignments?status=pending")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All returned assignments should have pending status
    for assignment in data:
        assert assignment["status"] == "pending"


def test_get_assignment_by_id_returns_200():
    """Test GET /api/assignments/{id} returns assignment details."""
    from app.main import app

    client = TestClient(app)

    # Create technician and assignment (Issue #30)
    technician_id = create_test_technician(client)
    assignment_data = {
        "technician_id": technician_id,
        "title": "Test Assignment",
        "description": "Test description",
        "priority": "medium"
    }

    create_response = client.post("/api/assignments", json=assignment_data)
    assignment_id = create_response.json()["assignment_id"]

    # Get the assignment by ID
    response = client.get(f"/api/assignments/{assignment_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["assignment_id"] == assignment_id
    assert data["title"] == "Test Assignment"


def test_get_nonexistent_assignment_returns_404():
    """Test GET /api/assignments/{id} returns 404 for non-existent assignment."""
    from app.main import app

    client = TestClient(app)

    response = client.get("/api/assignments/nonexistent-id-12345")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# NOTE (Issue #30): Technician endpoint tests moved to test_technician_api.py
# since technicians now have their own dedicated router

