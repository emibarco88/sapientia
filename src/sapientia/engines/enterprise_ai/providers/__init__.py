"""
Enterprise AI provider contracts.

Provider implementations are intentionally not imported here.

This prevents optional provider SDKs, such as OpenAI, Anthropic or
Google SDKs, from becoming mandatory simply because the package is
imported.
"""

from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)

__all__ = [
    "AIProvider",
]