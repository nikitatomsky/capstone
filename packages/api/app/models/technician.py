"""
Technician model for technician registration and profile management.

Architecture reference: docs/path-to-reactive-flow.md lines 72-77
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class Technician(BaseModel):
    """
    Technician model for field employee registration.

    Technicians are registered with their Telegram chat_id and phone number.
    The chat_id serves as the primary key for linking assignments and messages.
    """

    chat_id: int = Field(
        description="Telegram chat_id (primary key for technician identification)"
    )

    name: str = Field(
        min_length=1,
        description="Display name of the technician"
    )

    phone_number: str = Field(
        min_length=1,
        description="Phone number associated with Telegram account"
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
    def validate_phone_not_empty(cls, v: str) -> str:
        """Ensure phone_number is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError('Phone number cannot be empty')
        return v


class TechnicianCreate(BaseModel):
    """
    Request model for registering a new technician.

    Used by the POST /api/technicians endpoint.
    """

    chat_id: int = Field(
        description=(
            "Telegram chat_id of the technician "
            "(obtained by having them message the bot first)"
        )
    )

    name: str = Field(
        min_length=1,
        description="Display name of the technician"
    )

    phone_number: str = Field(
        min_length=1,
        description="Phone number associated with their Telegram account"
    )
