"""Data models for field service intake records."""

from datetime import datetime

from pydantic import BaseModel, Field


class IntakeRecord(BaseModel):
    """
    Represents a field service intake record.

    This model captures information about a service call reported by a field employee.
    All fields are optional to support incremental data collection through conversation.

    Note: employee_name is NOT included - it's known from the assignment/technician
    registration and doesn't need to be extracted from the conversation.
    """

    assignment_id: str | None = Field(
        default=None,
        description="Link to the assignment that initiated this intake (if applicable)",
    )
    location: str | None = Field(
        default=None,
        description="Service call location or address",
    )
    service_type: str | None = Field(
        default=None,
        description="Type of service performed (e.g., HVAC Repair, Plumbing, Electrical)",
    )
    outcome: str | None = Field(
        default=None,
        description="Call outcome (e.g., completed, needs_followup, escalated)",
    )
    notes: str | None = Field(
        default=None,
        description="Additional notes or details about the service call",
    )
    timestamp: datetime | None = Field(
        default=None,
        description="When the intake record was created",
    )

    def is_complete(self) -> bool:
        """
        Check if the intake record has all required fields filled.

        Required fields (employee_name removed - known from assignment):
        - location
        - service_type
        - outcome

        Returns:
            True if all required fields are present, False otherwise
        """
        return all(
            [
                self.location is not None,
                self.service_type is not None,
                self.outcome is not None,
            ]
        )
