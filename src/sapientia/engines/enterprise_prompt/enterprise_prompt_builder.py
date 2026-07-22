"""
Module: enterprise_prompt_builder.py

Purpose:
Transforms Sapientia Enterprise Context into a structured,
provider-independent Enterprise Prompt.

The builder:

- contains no database logic
- contains no provider-specific AI logic
- does not call an LLM
- curates and limits Enterprise Context
- preserves evidence provenance
- produces deterministic prompt output
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from sapientia.models.enterprise_context import (
    EnterpriseContext,
)
from sapientia.models.enterprise_prompt import (
    EnterprisePrompt,
)


class EnterprisePromptBuilder:
    """
    Builds grounded Enterprise AI prompts from Enterprise Context.
    """

    PROMPT_VERSION = "1.0"

    DEFAULT_MAX_DATASETS = 30
    DEFAULT_MAX_CONCEPTS = 40
    DEFAULT_MAX_KNOWLEDGE_ITEMS = 40
    DEFAULT_MAX_RELATIONSHIPS = 50
    DEFAULT_MAX_EVIDENCE = 60

    def build_question_prompt(
        self,
        context: EnterpriseContext,
        question: str,
        max_evidence: int | None = None,
    ) -> EnterprisePrompt:
        """
        Build an evidence-grounded question-answering prompt.

        This prompt is intended for use by Sapientia AI Advisor and
        future enterprise reasoning capabilities.
        """

        normalized_question = str(
            question or ""
        ).strip()

        if not normalized_question:
            raise ValueError(
                "A question is required."
            )

        context_payload = (
            self._build_context_payload(
                context=context,
                max_evidence=max_evidence,
            )
        )

        system_prompt = (
            self._build_system_prompt()
        )

        context_prompt = (
            self._render_context_prompt(
                payload=context_payload[
                    "payload"
                ]
            )
        )

        user_prompt = (
            self._build_user_prompt(
                question=normalized_question
            )
        )

        rendered_prompt = "\n\n".join(
            [
                system_prompt,
                context_prompt,
                user_prompt,
            ]
        )

        warnings = list(
            context_payload["warnings"]
        )

        if (
            context_payload[
                "included_evidence_count"
            ]
            == 0
        ):
            warnings.append(
                "No evidence records were included in "
                "the Enterprise Prompt."
            )

        return EnterprisePrompt(
            prompt_type=(
                "ENTERPRISE_QUESTION"
            ),

            prompt_version=(
                self.PROMPT_VERSION
            ),

            system_prompt=system_prompt,

            user_prompt=user_prompt,

            context_prompt=context_prompt,

            project_id=context.project_id,

            business_domain=(
                context.business_domain
            ),

            question=normalized_question,

            estimated_input_tokens=(
                self._estimate_tokens(
                    rendered_prompt
                )
            ),

            included_evidence_count=(
                context_payload[
                    "included_evidence_count"
                ]
            ),

            excluded_evidence_count=(
                context_payload[
                    "excluded_evidence_count"
                ]
            ),

            metadata={
                "builder":
                    self.__class__.__name__,

                "dataset_count":
                    context_payload[
                        "dataset_count"
                    ],

                "concept_count":
                    context_payload[
                        "concept_count"
                    ],

                "knowledge_item_count":
                    context_payload[
                        "knowledge_item_count"
                    ],

                "relationship_count":
                    context_payload[
                        "relationship_count"
                    ],

                "context_statistics":
                    self._extract_statistics(
                        context
                    ),

                "grounding_required":
                    True,

                "external_knowledge_allowed":
                    False,
            },

            warnings=warnings,
        )

    def build_assessment_prompt(
        self,
        context: EnterpriseContext,
        assessment_objective: str | None = None,
        max_evidence: int | None = None,
    ) -> EnterprisePrompt:
        """
        Build a prompt for a structured enterprise assessment.

        The resulting prompt can be used by the Enterprise Intelligence
        AI Engine introduced in Phase 4.4.
        """

        objective = str(
            assessment_objective
            or (
                "Assess the current enterprise understanding, "
                "identify material observations, risks, knowledge "
                "gaps and recommended next actions."
            )
        ).strip()

        context_payload = (
            self._build_context_payload(
                context=context,
                max_evidence=max_evidence,
            )
        )

        system_prompt = (
            self._build_system_prompt()
        )

        context_prompt = (
            self._render_context_prompt(
                payload=context_payload[
                    "payload"
                ]
            )
        )

        user_prompt = f"""
ASSESSMENT OBJECTIVE

{objective}

Return valid JSON using this structure:

