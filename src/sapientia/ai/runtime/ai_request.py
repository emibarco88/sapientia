"""
Module: ai_request.py

Purpose:
Defines the provider-independent request contract accepted by the
Sapientia AI Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sapientia.ai.runtime.ai_execution_context import (
    AIExecutionContext,
)


@dataclass(slots=True)
class AIRequest:
    """
    Provider-independent request submitted to the AI Runtime.

    The runtime will later translate this request into the format
    required by OpenAI, Azure OpenAI, Anthropic, Gemini or another
    provider.

    Attributes:
        prompt:
            Fully rendered prompt supplied to the model.

        execution_context:
            Traceability and business context for the request.

        provider:
            Logical provider identifier. The runtime may use this to
            choose the correct provider implementation.

        model:
            Optional model override.

        response_format:
            Expected response format, such as TEXT or JSON.

        temperature:
            Optional generation temperature.

        max_output_tokens:
            Optional maximum number of generated tokens.

        timeout_seconds:
            Optional provider execution timeout.

        metadata:
            Additional provider-independent request metadata.
    """

    prompt: str
    execution_context: AIExecutionContext

    provider: str = "DEFAULT"
    model: str | None = None

    response_format: str = "TEXT"

    temperature: float | None = None
    max_output_tokens: int | None = None
    timeout_seconds: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Normalise and validate the request.
        """

        self.prompt = str(
            self.prompt or ""
        ).strip()

        if not self.prompt:
            raise ValueError(
                "AI request prompt cannot be empty."
            )

        if not isinstance(
            self.execution_context,
            AIExecutionContext,
        ):
            raise TypeError(
                "execution_context must be an "
                "AIExecutionContext."
            )

        self.provider = str(
            self.provider or "DEFAULT"
        ).strip().upper()

        if not self.provider:
            self.provider = "DEFAULT"

        if self.model is not None:
            self.model = (
                str(self.model).strip()
                or None
            )

        self.response_format = str(
            self.response_format or "TEXT"
        ).strip().upper()

        supported_formats = {
            "TEXT",
            "JSON",
        }

        if (
            self.response_format
            not in supported_formats
        ):
            raise ValueError(
                "response_format must be TEXT or JSON."
            )

        if self.temperature is not None:
            if not 0 <= self.temperature <= 2:
                raise ValueError(
                    "temperature must be between 0 and 2."
                )

        if (
            self.max_output_tokens is not None
            and self.max_output_tokens <= 0
        ):
            raise ValueError(
                "max_output_tokens must be greater "
                "than zero."
            )

        if (
            self.timeout_seconds is not None
            and self.timeout_seconds <= 0
        ):
            raise ValueError(
                "timeout_seconds must be greater "
                "than zero."
            )

        self.metadata = dict(
            self.metadata or {}
        )

    def to_dict(
        self,
        include_prompt: bool = True,
    ) -> dict[str, Any]:
        """
        Return an API-safe request representation.

        The prompt can be excluded when logging request metadata to avoid
        persisting sensitive or excessively large content.
        """

        result: dict[str, Any] = {
            "execution_context":
                self.execution_context.to_dict(),

            "provider":
                self.provider,

            "model":
                self.model,

            "response_format":
                self.response_format,

            "temperature":
                self.temperature,

            "max_output_tokens":
                self.max_output_tokens,

            "timeout_seconds":
                self.timeout_seconds,

            "metadata":
                dict(self.metadata),
        }

        if include_prompt:
            result["prompt"] = self.prompt

        return result