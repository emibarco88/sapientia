"""
Module: ai_advisor_engine.py

Purpose:
Answers enterprise questions using evidence retrieved from Sapientia's
Enterprise Knowledge Repository and Enterprise Intelligence layer.

All AI generation is executed through the provider-independent
EnterpriseAIEngine.
"""

from __future__ import annotations

from typing import Any

from sapientia.db.connection import get_engine
from sapientia.engines.ai_advisor.prompt_builder import (
    AIAdvisorPromptBuilder,
)
from sapientia.engines.context_retrieval.context_retrieval_engine import (
    ContextRetrievalEngine,
)
from sapientia.engines.enterprise_ai import (
    AIResponse,
    EnterpriseAIEngine,
)
from sapientia.repositories.intelligence.ai_advisor_repository import (
    AIAdvisorRepository,
)


class AIAdvisorEngine:
    """
    Coordinates enterprise context retrieval, prompt construction,
    provider-independent AI generation and response persistence.
    """

    def __init__(
        self,
        prompt_builder: AIAdvisorPromptBuilder | None = None,
        ai_engine: EnterpriseAIEngine | None = None,
        context_retrieval_engine: ContextRetrievalEngine | None = None,
    ) -> None:
        """
        Initialise the AI Advisor Engine.

        Dependencies may be injected for testing. When omitted,
        production defaults are created.
        """

        self.prompt_builder = (
            prompt_builder
            or AIAdvisorPromptBuilder()
        )

        self.ai_engine = (
            ai_engine
            or EnterpriseAIEngine()
        )

        self.context_retrieval_engine = (
            context_retrieval_engine
            or ContextRetrievalEngine()
        )

    def ask_domain_question(
        self,
        project_id: int,
        business_domain: str,
        question: str,
        persist: bool = True,
    ) -> dict[str, Any]:
        """
        Answer a business-domain question using focused Sapientia
        Enterprise Knowledge and Enterprise Intelligence evidence.

        Parameters
        ----------
        project_id:
            Sapientia project identifier.

        business_domain:
            Business-domain code, for example FINANCE.

        question:
            Natural-language enterprise question.

        persist:
            Whether to persist the generated Advisor response.

        Returns
        -------
        dict[str, Any]
            Provider-independent AI Advisor response and retrieval
            metadata.
        """

        normalized_project_id = self._normalize_project_id(
            project_id
        )

        normalized_domain = self._normalize_business_domain(
            business_domain
        )

        normalized_question = self._normalize_question(
            question
        )

        retrieved_context = (
            self.context_retrieval_engine
            .retrieve_domain_context(
                project_id=normalized_project_id,
                business_domain=normalized_domain,
                question=normalized_question,
            )
        )

        focused_context = (
            retrieved_context.get(
                "focused_context"
            )
            or {}
        )

        prompt = (
            self.prompt_builder
            .build_prompt(
                question=normalized_question,
                ai_context=focused_context,
            )
        )

        ai_response = self.ai_engine.answer_question(
            prompt=prompt,
            max_output_tokens=1200,
            metadata={
                "sapientia_capability":
                    "AI_ADVISOR",

                "project_id":
                    normalized_project_id,

                "business_domain":
                    normalized_domain,

                "intelligence_report_id":
                    retrieved_context.get(
                        "intelligence_report_id"
                    ),

                "retrieval_mode":
                    focused_context.get(
                        "retrieval_mode"
                    ),
            },
        )

        self._validate_ai_response(
            ai_response
        )

        statistics = (
            focused_context.get(
                "context_statistics"
            )
            or {}
        )

        response_metadata = (
            self._build_response_metadata(
                ai_response=ai_response,
                focused_context=focused_context,
                statistics=statistics,
            )
        )

        advisor_response_id = None

        if persist:
            advisor_response_id = (
                self._persist_response(
                    project_id=normalized_project_id,
                    retrieved_context=retrieved_context,
                    question=normalized_question,
                    prompt=prompt,
                    ai_response=ai_response,
                    response_metadata=response_metadata,
                )
            )

        return self._build_result(
            advisor_response_id=advisor_response_id,
            project_id=normalized_project_id,
            business_domain=normalized_domain,
            retrieved_context=retrieved_context,
            question=normalized_question,
            ai_response=ai_response,
            response_metadata=response_metadata,
        )

    def _persist_response(
        self,
        project_id: int,
        retrieved_context: dict[str, Any],
        question: str,
        prompt: str,
        ai_response: AIResponse,
        response_metadata: dict[str, Any],
    ) -> int:
        """
        Persist an AI Advisor response.
        """

        engine = get_engine()

        with engine.begin() as connection:
            repository = AIAdvisorRepository(
                connection
            )

            return repository.create_response(
                project_id=project_id,

                business_domain_id=(
                    retrieved_context.get(
                        "business_domain_id"
                    )
                ),

                intelligence_report_id=(
                    retrieved_context.get(
                        "intelligence_report_id"
                    )
                ),

                question=question,

                answer=ai_response.content,

                model_name=ai_response.model,

                prompt_text=prompt,

                response_json=response_metadata,
            )

    @staticmethod
    def _build_response_metadata(
        ai_response: AIResponse,
        focused_context: dict[str, Any],
        statistics: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build the serialisable provider, generation and retrieval
        metadata persisted with the Advisor response.
        """

        knowledge_asset_links_used = int(
            statistics.get(
                "knowledge_asset_links"
            )
            or 0
        )

        return {
            "success":
                ai_response.success,

            "capability":
                ai_response.capability.value,

            "response_id":
                ai_response.response_id,

            "provider":
                ai_response.provider,

            "model":
                ai_response.model,

            "input_tokens":
                ai_response.input_tokens,

            "output_tokens":
                ai_response.output_tokens,

            "total_tokens":
                ai_response.total_tokens,

            "execution_time_ms":
                ai_response.execution_time_ms,

            "estimated_cost":
                ai_response.estimated_cost,

            "confidence":
                ai_response.confidence,

            "warnings":
                list(
                    ai_response.warnings
                    or []
                ),

            "errors":
                list(
                    ai_response.errors
                    or []
                ),

            "provider_metadata":
                dict(
                    ai_response.metadata
                    or {}
                ),

            "retrieval_mode":
                focused_context.get(
                    "retrieval_mode"
                ),

            "keywords":
                focused_context.get(
                    "keywords"
                )
                or [],

            "fallback_used":
                bool(
                    focused_context.get(
                        "fallback_used"
                    )
                ),

            "concepts_used":
                int(
                    statistics.get(
                        "concepts"
                    )
                    or 0
                ),

            "findings_used":
                int(
                    statistics.get(
                        "findings"
                    )
                    or 0
                ),

            "knowledge_items_used":
                int(
                    statistics.get(
                        "knowledge_items"
                    )
                    or 0
                ),

            "knowledge_asset_links_used":
                knowledge_asset_links_used,

            # Compatibility with previous response terminology.
            "fusion_links_used":
                knowledge_asset_links_used,

            "document_chunks_used":
                int(
                    statistics.get(
                        "document_chunks"
                    )
                    or 0
                ),

            "has_intelligence_report":
                bool(
                    statistics.get(
                        "has_intelligence_report"
                    )
                ),

            "context_warning":
                focused_context.get(
                    "context_warning"
                ),
        }

    @staticmethod
    def _build_result(
        advisor_response_id: int | None,
        project_id: int,
        business_domain: str,
        retrieved_context: dict[str, Any],
        question: str,
        ai_response: AIResponse,
        response_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build the response returned to CLI, API and service consumers.
        """

        return {
            "ai_advisor_response_id":
                advisor_response_id,

            "project_id":
                project_id,

            "business_domain":
                business_domain,

            "intelligence_report_id":
                retrieved_context.get(
                    "intelligence_report_id"
                ),

            "success":
                ai_response.success,

            "capability":
                ai_response.capability.value,

            "provider":
                ai_response.provider,

            "model":
                ai_response.model,

            "response_id":
                ai_response.response_id,

            "input_tokens":
                ai_response.input_tokens,

            "output_tokens":
                ai_response.output_tokens,

            "total_tokens":
                ai_response.total_tokens,

            "execution_time_ms":
                ai_response.execution_time_ms,

            "estimated_cost":
                ai_response.estimated_cost,

            "confidence":
                ai_response.confidence,

            "warnings":
                list(
                    ai_response.warnings
                    or []
                ),

            "errors":
                list(
                    ai_response.errors
                    or []
                ),

            "retrieval_mode":
                response_metadata[
                    "retrieval_mode"
                ],

            "keywords":
                response_metadata[
                    "keywords"
                ],

            "fallback_used":
                response_metadata[
                    "fallback_used"
                ],

            "concepts_used":
                response_metadata[
                    "concepts_used"
                ],

            "findings_used":
                response_metadata[
                    "findings_used"
                ],

            "knowledge_items_used":
                response_metadata[
                    "knowledge_items_used"
                ],

            "knowledge_asset_links_used":
                response_metadata[
                    "knowledge_asset_links_used"
                ],

            # Compatibility with the previous API and CLI.
            "fusion_links_used":
                response_metadata[
                    "fusion_links_used"
                ],

            "document_chunks_used":
                response_metadata[
                    "document_chunks_used"
                ],

            "has_intelligence_report":
                response_metadata[
                    "has_intelligence_report"
                ],

            "context_warning":
                response_metadata[
                    "context_warning"
                ],

            "question":
                question,

            "answer":
                ai_response.content,
        }

    @staticmethod
    def _validate_ai_response(
        ai_response: AIResponse,
    ) -> None:
        """
        Validate the response returned by the Enterprise AI Engine.
        """

        if not isinstance(
            ai_response,
            AIResponse,
        ):
            raise TypeError(
                "EnterpriseAIEngine returned an invalid "
                "response type."
            )

        if not ai_response.success:
            provider_errors = "; ".join(
                ai_response.errors
                or []
            )

            error_message = (
                provider_errors
                or "The AI provider returned an unsuccessful response."
            )

            raise RuntimeError(
                error_message
            )

        if not str(
            ai_response.content
            or ""
        ).strip():
            raise RuntimeError(
                "The AI provider returned an empty answer."
            )

    @staticmethod
    def _normalize_project_id(
        project_id: int,
    ) -> int:
        try:
            normalized = int(
                project_id
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "A valid project ID is required."
            ) from exc

        if normalized <= 0:
            raise ValueError(
                "Project ID must be greater than zero."
            )

        return normalized

    @staticmethod
    def _normalize_business_domain(
        business_domain: str,
    ) -> str:
        normalized = str(
            business_domain
            or ""
        ).strip().upper()

        if not normalized:
            raise ValueError(
                "A business domain is required."
            )

        return normalized

    @staticmethod
    def _normalize_question(
        question: str,
    ) -> str:
        normalized = str(
            question
            or ""
        ).strip()

        if not normalized:
            raise ValueError(
                "A question is required."
            )

        return normalized