"""
Module: models.py

Purpose:
Defines provider-independent request and response models for Sapientia's
Enterprise AI Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AICapability(str, Enum):
    """
    AI capabilities supported by the Enterprise AI Engine.
    """

    ANSWER_QUESTION = "ANSWER_QUESTION"
    SUMMARISE_DOCUMENT = "SUMMARISE_DOCUMENT"
    EXTRACT_BUSINESS_RULES = "EXTRACT_BUSINESS_RULES"
    EXTRACT_ENTITIES = "EXTRACT_ENTITIES"
    CLASSIFY_SEMANTICS = "CLASSIFY_SEMANTICS"
    DISCOVER_RELATIONSHIPS = "DISCOVER_RELATIONSHIPS"
    VALIDATE_CONCEPTS = "VALIDATE_CONCEPTS"


@dataclass(slots=True)
class AIRequest:
    """
    Provider-independent request sent to an AI provider.
    """

    capability: AICapability
    prompt: str
    max_output_tokens: int = 1200
    model: str | None = None
    temperature: float | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.prompt = str(self.prompt or "").strip()

        if not self.prompt:
            raise ValueError(
                "AI request prompt cannot be empty."
            )

        if self.max_output_tokens <= 0:
            raise ValueError(
                "max_output_tokens must be greater than zero."
            )


@dataclass(slots=True)
class AIResponse:
    """
    Standard response returned by every Enterprise AI operation.
    """

    success: bool
    capability: AICapability
    provider: str
    model: str
    content: str

    response_id: str | None = None
    structured_output: Any | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None

    execution_time_ms: int | None = None

    confidence: float | None = None
    estimated_cost: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    raw_response: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the response into a serialisable dictionary.
        """

        return {
            "success": self.success,
            "capability": self.capability.value,
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "response_id": self.response_id,
            "structured_output": self.structured_output,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "execution_time_ms": self.execution_time_ms,
            "confidence": self.confidence,
            "estimated_cost": self.estimated_cost,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "raw_response": self.raw_response,
        }