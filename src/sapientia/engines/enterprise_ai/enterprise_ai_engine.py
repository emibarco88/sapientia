"""
Module: enterprise_ai_engine.py

Purpose:
Provides Sapientia's enterprise AI capability façade.

The public Enterprise AI interface remains stable while all production
AI execution is routed through the Sapientia AI Runtime.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

from sapientia.engines.enterprise_ai.models import (
    AICapability,
    AIRequest,
    AIResponse,
)
from sapientia.engines.enterprise_ai.providers.base import (
    AIProvider,
)
from sapientia.runtime.ai import (
    AIRuntime,
    AIRuntimeContext,
)
from sapientia.runtime.ai import (
    AIRequest as RuntimeAIRequest,
)
from sapientia.runtime.ai import (
    AIResponse as RuntimeAIResponse,
)


class EnterpriseAIEngine:
    """
    Compatibility façade between Sapientia business capabilities and
    the central AI Runtime.

    Existing callers continue using EnterpriseAIEngine while execution
    is delegated to AIRuntime.
    """

    def __init__(
        self,
        runtime: AIRuntime | None = None,
        driver_name: str | None = None,
        provider: AIProvider | None = None,
        provider_name: str | None = None,
        provider_registry: Any | None = None,
        provider_options: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialise the Enterprise AI Engine.

        Parameters retained from the previous provider-based
        implementation remain accepted temporarily for compatibility.

        A legacy provider may still be injected by existing unit tests,
        but all normal production execution uses AIRuntime.
        """

        self.runtime = (
            runtime
            or AIRuntime()
        )

        self.driver_name = str(
            driver_name
            or provider_name
            or os.getenv(
                "SAPIENTIA_AI_DRIVER",
                os.getenv(
                    "SAPIENTIA_AI_PROVIDER",
                    "OPENAI",
                ),
            )
        ).strip().upper()

        if not self.driver_name:
            self.driver_name = "OPENAI"

        self._legacy_provider = provider

        # Retained temporarily to avoid breaking callers which inspect
        # these attributes. They are no longer used in production.
        self.provider_registry = provider_registry
        self.provider_options = (
            provider_options or {}
        )
        self.provider_name = self.driver_name

    @property
    def provider(self) -> AIProvider | None:
        """
        Return an explicitly injected legacy provider, when present.

        Production code should use AIRuntime rather than this property.
        """

        return self._legacy_provider

    def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Execute an Enterprise AI request through AIRuntime.
        """

        if not isinstance(
            request,
            AIRequest,
        ):
            raise TypeError(
                "request must be an Enterprise AIRequest."
            )

        # Temporary compatibility path for existing tests that inject
        # a mock implementation of the previous AIProvider contract.
        if self._legacy_provider is not None:
            return self._legacy_provider.generate(
                request
            )

        runtime_context = (
            self._build_runtime_context(
                request
            )
        )

        runtime_request = RuntimeAIRequest(
            prompt=request.prompt,
            runtime_context=runtime_context,
            driver_name=self.driver_name,
            model=request.model,
            response_format=(
                "JSON"
                if request.capability
                in {
                    AICapability.EXTRACT_BUSINESS_RULES,
                    AICapability.EXTRACT_ENTITIES,
                }
                else "TEXT"
            ),
            temperature=request.temperature,
            max_output_tokens=(
                request.max_output_tokens
            ),
            metadata={
                **dict(
                    request.metadata
                    or {}
                ),
                "enterprise_ai_capability":
                    request.capability.value,
            },
        )

        runtime_response = (
            self.runtime.execute(
                runtime_request
            )
        )

        return self._map_runtime_response(
            request=request,
            runtime_response=runtime_response,
        )

    def answer_question(
        self,
        prompt: str,
        max_output_tokens: int = 1200,
        metadata: dict[str, Any] | None = None,
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
        metadata: dict[str, Any] | None = None,
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
                    **dict(
                        metadata
                        or {}
                    ),
                    "document_title":
                        title,
                },
            )
        )

    def extract_business_rules(
        self,
        document_text: str,
        document_title: str | None = None,
        max_output_tokens: int = 1800,
        model: str | None = None,
        metadata: dict[str, Any] | None = None,
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
                    **dict(
                        metadata
                        or {}
                    ),
                    "document_title":
                        title,
                },
            )
        )

        if response.structured_output is None:
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
        metadata: dict[str, Any] | None = None,
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
                    **dict(
                        metadata
                        or {}
                    ),
                    "document_title":
                        title,
                },
            )
        )

        if response.structured_output is None:
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
    def _build_runtime_context(
        request: AIRequest,
    ) -> AIRuntimeContext:
        """
        Create runtime traceability context from Enterprise AI metadata.
        """

        metadata = dict(
            request.metadata
            or {}
        )

        raw_project_id = (
            metadata.get("project_id")
            or metadata.get(
                "sapientia_project_id"
            )
            or 1
        )

        try:
            project_id = int(
                raw_project_id
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Enterprise AI metadata contains "
                "an invalid project_id."
            ) from exc

        if project_id <= 0:
            raise ValueError(
                "Enterprise AI project_id must "
                "be greater than zero."
            )

        business_domain = str(
            metadata.get(
                "business_domain"
            )
            or metadata.get(
                "sapientia_business_domain"
            )
            or "ENTERPRISE"
        ).strip().upper()

        capability = str(
            metadata.get(
                "sapientia_capability"
            )
            or "ENTERPRISE_AI"
        ).strip().upper()

        return AIRuntimeContext(
            project_id=project_id,
            business_domain=business_domain,
            capability=capability,
            operation=request.capability.value,
            initiated_by=str(
                metadata.get(
                    "initiated_by"
                )
                or "ENTERPRISE_AI_ENGINE"
            ),
            workflow_id=(
                str(
                    metadata.get(
                        "workflow_id"
                    )
                ).strip()
                if metadata.get(
                    "workflow_id"
                )
                is not None
                else None
            ),
            metadata={
                **metadata,
                "enterprise_ai_capability":
                    request.capability.value,
            },
        )

    @staticmethod
    def _map_runtime_response(
        request: AIRequest,
        runtime_response: RuntimeAIResponse,
    ) -> AIResponse:
        """
        Map the Runtime response to the existing Enterprise AI model.
        """

        if not isinstance(
            runtime_response,
            RuntimeAIResponse,
        ):
            raise TypeError(
                "AIRuntime returned an invalid "
                "response type."
            )

        estimated_cost = (
            float(
                runtime_response
                .usage
                .estimated_cost
            )
            if runtime_response
            .usage
            .estimated_cost
            is not None
            else None
        )

        provider_metadata = {
            **dict(
                runtime_response.metadata
                or {}
            ),
            "execution_id":
                runtime_response.execution_id,
            "finish_reason":
                runtime_response.finish_reason,
            "created_at":
                runtime_response
                .created_at
                .isoformat(),
            "currency":
                runtime_response
                .usage
                .currency,
            "cached_input_tokens":
                runtime_response
                .usage
                .cached_input_tokens,
            "reasoning_tokens":
                runtime_response
                .usage
                .reasoning_tokens,
        }

        return AIResponse(
            success=True,
            capability=request.capability,
            provider=runtime_response.driver,
            model=runtime_response.model,
            content=runtime_response.content,
            response_id=(
                runtime_response
                .external_request_id
            ),
            structured_output=(
                runtime_response
                .parsed_content
            ),
            input_tokens=(
                runtime_response
                .usage
                .input_tokens
            ),
            output_tokens=(
                runtime_response
                .usage
                .output_tokens
            ),
            total_tokens=(
                runtime_response
                .usage
                .total_tokens
            ),
            execution_time_ms=(
                runtime_response
                .latency_ms
            ),
            estimated_cost=estimated_cost,
            metadata=provider_metadata,
            warnings=list(
                runtime_response.warnings
                or []
            ),
            errors=[],
            raw_response=(
                runtime_response.to_dict()
            ),
        )

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