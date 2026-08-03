"""Custom exceptions for Field Intake Service."""


class WebhookError(Exception):
    """Base exception for webhook-related errors."""


class MissingMessageError(WebhookError):
    """Raised when Telegram update has no message field."""


class MissingTextError(WebhookError):
    """Raised when Telegram message has no text content."""


class InvalidChatIdError(WebhookError):
    """Raised when chat_id is invalid or missing."""


class LLMExtractionError(Exception):
    """Base exception for LLM extraction errors."""


class LLMAPIError(LLMExtractionError):
    """Raised when LLM API call fails."""


class LLMParseError(LLMExtractionError):
    """Raised when LLM response cannot be parsed."""
