"""
Module: enterprise_prompt.py

Purpose:
Defines Sapientia's provider-independent Enterprise Prompt contract.

An EnterprisePrompt is the structured interface between Enterprise
Context and the Enterprise AI Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EnterprisePrompt:
    """
    Structured prompt generated from Sapientia Enterprise Context.

    The model intentionally separates:

    - system instructions
    - user instructions
    - enterprise context
    - prompt metadata

    This allows prompt versioning, inspection, testing and future
    provider-specific rendering without changing the underlying
    Enterprise Context.
    """

    prompt_type: str
    prompt_version: str

    system_prompt: str
    user_prompt: str
    context_prompt: str

    project_id: int
    business_domain: str

    question: str | None = None

    estimated_input_tokens: int = 0
    included_evidence_count: int = 0
    excluded_evidence_count: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    warnings: list[str] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        self.prompt_type = str(
            self.prompt_type or ""
        ).strip().upper()

        self.prompt_version = str(
            self.prompt_version or ""
        ).strip()

        self.system_prompt = str(
            self.system_prompt or ""
        ).strip()

        self.user_prompt = str(
            self.user_prompt or ""
        ).strip()

        self.context_prompt = str(
            self.context_prompt or ""
        ).strip()

        self.business_domain = str(
            self.business_domain or ""
        ).strip().upper()

        if self.question is not None:
            self.question = str(
                self.question
            ).strip()

        if not self.prompt_type:
            raise ValueError(
                "Enterprise prompt type cannot be empty."
            )

        if not self.prompt_version:
            raise ValueError(
                "Enterprise prompt version cannot be empty."
            )

        if not self.system_prompt:
            raise ValueError(
                "Enterprise system prompt cannot be empty."
            )

        if not self.user_prompt:
            raise ValueError(
                "Enterprise user prompt cannot be empty."
            )

        if not self.context_prompt:
            raise ValueError(
                "Enterprise context prompt cannot be empty."
            )

        if self.project_id <= 0:
            raise ValueError(
                "project_id must be greater than zero."
            )

        if not self.business_domain:
            raise ValueError(
                "business_domain cannot be empty."
            )

    def render(self) -> str:
        """
        Render the complete prompt as a provider-independent string.

        Phase 4.4 can pass this output directly to:

            EnterpriseAIEngine.answer_question(...)
        """

        return "\n\n".join(
            [
                self.system_prompt,
                self.context_prompt,
                self.user_prompt,
            ]
        ).strip()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the prompt into an API-safe dictionary.
        """

        return {
            "prompt_type":
                self.prompt_type,

            "prompt_version":
                self.prompt_version,

            "system_prompt":
                self.system_prompt,

            "user_prompt":
                self.user_prompt,

            "context_prompt":
                self.context_prompt,

            "rendered_prompt":
                self.render(),

            "project_id":
                self.project_id,

            "business_domain":
                self.business_domain,

            "question":
                self.question,

            "estimated_input_tokens":
                self.estimated_input_tokens,

            "included_evidence_count":
                self.included_evidence_count,

            "excluded_evidence_count":
                self.excluded_evidence_count,

            "metadata":
                self.metadata,

            "warnings":
                self.warnings,
        }