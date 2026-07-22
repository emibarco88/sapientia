"""
Module: ai_response.py

Purpose:
Defines the provider-independent response returned by the Sapientia
AI Runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sapientia.ai.runtime.ai_usage import (
    AIUsage,
)


@dataclass(slots=True)
class AIResponse:
    """
    Provider-independent response returned by the AI Runtime.

    The response retains both the generated content and the information
    needed for traceability, observability and future cost management.
    """

    execution_id: str
    provider: str
    model: str
    content: str

    usage: AIUsage = field(
        default_factory=AIUsage
    )

    finish_reason: str | None = None
    provider_request_id: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    latency_ms: int | None = None

    parsed_content: Any | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        """
        Normalise and validate the response.
        """

        self.execution_id = str(
            self.execution_id or ""
        ).strip()

        if not self.execution_id:
            raise ValueError(
                "execution_id cannot be empty."
            )

        self.provider = str(
            self.provider or ""
        ).strip().upper()

        if not self.provider:
            raise ValueError(
                "provider cannot be empty."
            )

        self.model = str(
            self.model or ""
        ).strip()

        if not self.model:
            raise ValueError(
                "model cannot be empty."
            )

        self.content = str(
            self.content or ""
        ).strip()

        if not self.content:
            raise ValueError(
                "AI response content cannot be empty."
            )

        if not isinstance(
            self.usage,
            AIUsage,
        ):
            raise TypeError(
                "usage must be an AIUsage instance."
            )

        if self.finish_reason is not None:
            self.finish_reason = (
                str(self.finish_reason).strip()
                or None
            )

        if self.provider_request_id is not None:
            self.provider_request_id = (
                str(
                    self.provider_request_id
                ).strip()
                or None
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        if (
            self.latency_ms is not None
            and self.latency_ms < 0
        ):
            raise ValueError(
                "latency_ms cannot be negative."
            )

        self.metadata = dict(
            self.metadata or {}
        )

        self.warnings = [
            str(warning).strip()
            for warning in (
                self.warnings or []
            )
            if str(warning).strip()
        ]

    @property
    def has_parsed_content(self) -> bool:
        """
        Indicate whether structured content has been parsed.
        """

        return self.parsed_content is not None

    def to_dict(self) -> dict[str, Any]:
        """
        Return an API-safe response representation.
        """

        return {
            "execution_id":
                self.execution_id,

            "provider":
                self.provider,

            "model":
                self.model,

            "content":
                self.content,

            "parsed_content":
                self.parsed_content,

            "has_parsed_content":
                self.has_parsed_content,

            "usage":
                self.usage.to_dict(),

            "finish_reason":
                self.finish_reason,

            "provider_request_id":
                self.provider_request_id,

            "created_at":
                self.created_at.isoformat(),

            "latency_ms":
                self.latency_ms,

            "metadata":
                dict(self.metadata),

            "warnings":
                list(self.warnings),
        }