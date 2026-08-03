"""Factory for creating LLM provider instances."""

import logging
import os
from typing import TYPE_CHECKING, Any

from app.services.extraction_service import LLMProvider

if TYPE_CHECKING:
    from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


def create_llm_provider(
    provider_type: str = "anthropic",
    **kwargs: Any,
) -> LLMProvider:
    """
    Factory function for creating LLM provider instances.

    Args:
        provider_type: Type of provider ('anthropic', 'openai', etc.)
        **kwargs: Provider-specific configuration arguments

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider_type is unknown or not supported

    Examples:
        >>> provider = create_llm_provider("anthropic")
        >>> provider = create_llm_provider("anthropic", timeout=60)
        >>> provider = create_llm_provider("anthropic", api_key="sk-...")
    """
    provider_type = provider_type.lower()

    if provider_type == "anthropic":
        from app.services.llm_providers import AnthropicProvider

        # Allow environment variable override
        if "api_key" not in kwargs:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                kwargs["api_key"] = api_key

        logger.info(f"Creating Anthropic LLM provider with config: {list(kwargs.keys())}")
        return AnthropicProvider(**kwargs)

    elif provider_type == "openai":
        # Future support for OpenAI
        raise NotImplementedError(
            "OpenAI provider not yet implemented. "
            "Use provider_type='anthropic' for now."
        )

    else:
        supported = ["anthropic", "openai (planned)"]
        raise ValueError(
            f"Unknown provider type: {provider_type}. "
            f"Supported providers: {', '.join(supported)}"
        )


def create_extraction_service(
    provider_type: str = "anthropic",
    **provider_kwargs: Any,
) -> "ExtractionService":
    """
    Convenience function to create ExtractionService with LLM provider.

    Args:
        provider_type: Type of LLM provider
        **provider_kwargs: Provider-specific configuration

    Returns:
        Configured ExtractionService instance

    Examples:
        >>> service = create_extraction_service()
        >>> service = create_extraction_service("anthropic", timeout=60)
    """
    from app.services.extraction_service import ExtractionService

    provider = create_llm_provider(provider_type, **provider_kwargs)
    return ExtractionService(provider)
