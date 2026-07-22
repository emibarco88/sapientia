"""
Provider-independent AI request contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sapientia.runtime.ai.contracts.ai_runtime_context import (
    AIRuntimeContext,
)


@dataclass(slots=True)
class AIRequest:
    """
    Request submitted to the Sapientia AI Runtime.

    The request contains no OpenAI, Anthropic, Gemini or Azure-specific
    structures. A driver translates it into the target service's
    request format.
    """

    prompt: str
    runtime_context: AIRuntimeContext

    driver_name: str = "DEFAULT"
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
            self.runtime_context,
            AIRuntimeContext,
        ):
            raise TypeError(
                "runtime_context must be an "
                "AIRuntimeContext."
            )

        self.driver_name = str(
            self.driver_name or "DEFAULT"
        ).strip().upper()

        if not self.driver_name:
            self.driver_name = "DEFAULT"

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

        if self.response_format not in supported_formats:
            raise ValueError(
                "response_format must be TEXT or JSON."
            )

        if self.temperature is not None:
            if not isinstance(
                self.temperature,
                int | float,
            ):
                raise TypeError(
                    "temperature must be numeric."
                )

            if not 0 <= self.temperature <= 2:
                raise ValueError(
                    "temperature must be between 0 and 2."
                )

            self.temperature = float(
                self.temperature
            )

        if self.max_output_tokens is not None:
            if not isinstance(
                self.max_output_tokens,
                int,
            ):
                raise TypeError(
                    "max_output_tokens must be an integer."
                )

            if self.max_output_tokens <= 0:
                raise ValueError(
                    "max_output_tokens must be greater "
                    "than zero."
                )

        if self.timeout_seconds is not None:
            if not isinstance(
                self.timeout_seconds,
                int | float,
            ):
                raise TypeError(
                    "timeout_seconds must be numeric."
                )

            if self.timeout_seconds <= 0:
                raise ValueError(
                    "timeout_seconds must be greater "
                    "than zero."
                )

            self.timeout_seconds = float(
                self.timeout_seconds
            )

        self.metadata = dict(
            self.metadata or {}
        )

    @property
    def execution_id(self) -> str:
        """
        Return the execution ID from the runtime context.
        """

        return self.runtime_context.execution_id

    @property
    def correlation_id(self) -> str:
        """
        Return the correlation ID from the runtime context.
        """

        return self.runtime_context.correlation_id

    def to_dict(
        self,
        include_prompt: bool = True,
    ) -> dict[str, Any]:
        """
        Return an API-safe request representation.
        """

        result: dict[str, Any] = {
            "runtime_context":
                self.runtime_context.to_dict(),

            "driver_name":
                self.driver_name,

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