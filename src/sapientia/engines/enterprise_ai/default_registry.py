"""
Module: default_registry.py

Purpose:
Builds Sapientia's default Enterprise AI provider registry.
"""

from __future__ import annotations

from sapientia.engines.enterprise_ai.provider_factories import (
    create_openai_provider,
)
from sapientia.engines.enterprise_ai.provider_registry import (
    AIProviderRegistry,
)


def build_default_provider_registry(
) -> AIProviderRegistry:
    """
    Build the default provider registry.

    Registration does not instantiate providers and does not import
    provider-specific SDKs.
    """

    registry = AIProviderRegistry()

    registry.register(
        provider_name="OPENAI",
        factory=create_openai_provider,
    )

    return registry