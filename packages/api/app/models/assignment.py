"""
Assignment and related models for admin-initiated assignment workflow.

Architecture reference: docs/path-to-reactive-flow.md lines 60-70

Updated for Issue #30: Assignment now references technician by UUID (technician_id)
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class Assignment(BaseModel):
    """
    Assignment model for admin-initiated work assignments.

    An assignment represents work assigned to a field technician by an admin.
    The assignment tracks status from creation through completion, and links
    to the completed intake record when the technician finishes the work.

    Issue #30: Now references technician by UUID (technician_id) instead of chat_id.
    """

    assignment_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for the assignment (UUID)"
    )

    technician_id: str = Field(
        description="UUID of the assigned technician"
    )

    technician_name: str = Field(
        description="Display name of the assigned technician"
    )

    title: str = Field(
        description="Short title for the assignment"
    )

    description: str = Field(
        description="Detailed description of the work to be performed"
    )

    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Priority level of the assignment"
    )

    status: Literal["pending", "assigned", "in_progress", "completed", "cancelled"] = Field(
        default="pending",
        description="Current status of the assignment"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when assignment was created"
    )

    assigned_at: datetime | None = Field(
        default=None,
        description="Timestamp when assignment was assigned to technician"
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when assignment was completed"
    )

    intake_record_id: str | None = Field(
        default=None,
        description="Link to the completed intake record (if completed)"
    )


class AssignmentCreate(BaseModel):
    """
    Request model for creating a new assignment.

    Used by the POST /api/assignments endpoint.
    Issue #30: Uses technician_id (UUID) instead of chat_id.
    """

    technician_id: str = Field(
        description="UUID of the technician to assign work to"
    )

    title: str = Field(
        description="Short title for the assignment"
    )

    description: str = Field(
        description="Detailed description of the work to be performed"
    )

    priority: Literal["low", "medium", "high", "urgent"] = Field(
        description="Priority level of the assignment"
    )
