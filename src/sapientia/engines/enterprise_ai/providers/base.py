"""
Module: base.py

Purpose:
Defines the provider-independent contract used by Sapientia's
Enterprise AI Engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sapientia.engines.enterprise_ai.models import (
    AIRequest,
    AIResponse,
)


class AIProvider(ABC):
    """
    Contract implemented by all Enterprise AI providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider identifier.
        """

    @abstractmethod
    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Execute an AI generation request.
        """