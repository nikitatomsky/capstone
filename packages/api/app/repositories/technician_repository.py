"""
Technician repository for managing technician profiles.

Provides an abstract repository interface and a DynamoDB implementation.
Includes a fake in-memory implementation for testing.

Issue #30: Separated from AssignmentRepository for cleaner separation of concerns.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from botocore.exceptions import ClientError

from app.models.technician import Technician, TechnicianCreate


class TechnicianRepository(ABC):
    """
    Abstract repository interface for technician persistence.

    This interface defines the contract for storing and retrieving technician
    profiles. Implementations can use different storage backends
    (in-memory for testing, DynamoDB for production).

    Issue #30: Uses technician_id (UUID) as primary key, with optional chat_id.
    """

    @abstractmethod
    def create_technician(self, technician_data: TechnicianCreate) -> Technician:
        """
        Create new technician with auto-generated UUID.

        Args:
            technician_data: TechnicianCreate request model

        Returns:
            Created Technician with auto-generated technician_id
        """

    @abstractmethod
    def get_technician(self, technician_id: str) -> Technician | None:
        """
        Get technician by UUID.

        Args:
            technician_id: UUID of the technician

        Returns:
            Technician or None if not found
        """

    @abstractmethod
    def list_technicians(self) -> list[Technician]:
        """
        Get all technicians.

        Returns:
            List of all registered technicians
        """

    @abstractmethod
    def delete_technician(self, technician_id: str) -> bool:
        """
        Delete technician.

        Args:
            technician_id: UUID of the technician to delete

        Returns:
            False if not found.

        Raises:
            ValueError: If technician has active assignments
        """

    @abstractmethod
    def get_technician_by_chat_id(self, chat_id: int) -> Technician | None:
        """
        Get technician by Telegram chat_id (for backward compatibility).

        Args:
            chat_id: Telegram chat_id

        Returns:
            Technician or None if not found
        """

    @abstractmethod
    def update_technician_chat_id(self, technician_id: str, chat_id: int) -> bool:
        """
        Update technician's Telegram chat_id (for invitation linking).

        Args:
            technician_id: UUID of the technician
            chat_id: Telegram chat_id to link

        Returns:
            True if updated, False if technician not found
        """


class DynamoDBTechnicianRepository(TechnicianRepository):
    """
    DynamoDB implementation of TechnicianRepository.

    Uses DynamoDB tables for production-ready persistence:
    - technicians table: stores Technician records with technician_id as primary key
    - ChatIdIndex GSI: allows lookup by chat_id for Telegram integration

    Args:
        dynamodb_resource: boto3 DynamoDB resource (can be mocked for testing)
        technicians_table_name: Name of the technicians DynamoDB table
        assignments_table_name: Name of the assignments table (for checking active assignments)
    """

    def __init__(
        self,
        dynamodb_resource: Any,
        technicians_table_name: str,
        assignments_table_name: str,
    ):
        self.dynamodb = dynamodb_resource
        self.technicians_table = dynamodb_resource.Table(technicians_table_name)
        self.assignments_table = dynamodb_resource.Table(assignments_table_name)

    def create_technician(self, technician_data: TechnicianCreate) -> Technician:
        """Create technician in DynamoDB with UUID."""
        technician = Technician(
            name=technician_data.name,
            phone_number=technician_data.phone_number,
            email=technician_data.email,
            chat_id=technician_data.chat_id
        )

        item = {
            'technician_id': technician.technician_id,
            'name': technician.name,
            'phone_number': technician.phone_number,
            'registered_at': technician.registered_at.isoformat()
        }

        # Only include optional fields if they're not None
        if technician.chat_id is not None:
            item['chat_id'] = technician.chat_id
        if technician.email is not None:
            item['email'] = technician.email

        self.technicians_table.put_item(Item=item)

        return technician

    def get_technician(self, technician_id: str) -> Technician | None:
        """Get by UUID."""
        try:
            response = self.technicians_table.get_item(Key={'technician_id': technician_id})
            if 'Item' not in response:
                return None

            item = response['Item']
            # Parse registered_at from ISO string
            if isinstance(item.get('registered_at'), str):
                item['registered_at'] = datetime.fromisoformat(item['registered_at'])

            return Technician(**item)
        except ClientError:
            return None

    def list_technicians(self) -> list[Technician]:
        """Get all technicians."""
        try:
            response = self.technicians_table.scan()
            technicians = []

            for item in response.get('Items', []):
                # Parse registered_at from ISO string
                if isinstance(item.get('registered_at'), str):
                    item['registered_at'] = datetime.fromisoformat(item['registered_at'])
                technicians.append(Technician(**item))

            return technicians
        except ClientError:
            return []

    def delete_technician(self, technician_id: str) -> bool:
        """Delete from DynamoDB after checking assignments."""
        # Check for active assignments
        if self._has_active_assignments(technician_id):
            raise ValueError("Cannot delete technician with active assignments")

        try:
            self.technicians_table.delete_item(
                Key={'technician_id': technician_id},
                ConditionExpression='attribute_exists(technician_id)'
            )
            return True
        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return False
        except ClientError:
            return False

    def get_technician_by_chat_id(self, chat_id: int) -> Technician | None:
        """Query ChatIdIndex GSI."""
        try:
            from boto3.dynamodb.conditions import Key

            response = self.technicians_table.query(
                IndexName='ChatIdIndex',
                KeyConditionExpression=Key('chat_id').eq(chat_id)
            )

            if not response.get('Items'):
                return None

            item = response['Items'][0]
            # Parse registered_at from ISO string
            if isinstance(item.get('registered_at'), str):
                item['registered_at'] = datetime.fromisoformat(item['registered_at'])

            return Technician(**item)
        except ClientError:
            return None

    def update_technician_chat_id(self, technician_id: str, chat_id: int) -> bool:
        """Update chat_id in DynamoDB."""
        try:
            self.technicians_table.update_item(
                Key={'technician_id': technician_id},
                UpdateExpression='SET chat_id = :chat_id',
                ExpressionAttributeValues={':chat_id': chat_id},
                ConditionExpression='attribute_exists(technician_id)'
            )
            return True
        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # Technician not found
            return False
        except ClientError:
            return False

    def _has_active_assignments(self, technician_id: str) -> bool:
        """Check if technician has active assignments."""
        try:
            from boto3.dynamodb.conditions import Attr, Key

            # Query assignments using TechnicianIdIndex
            response = self.assignments_table.query(
                IndexName='TechnicianIdIndex',
                KeyConditionExpression=Key('technician_id').eq(technician_id),
                FilterExpression=Attr('status').is_in(['pending', 'assigned', 'in_progress'])
            )

            return len(response.get('Items', [])) > 0
        except ClientError:
            # If query fails, be conservative and prevent deletion
            return True


class FakeTechnicianRepository(TechnicianRepository):
    """
    In-memory fake implementation of TechnicianRepository for testing.

    Stores technicians in a dictionary keyed by technician_id.
    Useful for fast unit tests without requiring DynamoDB.
    """

    def __init__(self):
        self.technicians: dict[str, Technician] = {}
        self.assignments: dict[str, Any] = {}  # For testing assignment checks

    def create_technician(self, technician_data: TechnicianCreate) -> Technician:
        """Create technician with auto-generated UUID."""
        technician = Technician(
            name=technician_data.name,
            phone_number=technician_data.phone_number,
            email=technician_data.email,
            chat_id=technician_data.chat_id
        )

        self.technicians[technician.technician_id] = technician
        return technician

    def get_technician(self, technician_id: str) -> Technician | None:
        """Get by UUID."""
        return self.technicians.get(technician_id)

    def list_technicians(self) -> list[Technician]:
        """Get all technicians."""
        return list(self.technicians.values())

    def delete_technician(self, technician_id: str) -> bool:
        """Delete technician if exists and has no active assignments."""
        if technician_id not in self.technicians:
            return False

        # Check for active assignments
        if self._has_active_assignments(technician_id):
            raise ValueError("Cannot delete technician with active assignments")

        del self.technicians[technician_id]
        return True

    def get_technician_by_chat_id(self, chat_id: int) -> Technician | None:
        """Find technician by chat_id."""
        for technician in self.technicians.values():
            if technician.chat_id == chat_id:
                return technician
        return None

    def update_technician_chat_id(self, technician_id: str, chat_id: int) -> bool:
        """Update technician's chat_id."""
        if technician_id not in self.technicians:
            return False

        technician = self.technicians[technician_id]
        # Create updated technician with new chat_id
        updated_technician = Technician(
            technician_id=technician.technician_id,
            name=technician.name,
            phone_number=technician.phone_number,
            email=technician.email,
            chat_id=chat_id,  # Update chat_id
            registered_at=technician.registered_at
        )
        self.technicians[technician_id] = updated_technician
        return True

    def _has_active_assignments(self, technician_id: str) -> bool:
        """Check if technician has active assignments."""
        # Check local assignments dict
        if self._check_local_assignments(technician_id):
            return True

        # Check global assignment repository
        return self._check_global_assignment_repo(technician_id)

    def _check_local_assignments(self, technician_id: str) -> bool:
        """Check local assignments dictionary for active assignments."""
        for assignment in self.assignments.values():
            if self._is_active_assignment(assignment, technician_id):
                return True
        return False

    def _is_active_assignment(self, assignment, technician_id: str) -> bool:
        """Check if assignment is active for given technician."""
        active_statuses = ['pending', 'assigned', 'in_progress']

        # Handle Assignment object
        if hasattr(assignment, 'technician_id'):
            return (assignment.technician_id == technician_id and
                    assignment.status in active_statuses)

        # Handle dict (from add_assignment_for_testing)
        if isinstance(assignment, dict):
            return (assignment.get('technician_id') == technician_id and
                    assignment.get('status') in active_statuses)

        return False

    def _check_global_assignment_repo(self, technician_id: str) -> bool:
        """Check global assignment repository for active assignments."""
        try:
            import app.routers.assignment
            if not hasattr(app.routers.assignment, '_repository_instance'):
                return False

            repo = app.routers.assignment._repository_instance
            if not repo or not hasattr(repo, '_assignments'):
                return False

            active_statuses = ['pending', 'assigned', 'in_progress']
            for assignment in repo._assignments.values():
                if hasattr(assignment, 'technician_id'):
                    if (assignment.technician_id == technician_id and
                        assignment.status in active_statuses):
                        return True
        except Exception:
            pass  # If assignment repo not available, just check local dict

        return False

    def add_assignment_for_testing(self, assignment_id: str, technician_id: str, status: str):
        """Helper method to add assignments for testing deletion constraints."""
        self.assignments[assignment_id] = {
            'assignment_id': assignment_id,
            'technician_id': technician_id,
            'status': status
        }
