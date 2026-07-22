"""
Module: enterprise_ai_engine.py

Purpose:
Provides a central, provider-independent AI capability layer for
Sapientia.

All Sapientia engines should call this component rather than invoking
OpenAI or another model provider directly.
"""

from __future__ import annotations

import json
from typing import Any

from sapientia.engines.enterprise_ai.models import (
    AICapability,
    AIRequest,
    AIResponse,
)
from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)
from sapientia.engines.enterprise_ai.providers.openai_provider import (
    OpenAIProvider,
)


class EnterpriseAIEngine:
    """
    Central AI façade used by Sapientia.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
    ) -> None:
        self.provider = (
            provider
            or OpenAIProvider()
        )

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Execute a provider-independent AI request.
        """

        return self.provider.generate(
            request
        )

    def answer_question(
        self,
        prompt: str,
        max_output_tokens: int = 1200,
        metadata: (
            dict[str, Any] | None
        ) = None,
    ) -> AIResponse:
        """
        Answer an enterprise question using a completed grounded prompt.
        """

        return self.generate(
            AIRequest(
                capability=(
                    AICapability.ANSWER_QUESTION
                ),
                prompt=prompt,
                max_output_tokens=(
                    max_output_tokens
                ),
                metadata=metadata or {},
            )
        )

    def summarise_document(
        self,
        document_text: str,
        document_title: str | None = None,
        max_output_tokens: int = 1200,
    ) -> AIResponse:
        """
        Generate an enterprise-focused document summary.
        """

        title = (
            document_title
            or "Untitled enterprise document"
        )

        prompt = f"""
You are Sapientia Enterprise AI.

Summarise the supplied enterprise document.

Instructions:

1. Use only the supplied document text.
2. Identify the document's purpose.
3. Identify the main business topics.
4. Identify important obligations, controls, decisions or procedures.
5. Identify key definitions and thresholds when present.
6. Do not invent missing information.
7. Clearly identify uncertainty caused by incomplete text.
8. Produce a concise but useful enterprise summary.

Document title:
{title}

Document text:
{document_text}

Summary:
""".strip()

        return self.generate(
            AIRequest(
                capability=(
                    AICapability.SUMMARISE_DOCUMENT
                ),
                prompt=prompt,
                max_output_tokens=(
                    max_output_tokens
                ),
                metadata={
                    "document_title": title,
                },
            )
        )

    def extract_business_rules(
        self,
        document_text: str,
        document_title: str | None = None,
        max_output_tokens: int = 1800,
    ) -> AIResponse:
        """
        Extract candidate business rules from enterprise content.

        The response is requested as JSON text. Formal structured-output
        enforcement will be added in the next iteration.
        """

        title = (
            document_title
            or "Untitled enterprise document"
        )

        prompt = f"""
You are Sapientia Enterprise AI.

Extract explicit business rules from the supplied enterprise document.

Return valid JSON using this structure:

{{
  "business_rules": [
    {{
      "rule_name": "Short rule name",
      "rule_description": "What the rule requires",
      "rule_type": "APPROVAL|THRESHOLD|VALIDATION|CONTROL|PROCESS|OTHER",
      "condition": "When the rule applies",
      "required_action": "What must happen",
      "exception": "Any stated exception or null",
      "evidence_text": "Supporting source wording",
      "confidence": 0.0
    }}
  ]
}}

Rules:

1. Use only the supplied document.
2. Extract only rules supported by explicit evidence.
3. Do not invent thresholds or obligations.
4. Use confidence values between 0 and 1.
5. Return an empty business_rules list when no rule is supported.
6. Return JSON only.

Document title:
{title}

Document text:
{document_text}
""".strip()

        response = self.generate(
            AIRequest(
                capability=(
                    AICapability.EXTRACT_BUSINESS_RULES
                ),
                prompt=prompt,
                max_output_tokens=(
                    max_output_tokens
                ),
                metadata={
                    "document_title": title,
                },
            )
        )

        response.structured_output = (
            self._parse_json_content(
                response.content
            )
        )

        if (
            response.structured_output
            is None
        ):
            response.warnings.append(
                "The business-rule response "
                "could not be parsed as JSON."
            )

        return response

    def extract_entities(
        self,
        document_text: str,
        document_title: str | None = None,
        max_output_tokens: int = 1600,
    ) -> AIResponse:
        """
        Extract enterprise entities from document content.
        """

        title = (
            document_title
            or "Untitled enterprise document"
        )

        prompt = f"""
You are Sapientia Enterprise AI.

Extract enterprise entities from the supplied document.

Return valid JSON using this structure:

{{
  "entities": [
    {{
      "entity_name": "Name",
      "entity_type": "ORGANISATION|ROLE|SYSTEM|PROCESS|KPI|ACCOUNT|PRODUCT|LOCATION|OTHER",
      "description": "Meaning in this document",
      "evidence_text": "Supporting document wording",
      "confidence": 0.0
    }}
  ]
}}

Rules:

1. Use only the supplied document.
2. Do not invent entities.
3. Merge obvious duplicates.
4. Use confidence values between 0 and 1.
5. Return JSON only.

Document title:
{title}

Document text:
{document_text}
""".strip()

        response = self.generate(
            AIRequest(
                capability=(
                    AICapability.EXTRACT_ENTITIES
                ),
                prompt=prompt,
                max_output_tokens=(
                    max_output_tokens
                ),
                metadata={
                    "document_title": title,
                },
            )
        )

        response.structured_output = (
            self._parse_json_content(
                response.content
            )
        )

        if (
            response.structured_output
            is None
        ):
            response.warnings.append(
                "The entity response could "
                "not be parsed as JSON."
            )

        return response

    @staticmethod
    def _parse_json_content(
        content: str,
    ) -> Any | None:
        """
        Parse JSON returned by the model, including responses enclosed
        in Markdown JSON fences.
        """

        normalized = str(
            content or ""
        ).strip()

        if normalized.startswith("```"):
            lines = normalized.splitlines()

            if lines:
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip()
                == "```"
            ):
                lines = lines[:-1]

            normalized = "\n".join(
                lines
            ).strip()

        try:
            return json.loads(
                normalized
            )
        except json.JSONDecodeError:
            return None