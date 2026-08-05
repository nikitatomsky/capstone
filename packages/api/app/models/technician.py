"""
Technician model for technician registration and profile management.

Architecture reference: docs/path-to-reactive-flow.md lines 72-77

Updated for Issue #30: UUID-based technician identification with optional chat_id
"""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class Technician(BaseModel):
    """
    Technician model for field employee registration.

    Issue #30: Refactored to use UUID as primary key instead of chat_id.
    The technician_id serves as the primary key for linking assignments.
    chat_id is now optional and only used for Telegram integration.
    """

    technician_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID primary key for technician identification"
    )

    name: str = Field(
        min_length=1,
        description="Display name of the technician"
    )

    phone_number: str | None = Field(
        default=None,
        description="Phone number (can be actual phone or UUID placeholder)"
    )

    email: str | None = Field(
        default=None,
        description="Email address (for email-based invitation delivery)"
    )

    chat_id: int | None = Field(
        default=None,
        description="Optional Telegram chat_id (for Telegram integration)"
    )

    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when technician was registered"
    )

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_not_empty(cls, v: str | None) -> str | None:
        """Ensure phone_number is not empty or whitespace only if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Phone number cannot be empty')
        return v


class TechnicianCreate(BaseModel):
    """
    Request model for registering a new technician.

    Used by the POST /api/technicians endpoint.
    Issue #30: chat_id is now optional (only needed for Telegram integration).
    """

    name: str = Field(
        min_length=1,
        description="Display name of the technician"
    )

    phone_number: str | None = Field(
        default=None,
        description="Phone number (can be actual phone or UUID placeholder)"
    )

    email: str | None = Field(
        default=None,
        description="Email address (for email-based invitation delivery)"
    )

    chat_id: int | None = Field(
        default=None,
        description=(
            "Optional Telegram chat_id "
            "(only needed if technician uses Telegram integration)"
        )
    )
