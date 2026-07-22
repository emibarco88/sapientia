"""
Module: ai_advisor_engine.py

Purpose:
Answers enterprise questions using evidence retrieved from Sapientia's
Enterprise Knowledge Repository and Enterprise Intelligence layer.
"""

from __future__ import annotations

from typing import Any

from sapientia.db.connection import get_engine
from sapientia.engines.ai_advisor.openai_client import (
    SapientiaOpenAIClient,
)
from sapientia.engines.ai_advisor.prompt_builder import (
    AIAdvisorPromptBuilder,
)
from sapientia.engines.context_retrieval.context_retrieval_engine import (
    ContextRetrievalEngine,
)
from sapientia.repositories.intelligence.ai_advisor_repository import (
    AIAdvisorRepository,
)


class AIAdvisorEngine:
    """
    Coordinates retrieval, prompt construction, AI generation and
    response persistence.
    """

    def __init__(
        self,
        prompt_builder: (
            AIAdvisorPromptBuilder | None
        ) = None,
        openai_client: (
            SapientiaOpenAIClient | None
        ) = None,
        context_retrieval_engine: (
            ContextRetrievalEngine | None
        ) = None,
    ) -> None:
        self.prompt_builder = (
            prompt_builder
            or AIAdvisorPromptBuilder()
        )

        self.openai_client = (
            openai_client
            or SapientiaOpenAIClient()
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
        normalized_domain = (
            str(business_domain)
            .strip()
            .upper()
        )

        normalized_question = (
            str(question or "")
            .strip()
        )

        if not normalized_question:
            raise ValueError(
                "A question is required."
            )

        retrieved_context = (
            self.context_retrieval_engine
            .retrieve_domain_context(
                project_id=project_id,
                business_domain=(
                    normalized_domain
                ),
                question=normalized_question,
            )
        )

        focused_context = (
            retrieved_context[
                "focused_context"
            ]
        )

        prompt = (
            self.prompt_builder
            .build_prompt(
                question=normalized_question,
                ai_context=focused_context,
            )
        )

        ai_response = (
            self.openai_client
            .generate_answer(prompt)
        )

        statistics = (
            focused_context.get(
                "context_statistics"
            )
            or {}
        )

        response_metadata = {
            "response_id":
                ai_response.get(
                    "response_id"
                ),

            "model":
                ai_response.get(
                    "model"
                ),

            "retrieval_mode":
                focused_context.get(
                    "retrieval_mode"
                ),

            "keywords":
                focused_context.get(
                    "keywords"
                ),

            "fallback_used":
                focused_context.get(
                    "fallback_used"
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
                int(
                    statistics.get(
                        "knowledge_asset_links"
                    )
                    or 0
                ),

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
        }

        advisor_response_id = None

        if persist:
            engine = get_engine()

            with engine.begin() as connection:
                repository = (
                    AIAdvisorRepository(
                        connection
                    )
                )

                advisor_response_id = (
                    repository.create_response(
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

                        question=(
                            normalized_question
                        ),

                        answer=(
                            ai_response["answer"]
                        ),

                        model_name=(
                            ai_response["model"]
                        ),

                        prompt_text=prompt,

                        response_json=(
                            response_metadata
                        ),
                    )
                )

        return {
            "ai_advisor_response_id":
                advisor_response_id,

            "project_id":
                project_id,

            "business_domain":
                normalized_domain,

            "intelligence_report_id":
                retrieved_context.get(
                    "intelligence_report_id"
                ),

            "model":
                ai_response["model"],

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

            # Compatibility with the previous API.
            "fusion_links_used":
                response_metadata[
                    "knowledge_asset_links_used"
                ],

            "document_chunks_used":
                response_metadata[
                    "document_chunks_used"
                ],

            "question":
                normalized_question,

            "answer":
                ai_response["answer"],
        }