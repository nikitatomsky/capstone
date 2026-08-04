"""Pydantic models for Telegram invitations."""
from datetime import datetime

from pydantic import BaseModel, Field


class TelegramInvitationCreate(BaseModel):
    """Model for creating a new Telegram invitation."""

    token_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 hash of invitation token (hex string)"
    )
    technician_id: str = Field(
        ...,
        description="UUID of technician receiving invitation"
    )
    telegram_link: str = Field(
        ...,
        description="Telegram deeplink with invitation token"
    )
    expires_at: datetime = Field(
        ...,
        description="Expiration timestamp for invitation"
    )


class TelegramInvitation(TelegramInvitationCreate):
    """Model for Telegram invitation with metadata."""

    created_at: datetime = Field(
        ...,
        description="Timestamp when invitation was created"
    )
    used_at: datetime | None = Field(
        default=None,
        description="Timestamp when invitation was used (null if unused)"
    )
    expires_at_ttl: int | None = Field(
        default=None,
        description="Unix timestamp for DynamoDB TTL (derived from expires_at)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "token_hash": "a1b2c3d4" * 8,
                "technician_id": "550e8400-e29b-41d4-a716-446655440000",
                "telegram_link": "https://t.me/field_bot?start=abc123xyz",
                "expires_at": "2026-08-04T15:30:00Z",
                "created_at": "2026-08-04T14:30:00Z",
                "used_at": None,
                "expires_at_ttl": 1722782000,
            }
        }
