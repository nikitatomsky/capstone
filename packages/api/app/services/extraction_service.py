"""LLM-powered extraction service for intake data."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import ValidationError

from app.constants import EXTRACTION_SYSTEM_PROMPT, MAX_MESSAGE_LENGTH
from app.exceptions import LLMParseError

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_message: str) -> str:
        """
        Generate completion from LLM.

        Args:
            prompt: User prompt
            system_message: System/instruction prompt

        Returns:
            Generated text response
        """


class ExtractionService:
    """
    Service for extracting structured intake data from free-text messages.

    Uses LLM to parse field employee messages and extract structured fields
    like employee_name, location, service_type, outcome, and notes.
    """

    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize extraction service with LLM provider.

        Args:
            llm_provider: LLM provider instance (Anthropic, OpenAI, etc.)
        """
        self.llm_provider = llm_provider
        logger.info(f"ExtractionService initialized with {type(llm_provider).__name__}")

    def extract_from_message(self, message_text: str) -> dict[str, Any]:
        """
        Extract structured intake data from free-text message.

        Args:
            message_text: Free-text message from field employee

        Returns:
            Dict with extracted field names and values, e.g.:
            {
                "employee_name": "John Doe",
                "location": "123 Main St",
                "service_type": "HVAC Repair",
                "outcome": "completed"
            }

            Only includes fields that were successfully extracted.

        Raises:
            ValueError: If message_text is empty or invalid
            TypeError: If message_text is not a string
            LLMParseError: If LLM response cannot be parsed
        """
        # Validate input
        if not isinstance(message_text, str):
            raise TypeError(
                f"Message text must be string, got {type(message_text).__name__}"
            )

        if not message_text or not message_text.strip():
            raise ValueError("Message text cannot be empty")

        # Truncate if exceeds maximum length
        if len(message_text) > MAX_MESSAGE_LENGTH:
            logger.warning(
                f"Message exceeds {MAX_MESSAGE_LENGTH} chars "
                f"({len(message_text)} chars), truncating"
            )
            message_text = message_text[:MAX_MESSAGE_LENGTH]

        prompt = (
            f"Extract structured data from this field service message:\n\n"
            f"{message_text}"
        )

        # Get LLM response
        response = self.llm_provider.generate(prompt, EXTRACTION_SYSTEM_PROMPT)

        # Parse JSON response
        try:
            extracted_data = json.loads(response)
            logger.info(f"Extracted {len(extracted_data)} fields from message")
            
            # Validate against IntakeRecord schema
            self._validate_extracted_data(extracted_data)
            
            return extracted_data
        except json.JSONDecodeError as e:
            logger.exception(
                f"Failed to parse LLM response as JSON. "
                f"Response preview: {response[:200]}..."
            )
            raise LLMParseError(
                "LLM returned invalid JSON format"
            ) from e

    def _validate_extracted_data(self, data: dict[str, Any]) -> None:
        """
        Validate extracted data against IntakeRecord schema.
        
        Logs warnings if validation fails but doesn't raise exceptions,
        allowing partial data to be used.
        
        Args:
            data: Extracted data dictionary
        """
        from app.models.intake import IntakeRecord
        
        try:
            # Attempt to validate with Pydantic model
            IntakeRecord(**data)
        except ValidationError as e:
            # Log validation issues but don't fail extraction
            error_fields = [err["loc"][0] for err in e.errors()]
            logger.warning(
                f"Extracted data validation issues: {error_fields}. "
                f"Continuing with partial data."
            )
