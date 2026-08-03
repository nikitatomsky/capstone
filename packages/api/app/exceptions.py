"""Custom exceptions for Field Intake Service."""


class WebhookError(Exception):
    """Base exception for webhook-related errors."""


class MissingMessageError(WebhookError):
    """Raised when Telegram update has no message field."""


class MissingTextError(WebhookError):
    """Raised when Telegram message has no text content."""


class InvalidChatIdError(WebhookError):
    """Raised when chat_id is invalid or missing."""
