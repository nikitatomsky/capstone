"""
Tests for AssignmentRepository - Following TDD RED-GREEN-REFACTOR cycle.

Test what the AssignmentRepository should do:
- Create and retrieve assignments
- List assignments with optional status filter
- Update assignment status
- Register and list technicians
- Handle non-existent resources gracefully
"""



def test_create_assignment():
    """Test assignment creation and retrieval."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()  # In-memory fake for testing
    
    assignment = Assignment(
        assignment_id="test-123",
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="HVAC Repair",
        description="Fix heating system",
        priority="high",
        status="pending"
    )
    
    created = repo.create_assignment(assignment)
    
    assert created.assignment_id == "test-123"
    assert created.title == "HVAC Repair"
    assert created.status == "pending"


def test_get_assignment_by_id():
    """Test retrieval of assignment by ID."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    assignment = Assignment(
        assignment_id="test-123",
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="HVAC Repair",
        description="Fix heating system",
        priority="high"
    )
    
    repo.create_assignment(assignment)
    retrieved = repo.get_assignment("test-123")
    
    assert retrieved is not None
    assert retrieved.assignment_id == "test-123"
    assert retrieved.title == "HVAC Repair"


def test_get_nonexistent_assignment():
    """Test that retrieving non-existent assignment returns None."""
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    result = repo.get_assignment("nonexistent-id")
    
    assert result is None


def test_list_assignments_empty():
    """Test listing assignments when repository is empty."""
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    assignments = repo.list_assignments()
    
    assert assignments == []


def test_list_assignments_all():
    """Test listing all assignments."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    assignment1 = Assignment(
        assignment_id="test-1",
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="Assignment 1",
        description="Description 1",
        priority="high"
    )
    
    assignment2 = Assignment(
        assignment_id="test-2",
        technician_chat_id=87654321,
        technician_name="Jane Doe",
        title="Assignment 2",
        description="Description 2",
        priority="low",
        status="completed"
    )
    
    repo.create_assignment(assignment1)
    repo.create_assignment(assignment2)
    
    assignments = repo.list_assignments()
    
    assert len(assignments) == 2
    assignment_ids = {a.assignment_id for a in assignments}
    assert "test-1" in assignment_ids
    assert "test-2" in assignment_ids


def test_list_assignments_filtered_by_status():
    """Test listing assignments filtered by status."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    pending = Assignment(
        assignment_id="pending-1",
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="Pending Assignment",
        description="Description",
        priority="high",
        status="pending"
    )
    
    completed = Assignment(
        assignment_id="completed-1",
        technician_chat_id=87654321,
        technician_name="Jane Doe",
        title="Completed Assignment",
        description="Description",
        priority="low",
        status="completed"
    )
    
    repo.create_assignment(pending)
    repo.create_assignment(completed)
    
    # Filter by pending
    pending_list = repo.list_assignments(status="pending")
    assert len(pending_list) == 1
    assert pending_list[0].assignment_id == "pending-1"
    
    # Filter by completed
    completed_list = repo.list_assignments(status="completed")
    assert len(completed_list) == 1
    assert completed_list[0].assignment_id == "completed-1"
    
    # All assignments
    all_list = repo.list_assignments()
    assert len(all_list) == 2


def test_update_assignment_status():
    """Test updating assignment status."""
    from app.models.assignment import Assignment
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    assignment = Assignment(
        assignment_id="test-123",
        technician_chat_id=12345678,
        technician_name="John Smith",
        title="HVAC Repair",
        description="Fix heating system",
        priority="high",
        status="pending"
    )
    
    repo.create_assignment(assignment)
    
    # Update to in_progress
    updated = repo.update_assignment_status("test-123", "in_progress")
    
    assert updated is not None
    assert updated.status == "in_progress"
    
    # Verify change persisted
    retrieved = repo.get_assignment("test-123")
    assert retrieved.status == "in_progress"


def test_update_nonexistent_assignment():
    """Test that updating non-existent assignment returns None."""
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    result = repo.update_assignment_status("nonexistent-id", "completed")
    
    assert result is None


def test_create_technician():
    """Test technician registration."""
    from app.models.technician import Technician
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    technician = Technician(
        chat_id=12345678,
        name="John Smith",
        phone_number="+1-555-0123"
    )
    
    created = repo.create_technician(technician)
    
    assert created.chat_id == 12345678
    assert created.name == "John Smith"
    assert created.phone_number == "+1-555-0123"


def test_get_technician_by_chat_id():
    """Test retrieving technician by chat_id."""
    from app.models.technician import Technician
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    technician = Technician(
        chat_id=12345678,
        name="John Smith",
        phone_number="+1-555-0123"
    )
    
    repo.create_technician(technician)
    retrieved = repo.get_technician(12345678)
    
    assert retrieved is not None
    assert retrieved.chat_id == 12345678
    assert retrieved.name == "John Smith"


def test_get_nonexistent_technician():
    """Test that retrieving non-existent technician returns None."""
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    result = repo.get_technician(99999999)
    
    assert result is None


def test_list_technicians_empty():
    """Test listing technicians when repository is empty."""
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    technicians = repo.list_technicians()
    
    assert technicians == []


def test_list_technicians():
    """Test listing all technicians."""
    from app.models.technician import Technician
    from app.repositories.assignment_repository import FakeAssignmentRepository
    
    repo = FakeAssignmentRepository()
    
    tech1 = Technician(
        chat_id=12345678,
        name="John Smith",
        phone_number="+1-555-0123"
    )
    
    tech2 = Technician(
        chat_id=87654321,
        name="Jane Doe",
        phone_number="+1-555-0124"
    )
    
    repo.create_technician(tech1)
    repo.create_technician(tech2)
    
    technicians = repo.list_technicians()
    
    assert len(technicians) == 2
    chat_ids = {t.chat_id for t in technicians}
    assert 12345678 in chat_ids
    assert 87654321 in chat_ids
