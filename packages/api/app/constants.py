"""Application-wide constants for the Field Intake Service."""

# Logging
MAX_LOG_MESSAGE_LENGTH = 50  # Characters to show in logs

# Telegram
MAX_MESSAGE_LENGTH = 4096  # Telegram message limit

# Session Management
MAX_CONVERSATION_HISTORY = 100  # Maximum messages to retain per session

# LLM Provider
DEFAULT_MAX_TOKENS = 1024  # Sufficient for JSON extraction response
DEFAULT_TIMEOUT_SECONDS = 30  # Prevent hanging requests
MAX_RETRY_ATTEMPTS = 3  # Number of retry attempts for transient errors

# System prompt for LLM extraction
EXTRACTION_SYSTEM_PROMPT = (
    "You are an AI assistant that extracts structured data from "
    "field service reports.\\n\\n"
    "Extract the following fields if present in the message:\\n"
    "- employee_name: Name of the field employee\\n"
    "- location: Service call location or address\\n"
    "- service_type: Type of service (Delivery, Pickup, Fire Drill, etc.)\\n"
    "- outcome: Call outcome (completed, needs_followup, escalated, cancelled)\\n"
    "- notes: Any additional notes or details\\n\\n"
    "Return ONLY a JSON object with the extracted fields. "
    "Do not include fields that are not mentioned.\\n"
    'Example: {"location": "123 Main St", "service_type": "Delivery", '
    '"outcome": "completed"}'
)