{{
  "executive_summary": "Business-level summary",
  "observations": [
    {{
      "title": "Observation title",
      "description": "Evidence-grounded observation",
      "business_impact": "Why the observation matters",
      "confidence": 0.0,
      "supporting_evidence": [
        "Evidence title or source"
      ]
    }}
  ],
  "risks": [
    {{
      "title": "Risk title",
      "description": "Evidence-grounded risk",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "confidence": 0.0,
      "supporting_evidence": [
        "Evidence title or source"
      ]
    }}
  ],
  "recommendations": [
    {{
      "title": "Recommendation title",
      "description": "Recommended action",
      "priority": "LOW|MEDIUM|HIGH",
      "rationale": "Why this action is recommended"
    }}
  ],
  "knowledge_gaps": [
    {{
      "missing_information": "Information not currently available",
      "reason_required": "Why Sapientia needs it",
      "suggested_source": "Potential source or null"
    }}
  ],
  "confidence": 0.0
}}

Rules:

1. Return JSON only.
2. Use only the supplied Enterprise Context.
3. Do not invent risks, controls, thresholds or business rules.
4. Every material observation and risk must be traceable to supplied
   evidence.
5. Clearly identify missing information.
6. Confidence values must be between 0 and 1.
""".strip()

        rendered_prompt = "\n\n".join(
            [
                system_prompt,
                context_prompt,
                user_prompt,
            ]
        )

        return EnterprisePrompt(
            prompt_type=(
                "ENTERPRISE_ASSESSMENT"
            ),

            prompt_version=(
                self.PROMPT_VERSION
            ),

            system_prompt=system_prompt,

            user_prompt=user_prompt,

            context_prompt=context_prompt,

            project_id=context.project_id,

            business_domain=(
                context.business_domain
            ),

            question=None,

            estimated_input_tokens=(
                self._estimate_tokens(
                    rendered_prompt
                )
            ),

            included_evidence_count=(
                context_payload[
                    "included_evidence_count"
                ]
            ),

            excluded_evidence_count=(
                context_payload[
                    "excluded_evidence_count"
                ]
            ),

            metadata={
                "builder":
                    self.__class__.__name__,

                "assessment_objective":
                    objective,

                "dataset_count":
                    context_payload[
                        "dataset_count"
                    ],

                "concept_count":
                    context_payload[
                        "concept_count"
                    ],

                "knowledge_item_count":
                    context_payload[
                        "knowledge_item_count"
                    ],

                "relationship_count":
                    context_payload[
                        "relationship_count"
                    ],

                "context_statistics":
                    self._extract_statistics(
                        context
                    ),

                "expected_response_format":
                    "JSON",

                "grounding_required":
                    True,

                "external_knowledge_allowed":
                    False,
            },

            warnings=list(
                context_payload["warnings"]
            ),
        )

    def _build_context_payload(
        self,
        context: EnterpriseContext,
        max_evidence: int | None,
    ) -> dict[str, Any]:
        """
        Convert Enterprise Context into a bounded AI-ready payload.
        """

        if not isinstance(
            context,
            EnterpriseContext,
        ):
            raise TypeError(
                "context must be an EnterpriseContext."
            )

        evidence_limit = (
            max_evidence
            if max_evidence is not None
            else self.DEFAULT_MAX_EVIDENCE
        )

        if evidence_limit < 0:
            raise ValueError(
                "max_evidence cannot be negative."
            )

        all_datasets = list(
            context.datasets or []
        )

        all_concepts = list(
            context.concepts or []
        )

        all_knowledge_items = list(
            context.knowledge_items or []
        )

        all_relationships = list(
            context.relationships or []
        )

        all_evidence = list(
            context.evidence or []
        )

        datasets = all_datasets[
            :self.DEFAULT_MAX_DATASETS
        ]

        concepts = all_concepts[
            :self.DEFAULT_MAX_CONCEPTS
        ]

        knowledge_items = (
            all_knowledge_items[
                :self.DEFAULT_MAX_KNOWLEDGE_ITEMS
            ]
        )

        relationships = (
            all_relationships[
                :self.DEFAULT_MAX_RELATIONSHIPS
            ]
        )

        evidence = all_evidence[
            :evidence_limit
        ]

        warnings: list[str] = []

        self._append_truncation_warning(
            warnings=warnings,
            object_name="datasets",
            total=len(all_datasets),
            included=len(datasets),
        )

        self._append_truncation_warning(
            warnings=warnings,
            object_name="concepts",
            total=len(all_concepts),
            included=len(concepts),
        )

        self._append_truncation_warning(
            warnings=warnings,
            object_name="knowledge items",
            total=len(all_knowledge_items),
            included=len(knowledge_items),
        )

        self._append_truncation_warning(
            warnings=warnings,
            object_name="relationships",
            total=len(all_relationships),
            included=len(relationships),
        )

        self._append_truncation_warning(
            warnings=warnings,
            object_name="evidence records",
            total=len(all_evidence),
            included=len(evidence),
        )

        payload = {
            "enterprise_context": {
                "project_id":
                    context.project_id,

                "business_domain":
                    context.business_domain,

                "datasets": [
                    self._serialise_item(
                        item
                    )
                    for item in datasets
                ],

                "enterprise_concepts": [
                    self._serialise_item(
                        item
                    )
                    for item in concepts
                ],

                "knowledge_items": [
                    self._serialise_item(
                        item
                    )
                    for item in knowledge_items
                ],

                "relationships": [
                    self._serialise_item(
                        item
                    )
                    for item in relationships
                ],

                "evidence": [
                    self._serialise_item(
                        item
                    )
                    for item in evidence
                ],

                "metadata":
                    self._safe_metadata(
                        context.metadata
                    ),
            }
        }

        return {
            "payload":
                payload,

            "dataset_count":
                len(datasets),

            "concept_count":
                len(concepts),

            "knowledge_item_count":
                len(knowledge_items),

            "relationship_count":
                len(relationships),

            "included_evidence_count":
                len(evidence),

            "excluded_evidence_count":
                max(
                    0,
                    len(all_evidence)
                    - len(evidence),
                ),

            "warnings":
                warnings,
        }

    @staticmethod
    def _build_system_prompt() -> str:
        """
        Define Sapientia's stable grounding contract.
        """

        return """
