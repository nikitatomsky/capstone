"""LLM provider implementations."""

import logging
import os
import time

from anthropic import Anthropic, APIError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.exceptions import LLMAPIError
from app.services.extraction_service import LLMProvider

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_TOKENS = 1024  # Sufficient for JSON extraction response
DEFAULT_TIMEOUT_SECONDS = 30  # Prevent hanging requests
MAX_RETRY_ATTEMPTS = 3  # Number of retry attempts for transient errors


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds

        Raises:
            ValueError: If no API key is provided
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required (ANTHROPIC_API_KEY env var or constructor arg)"
            )

        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = Anthropic(api_key=self.api_key, timeout=timeout)
        logger.info(
            f"AnthropicProvider initialized: model={model}, "
            f"max_tokens={max_tokens}, timeout={timeout}s"
        )
        # NOTE: Never log self.api_key or self.client details

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError),
        reraise=True,
    )
    def generate(self, prompt: str, system_message: str) -> str:
        """
        Generate completion from Claude.

        Args:
            prompt: User prompt
            system_message: System/instruction prompt

        Returns:
            Generated text response (JSON string)

        Raises:
            LLMAPIError: If API call fails
        """
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_message,
                messages=[{"role": "user", "content": prompt}],
            )

            duration = time.time() - start_time
            result = response.content[0].text
            
            # Log usage metrics for cost tracking
            logger.info(
                f"LLM API call completed: "
                f"model={self.model}, "
                f"duration={duration:.2f}s, "
                f"input_tokens={response.usage.input_tokens}, "
                f"output_tokens={response.usage.output_tokens}, "
                f"response_chars={len(result)}"
            )
            
            return result

        except APIError as e:
            duration = time.time() - start_time
            error_msg = str(e).lower()
            logger.exception("Anthropic API error")
            
            # Log failed attempt metrics
            logger.warning(
                f"LLM API call failed after {duration:.2f}s: {error_msg[:100]}"
            )
            
            # Provide specific error messages for common issues
            if "rate_limit" in error_msg:
                raise LLMAPIError("Rate limit exceeded") from e
            elif "authentication" in error_msg or "api_key" in error_msg:
                raise LLMAPIError("API authentication failed") from e
            elif "timeout" in error_msg:
                raise LLMAPIError(f"Request timeout after {self.timeout}s") from e
            else:
                raise LLMAPIError(f"LLM API error: {e}") from e
