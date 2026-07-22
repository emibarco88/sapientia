"""
Module: enterprise_ai_engine.py

Purpose:
Provides Sapientia's central, provider-independent AI capability layer.

The engine depends only on the AIProvider contract and the provider
registry. It has no direct dependency on OpenAI or any other vendor.
"""

from __future__ import annotations

import json
import os
from typing import Any

from sapientia.engines.enterprise_ai.default_registry import (
    build_default_provider_registry,
)
from sapientia.engines.enterprise_ai.models import (
    AICapability,
    AIRequest,
    AIResponse,
)
from sapientia.engines.enterprise_ai.provider_registry import (
    AIProviderRegistry,
)
from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)


class EnterpriseAIEngine:
    """
    Central provider-independent AI façade used by Sapientia.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
        provider_name: str | None = None,
        provider_registry: (
            AIProviderRegistry | None
        ) = None,
        provider_options: (
            dict[str, Any] | None
        ) = None,
    ) -> None:
        """
        Initialise the Enterprise AI Engine.

        A concrete provider can be injected directly for testing.

        Otherwise, the configured provider is resolved lazily through
        the provider registry.
        """

        self.provider_registry = (
            provider_registry
            or build_default_provider_registry()
        )

        self.provider_name = (
            provider_name
            or os.getenv(
                "SAPIENTIA_AI_PROVIDER",
                "OPENAI",
            )
        ).strip().upper()

        self.provider_options = (
            provider_options or {}
        )

        self._provider = provider

    @property
    def provider(self) -> AIProvider:
        """
        Return the active provider.

        Provider creation is lazy, so provider SDKs are imported only
        when the first AI operation is executed.
        """

        if self._provider is None:
            self._provider = (
                self.provider_registry.create_provider(
                    provider_name=(
                        self.provider_name
                    ),
                    **self.provider_options,
                )
            )

        return self._provider

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
        model: str | None = None,
    ) -> AIResponse:
        """
        Answer an enterprise question using a grounded prompt.
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
                model=model,
                metadata=metadata or {},
            )
        )

    def summarise_document(
        self,
        document_text: str,
        document_title: str | None = None,
        max_output_tokens: int = 1200,
        model: str | None = None,
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
                model=model,
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
        model: str | None = None,
    ) -> AIResponse:
        """
        Extract candidate business rules from enterprise content.
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
                model=model,
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

        if response.structured_output is None:
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
        model: str | None = None,
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
                model=model,
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

        if response.structured_output is None:
            response.warnings.append(
                "The entity response could not "
                "be parsed as JSON."
            )

        return response

    @staticmethod
    def _parse_json_content(
        content: str,
    ) -> Any | None:
        """
        Parse model-returned JSON, including Markdown JSON fences.
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
                and lines[-1].strip() == "```"
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