You are Sapientia Enterprise Intelligence.

Your role is to explain how an enterprise operates using Sapientia's
evidence-backed Enterprise Context.

GROUNDING CONTRACT

1. Use only the Enterprise Context supplied in this prompt.
2. Do not introduce external facts, assumptions or industry rules.
3. Do not invent business policies, thresholds, controls or decisions.
4. Treat evidence records as the primary source of truth.
5. Treat enterprise concepts as consolidated interpretations supported
   by evidence, not as independent source facts.
6. Treat relationships as discovered or inferred connections and
   respect their available confidence and reasoning.
7. Distinguish source evidence from Sapientia-generated interpretation.
8. When evidence is missing, incomplete or contradictory, explicitly
   state the limitation.
9. Prefer business language over database or implementation language.
10. Never claim certainty beyond the supplied evidence.
""".strip()

    @staticmethod
    def _build_user_prompt(
        question: str,
    ) -> str:
        return f"""
USER QUESTION

{question}

RESPONSE INSTRUCTIONS

1. Answer the question directly.
2. Explain the relevant business meaning.
3. Identify the evidence supporting the answer.
4. Mention uncertainty or missing information.
5. Do not expose unnecessary implementation metadata.
6. Use clear headings when they improve readability.
""".strip()

    @staticmethod
    def _render_context_prompt(
        payload: dict[str, Any],
    ) -> str:
        context_json = json.dumps(
            payload,
            indent=2,
            default=str,
            ensure_ascii=False,
        )

        return f"""
SAPIENTIA ENTERPRISE CONTEXT

The following JSON contains the curated Enterprise Context available
for this request.

{context_json}
""".strip()

    @staticmethod
    def _serialise_item(
        item: Any,
    ) -> dict[str, Any]:
        """
        Serialise dataclasses and dictionary-compatible context items.
        """

        if is_dataclass(item):
            return asdict(item)

        if isinstance(item, dict):
            return dict(item)

        if hasattr(item, "to_dict"):
            result = item.to_dict()

            if isinstance(result, dict):
                return result

        raise TypeError(
            "Enterprise Context contains an "
            f"unsupported item type: {type(item).__name__}"
        )

    @staticmethod
    def _safe_metadata(
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Keep metadata serialisable and exclude raw oversized objects
        that are already represented elsewhere in the prompt.
        """

        source = dict(
            metadata or {}
        )

        excluded_keys = {
            "semantic_columns",
            "intelligence_links",
            "lineage",
        }

        return {
            key: value
            for key, value in source.items()
            if key not in excluded_keys
        }

    @staticmethod
    def _extract_statistics(
        context: EnterpriseContext,
    ) -> dict[str, Any]:
        metadata = dict(
            context.metadata or {}
        )

        statistics = metadata.get(
            "statistics"
        )

        if isinstance(
            statistics,
            dict,
        ):
            return dict(statistics)

        return {
            "datasets":
                len(context.datasets or []),

            "concepts":
                len(context.concepts or []),

            "knowledge_items":
                len(
                    context.knowledge_items
                    or []
                ),

            "relationships":
                len(
                    context.relationships
                    or []
                ),

            "evidence":
                len(context.evidence or []),
        }

    @staticmethod
    def _append_truncation_warning(
        warnings: list[str],
        object_name: str,
        total: int,
        included: int,
    ) -> None:
        if total > included:
            warnings.append(
                f"Enterprise Context contained "
                f"{total} {object_name}; "
                f"{included} were included in the prompt."
            )

    @staticmethod
    def _estimate_tokens(
        text: str,
    ) -> int:
        """
        Estimate input tokens without depending on a provider-specific
        tokenizer.

        The estimate uses approximately four characters per token.
        Provider-reported token usage remains authoritative.
        """

        normalized = str(
            text or ""
        )

        if not normalized:
            return 0

        return max(
            1,
            round(
                len(normalized) / 4
            ),
        )