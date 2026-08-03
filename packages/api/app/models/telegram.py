"""Pydantic models for Telegram Bot API data structures."""

from pydantic import BaseModel, ConfigDict, Field


class TelegramUser(BaseModel):
    """Represents a Telegram user."""

    id: int = Field(..., description="Unique identifier for this user")
    is_bot: bool = Field(..., description="True if this user is a bot")
    first_name: str = Field(..., description="User's first name")
    last_name: str | None = Field(None, description="User's last name")
    username: str | None = Field(None, description="User's username")


class TelegramChat(BaseModel):
    """Represents a Telegram chat."""

    id: int = Field(..., description="Unique identifier for this chat")
    type: str = Field(..., description="Type of chat (private, group, etc.)")
    first_name: str | None = Field(None, description="First name for private chats")
    last_name: str | None = Field(None, description="Last name for private chats")
    username: str | None = Field(None, description="Username for private chats")
    title: str | None = Field(None, description="Title for channels and group chats")


class TelegramMessage(BaseModel):
    """Represents a Telegram message."""

    model_config = ConfigDict(populate_by_name=True)

    message_id: int = Field(..., description="Unique message identifier")
    date: int = Field(..., description="Date the message was sent (Unix time)")
    chat: TelegramChat = Field(..., description="Conversation the message belongs to")
    from_user: TelegramUser | None = Field(
        None, alias="from", description="Sender of the message"
    )
    text: str | None = Field(None, description="Text content of the message")


class TelegramUpdate(BaseModel):
    """Represents an incoming Telegram update."""

    model_config = ConfigDict(populate_by_name=True)

    update_id: int = Field(..., description="Unique identifier for this update")
    message: TelegramMessage | None = Field(None, description="New incoming message")
