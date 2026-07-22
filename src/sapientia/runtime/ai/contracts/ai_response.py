"""
Provider-independent AI response contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sapientia.runtime.ai.contracts.ai_usage import (
    AIUsage,
)


@dataclass(slots=True)
class AIResponse:
    """
    Response returned by the Sapientia AI Runtime.

    The response retains generated content together with usage,
    traceability, latency and provider metadata.
    """

    execution_id: str
    driver: str
    model: str
    content: str

    usage: AIUsage = field(
        default_factory=AIUsage
    )

    finish_reason: str | None = None
    external_request_id: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
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

        self.driver = str(
            self.driver or ""
        ).strip().upper()

        if not self.driver:
            raise ValueError(
                "driver cannot be empty."
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

        if self.external_request_id is not None:
            self.external_request_id = (
                str(self.external_request_id).strip()
                or None
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be a datetime."
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware."
            )

        if self.latency_ms is not None:
            if not isinstance(self.latency_ms, int):
                raise TypeError(
                    "latency_ms must be an integer."
                )

            if self.latency_ms < 0:
                raise ValueError(
                    "latency_ms cannot be negative."
                )

        self.metadata = dict(
            self.metadata or {}
        )

        self.warnings = [
            str(warning).strip()
            for warning in self.warnings or []
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
        Return an API-safe dictionary representation.
        """

        return {
            "execution_id": self.execution_id,
            "driver": self.driver,
            "model": self.model,
            "content": self.content,
            "parsed_content": self.parsed_content,
            "has_parsed_content": self.has_parsed_content,
            "usage": self.usage.to_dict(),
            "finish_reason": self.finish_reason,
            "external_request_id": self.external_request_id,
            "created_at": self.created_at.isoformat(),
            "latency_ms": self.latency_ms,
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
        }