"""
Assignment repository for managing assignments and technicians.

Provides an abstract repository interface and a DynamoDB implementation.
Includes a fake in-memory implementation for testing.
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.models.assignment import Assignment
from app.models.technician import Technician

logger = logging.getLogger(__name__)


class AssignmentRepository(ABC):
    """
    Abstract repository interface for assignment and technician persistence.

    This interface defines the contract for storing and retrieving assignments
    and technician profiles. Implementations can use different storage backends
    (SQLite for local, DynamoDB for production).
    """

    @abstractmethod
    def create_assignment(self, assignment: Assignment) -> Assignment:
        """Create a new assignment and return it."""

    @abstractmethod
    def get_assignment(self, assignment_id: str) -> Assignment | None:
        """Retrieve an assignment by ID, or None if not found."""

    @abstractmethod
    def list_assignments(self, status: str | None = None) -> list[Assignment]:
        """List all assignments, optionally filtered by status."""

    @abstractmethod
    def update_assignment_status(self, assignment_id: str, status: str) -> Assignment | None:
        """Update assignment status and return updated assignment, or None if not found."""

    @abstractmethod
    def complete_assignment(self, assignment_id: str, intake_record_id: str) -> Assignment | None:
        """
        Mark assignment as completed with intake record link.

        Sets status to 'completed', sets intake_record_id, and sets completed_at timestamp.

        Args:
            assignment_id: ID of the assignment to complete
            intake_record_id: ID of the completed intake record

        Returns:
            Updated Assignment or None if not found
        """

    @abstractmethod
    def get_active_assignment_for_technician(self, chat_id: int) -> Assignment | None:
        """
        Get the most recent active assignment for a technician.

        Active means status is one of: pending, assigned, in_progress.
        If multiple active assignments exist, return the most recently created one.

        Args:
            chat_id: Telegram chat_id of the technician

        Returns:
            Most recent active Assignment or None if no active assignments exist
        """

    @abstractmethod
    def create_technician(self, technician: Technician) -> Technician:
        """Register a new technician and return it."""

    @abstractmethod
    def get_technician(self, chat_id: int) -> Technician | None:
        """Retrieve a technician by chat_id, or None if not found."""

    @abstractmethod
    def list_technicians(self) -> list[Technician]:
        """List all registered technicians."""


class DynamoDBAssignmentRepository(AssignmentRepository):
    """
    DynamoDB implementation of AssignmentRepository.

    Uses DynamoDB tables for production-ready persistence:
    - assignments table: stores Assignment records
    - technicians table: stores Technician records

    Args:
        dynamodb_resource: boto3 DynamoDB resource (can be mocked for testing)
        assignments_table_name: Name of the assignments DynamoDB table
        technicians_table_name: Name of the technicians DynamoDB table
    """

    def __init__(
        self,
        dynamodb_resource: Any = None,
        assignments_table_name: str | None = None,
        technicians_table_name: str | None = None
    ):
        if dynamodb_resource is None:
            # Use real DynamoDB from environment
            region = os.getenv("AWS_REGION", "us-east-2")
            self.dynamodb = boto3.resource("dynamodb", region_name=region)
        else:
            # Use provided resource (for testing with mocks)
            self.dynamodb = dynamodb_resource

        # Get table names from environment or use provided names
        self.assignments_table_name = assignments_table_name or os.getenv(
            "DYNAMODB_ASSIGNMENTS_TABLE", "field-intake-assignments-dev"
        )
        self.technicians_table_name = technicians_table_name or os.getenv(
            "DYNAMODB_TECHNICIANS_TABLE", "field-intake-technicians-dev"
        )

        self.assignments_table = self.dynamodb.Table(self.assignments_table_name)
        self.technicians_table = self.dynamodb.Table(self.technicians_table_name)

    def create_assignment(self, assignment: Assignment) -> Assignment:
        """Create a new assignment in DynamoDB."""
        item = {
            "assignment_id": assignment.assignment_id,
            "technician_chat_id": assignment.technician_chat_id,
            "technician_name": assignment.technician_name,
            "title": assignment.title,
            "description": assignment.description,
            "priority": assignment.priority,
            "status": assignment.status,
            "created_at": assignment.created_at.isoformat(),
        }

        if assignment.assigned_at:
            item["assigned_at"] = assignment.assigned_at.isoformat()
        if assignment.completed_at:
            item["completed_at"] = assignment.completed_at.isoformat()
        if assignment.intake_record_id:
            item["intake_record_id"] = assignment.intake_record_id

        self.assignments_table.put_item(Item=item)
        return assignment

    def get_assignment(self, assignment_id: str) -> Assignment | None:
        """Retrieve an assignment by ID from DynamoDB."""
        try:
            response = self.assignments_table.get_item(
                Key={"assignment_id": assignment_id}
            )

            if "Item" not in response:
                return None

            return self._item_to_assignment(response["Item"])
        except ClientError:
            return None

    def list_assignments(self, status: str | None = None) -> list[Assignment]:
        """List assignments, optionally filtered by status."""
        try:
            if status:
                # Use scan with filter for status (in production, use GSI)
                response = self.assignments_table.scan(
                    FilterExpression="#status = :status",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={":status": status}
                )
            else:
                response = self.assignments_table.scan()

            items = response.get("Items", [])
            return [self._item_to_assignment(item) for item in items]
        except ClientError:
            return []

    def update_assignment_status(self, assignment_id: str, status: str) -> Assignment | None:
        """Update assignment status in DynamoDB."""
        try:
            response = self.assignments_table.update_item(
                Key={"assignment_id": assignment_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": status},
                ReturnValues="ALL_NEW"
            )

            if "Attributes" not in response:
                return None

            return self._item_to_assignment(response["Attributes"])
        except ClientError:
            return None

    def complete_assignment(self, assignment_id: str, intake_record_id: str) -> Assignment | None:
        """Mark assignment as completed with intake record link in DynamoDB."""
        from datetime import UTC, datetime

        try:
            completed_at = datetime.now(UTC).isoformat()

            response = self.assignments_table.update_item(
                Key={"assignment_id": assignment_id},
                UpdateExpression=(
                    "SET #status = :status, "
                    "intake_record_id = :intake_id, "
                    "completed_at = :completed"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "completed",
                    ":intake_id": intake_record_id,
                    ":completed": completed_at
                },
                ReturnValues="ALL_NEW"
            )

            if "Attributes" not in response:
                return None

            return self._item_to_assignment(response["Attributes"])
        except ClientError:
            return None

    def get_active_assignment_for_technician(self, chat_id: int) -> Assignment | None:
        """Get the most recent active assignment for a technician from DynamoDB."""
        try:
            # Query using GSI on technician_chat_id
            # Note: This assumes a GSI exists on technician_chat_id
            # For now, we'll scan and filter (less efficient but works for demo)
            response = self.assignments_table.scan(
                FilterExpression=(
                    "technician_chat_id = :chat_id AND "
                    "#status IN (:pending, :assigned, :in_progress)"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":chat_id": chat_id,
                    ":pending": "pending",
                    ":assigned": "assigned",
                    ":in_progress": "in_progress"
                }
            )

            items = response.get("Items", [])
            if not items:
                return None

            # Convert to Assignment objects and find most recent
            assignments = [self._item_to_assignment(item) for item in items]
            return max(assignments, key=lambda a: a.created_at)
        except ClientError:
            return None

    def create_technician(self, technician: Technician) -> Technician:
        """Register a new technician in DynamoDB."""
        item = {
            "chat_id": technician.chat_id,
            "name": technician.name,
            "phone_number": technician.phone_number,
            "registered_at": technician.registered_at.isoformat()
        }

        self.technicians_table.put_item(Item=item)
        return technician

    def get_technician(self, chat_id: int) -> Technician | None:
        """Retrieve a technician by chat_id from DynamoDB."""
        try:
            response = self.technicians_table.get_item(
                Key={"chat_id": chat_id}
            )

            if "Item" not in response:
                return None

            return self._item_to_technician(response["Item"])
        except ClientError:
            return None

    def list_technicians(self) -> list[Technician]:
        """List all registered technicians."""
        try:
            response = self.technicians_table.scan()
            items = response.get("Items", [])
            return [self._item_to_technician(item) for item in items]
        except ClientError:
            return []

    def _item_to_assignment(self, item: dict) -> Assignment:
        """Convert DynamoDB item to Assignment model."""
        return Assignment(
            assignment_id=item["assignment_id"],
            technician_id=item["technician_id"],
            technician_name=item["technician_name"],
            title=item["title"],
            description=item["description"],
            priority=item["priority"],
            status=item["status"],
            created_at=datetime.fromisoformat(item["created_at"]),
            assigned_at=(
                datetime.fromisoformat(item["assigned_at"])
                if item.get("assigned_at")
                else None
            ),
            completed_at=(
                datetime.fromisoformat(item["completed_at"])
                if item.get("completed_at")
                else None
            ),
            intake_record_id=item.get("intake_record_id")
        )

    def _item_to_technician(self, item: dict) -> Technician:
        """Convert DynamoDB item to Technician model."""
        return Technician(
            chat_id=int(item["chat_id"]),
            name=item["name"],
            phone_number=item["phone_number"],
            registered_at=datetime.fromisoformat(item["registered_at"])
        )


# Fake in-memory implementation for testing
class FakeAssignmentRepository(AssignmentRepository):
    """In-memory fake repository for testing without DynamoDB."""

    def __init__(self):
        self._assignments: dict[str, Assignment] = {}
        self._technicians: dict[int, Technician] = {}

    def create_assignment(self, assignment: Assignment) -> Assignment:
        self._assignments[assignment.assignment_id] = assignment
        return assignment

    def get_assignment(self, assignment_id: str) -> Assignment | None:
        return self._assignments.get(assignment_id)

    def list_assignments(self, status: str | None = None) -> list[Assignment]:
        assignments = list(self._assignments.values())
        if status:
            return [a for a in assignments if a.status == status]
        return assignments

    def update_assignment_status(self, assignment_id: str, status: str) -> Assignment | None:
        assignment = self._assignments.get(assignment_id)
        if assignment is None:
            return None
        # Create a new assignment with updated status
        updated = Assignment(
            assignment_id=assignment.assignment_id,
            technician_id=assignment.technician_id,
            technician_name=assignment.technician_name,
            title=assignment.title,
            description=assignment.description,
            priority=assignment.priority,
            status=status,
            created_at=assignment.created_at,
            assigned_at=assignment.assigned_at,
            completed_at=assignment.completed_at,
            intake_record_id=assignment.intake_record_id
        )
        self._assignments[assignment_id] = updated
        return updated

    def complete_assignment(self, assignment_id: str, intake_record_id: str) -> Assignment | None:
        """Mark assignment as completed with intake record link."""
        from datetime import UTC, datetime

        assignment = self._assignments.get(assignment_id)
        if assignment is None:
            return None

        # Create updated assignment with completed status and intake link
        updated = Assignment(
            assignment_id=assignment.assignment_id,
            technician_id=assignment.technician_id,
            technician_name=assignment.technician_name,
            title=assignment.title,
            description=assignment.description,
            priority=assignment.priority,
            status="completed",
            created_at=assignment.created_at,
            assigned_at=assignment.assigned_at,
            completed_at=datetime.now(UTC),
            intake_record_id=intake_record_id
        )
        self._assignments[assignment_id] = updated
        return updated

    def get_active_assignment_for_technician(self, chat_id: int) -> Assignment | None:
        """Get the most recent active assignment for a technician (legacy method using chat_id)."""
        # Note (Issue #30): This method is deprecated in favor of
        # get_active_assignment_by_technician_id
        # Kept for backward compatibility only
        logger.warning(
            f"get_active_assignment_for_technician called with chat_id={chat_id} - "
            f"this method is deprecated, use get_active_assignment_by_technician_id instead"
        )
        return None

    def get_active_assignment_by_technician_id(self, technician_id: str) -> Assignment | None:
        """Get the most recent active assignment for a technician by their technician_id."""
        active_statuses = ["pending", "assigned", "in_progress"]

        # Find all active assignments for this technician
        active_assignments = [
            assignment for assignment in self._assignments.values()
            if assignment.technician_id == technician_id and assignment.status in active_statuses
        ]

        if not active_assignments:
            return None

        # Return the most recent one (by created_at timestamp)
        return max(active_assignments, key=lambda a: a.created_at)

    def create_technician(self, technician: Technician) -> Technician:
        self._technicians[technician.chat_id] = technician
        return technician

    def get_technician(self, chat_id: int) -> Technician | None:
        return self._technicians.get(chat_id)

    def list_technicians(self) -> list[Technician]:
        return list(self._technicians.values())
