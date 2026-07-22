"""
Module: provider_registry.py

Purpose:
Registers and resolves Enterprise AI providers without coupling the
Enterprise AI Engine to a specific vendor.

Provider factories are lazy. A provider SDK is therefore imported only
when that provider is actually selected.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sapientia.engines.enterprise_ai.exceptions import (
    AIProviderLoadError,
    AIProviderNotRegisteredError,
)
from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)


ProviderFactory = Callable[..., AIProvider]


class AIProviderRegistry:
    """
    Registry of available Enterprise AI provider factories.
    """

    def __init__(self) -> None:
        self._provider_factories: dict[
            str,
            ProviderFactory,
        ] = {}

    @staticmethod
    def normalize_provider_name(
        provider_name: str,
    ) -> str:
        """
        Convert provider names into a consistent registry key.
        """

        normalized = str(
            provider_name or ""
        ).strip().upper()

        if not normalized:
            raise ValueError(
                "Provider name cannot be empty."
            )

        return normalized

    def register(
        self,
        provider_name: str,
        factory: ProviderFactory,
        replace: bool = False,
    ) -> None:
        """
        Register a provider factory.

        Parameters
        ----------
        provider_name:
            Logical provider name, for example OPENAI.

        factory:
            Callable that creates and returns an AIProvider.

        replace:
            Whether an existing registration may be replaced.
        """

        normalized_name = (
            self.normalize_provider_name(
                provider_name
            )
        )

        if (
            normalized_name
            in self._provider_factories
            and not replace
        ):
            raise ValueError(
                "AI provider is already registered: "
                f"{normalized_name}"
            )

        if not callable(factory):
            raise TypeError(
                "Provider factory must be callable."
            )

        self._provider_factories[
            normalized_name
        ] = factory

    def unregister(
        self,
        provider_name: str,
    ) -> None:
        """
        Remove a provider registration.
        """

        normalized_name = (
            self.normalize_provider_name(
                provider_name
            )
        )

        self._provider_factories.pop(
            normalized_name,
            None,
        )

    def is_registered(
        self,
        provider_name: str,
    ) -> bool:
        """
        Check whether a provider has been registered.
        """

        normalized_name = (
            self.normalize_provider_name(
                provider_name
            )
        )

        return (
            normalized_name
            in self._provider_factories
        )

    def list_providers(self) -> list[str]:
        """
        Return registered provider names.
        """

        return sorted(
            self._provider_factories.keys()
        )

    def create_provider(
        self,
        provider_name: str,
        **provider_options: Any,
    ) -> AIProvider:
        """
        Create a provider using its registered factory.
        """

        normalized_name = (
            self.normalize_provider_name(
                provider_name
            )
        )

        factory = self._provider_factories.get(
            normalized_name
        )

        if factory is None:
            registered = (
                ", ".join(self.list_providers())
                or "none"
            )

            raise AIProviderNotRegisteredError(
                "AI provider is not registered: "
                f"{normalized_name}. "
                f"Registered providers: {registered}"
            )

        try:
            provider = factory(
                **provider_options
            )
        except Exception as exc:
            raise AIProviderLoadError(
                "Failed to load AI provider "
                f"{normalized_name}: {exc}"
            ) from exc

        if not isinstance(
            provider,
            AIProvider,
        ):
            raise AIProviderLoadError(
                "Provider factory did not return "
                "an AIProvider instance for "
                f"{normalized_name}."
            )

        return provider