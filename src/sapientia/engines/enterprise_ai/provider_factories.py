"""
Module: provider_factories.py

Purpose:
Defines lazy factories for Enterprise AI provider implementations.

Each provider SDK is imported only when its corresponding factory is
executed.
"""

from __future__ import annotations

from typing import Any

from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)


def create_openai_provider(
    **provider_options: Any,
) -> AIProvider:
    """
    Lazily import and create the OpenAI provider.
    """

    from sapientia.engines.enterprise_ai.providers.openai_provider import (
        OpenAIProvider,
    )

    return OpenAIProvider(
        **provider_options
    )