"""
Module: ai_advisor_engine.py

Purpose:
Grounds OpenAI answers in Sapientia Enterprise Intelligence.
"""

from sapientia.db.connection import get_engine
from sapientia.engines.ai_advisor.openai_client import SapientiaOpenAIClient
from sapientia.engines.ai_advisor.prompt_builder import AIAdvisorPromptBuilder
from sapientia.engines.context_retrieval.context_retrieval_engine import (
    ContextRetrievalEngine,
)
from sapientia.repositories.intelligence.ai_advisor_repository import (
    AIAdvisorRepository,
)


class AIAdvisorEngine:
    def __init__(self):
        self.prompt_builder = AIAdvisorPromptBuilder()
        self.openai_client = SapientiaOpenAIClient()
        self.context_retrieval_engine = ContextRetrievalEngine()

    def ask_domain_question(
        self,
        project_id: int,
        business_domain: str,
        question: str,
        persist: bool = True,
    ) -> dict:
        business_domain = business_domain.upper()

        retrieved_context = self.context_retrieval_engine.retrieve_domain_context(
            project_id=project_id,
            business_domain=business_domain,
            question=question,
        )

        focused_context = retrieved_context["focused_context"]

        prompt = self.prompt_builder.build_prompt(
            question=question,
            ai_context=focused_context,
        )

        ai_response = self.openai_client.generate_answer(prompt)

        response_id = None

        if persist:
            engine = get_engine()

            with engine.begin() as connection:
                repository = AIAdvisorRepository(connection)

                response_id = repository.create_response(
                    project_id=project_id,
                    business_domain_id=retrieved_context.get("business_domain_id"),
                    intelligence_report_id=retrieved_context.get(
                        "intelligence_report_id"
                    ),
                    question=question,
                    answer=ai_response["answer"],
                    model_name=ai_response["model"],
                    prompt_text=prompt,
                    response_json={
                        "response_id": ai_response.get("response_id"),
                        "model": ai_response.get("model"),
                        "retrieval_mode": focused_context.get("retrieval_mode"),
                        "keywords": focused_context.get("keywords"),
                        "fallback_used": focused_context.get("fallback_used"),
                        "concepts_used": len(
                            focused_context.get(
                                "relevant_enterprise_concepts",
                                [],
                            )
                        ),
                        "findings_used": len(
                            focused_context.get("relevant_findings", [])
                        ),
                        "fusion_links_used": len(
                            focused_context.get(
                                "relevant_intelligence_links",
                                [],
                            )
                        ),
                    },
                )

        return {
            "ai_advisor_response_id": response_id,
            "project_id": project_id,
            "business_domain": business_domain,
            "intelligence_report_id": retrieved_context.get(
                "intelligence_report_id"
            ),
            "model": ai_response["model"],
            "retrieval_mode": focused_context.get("retrieval_mode"),
            "keywords": focused_context.get("keywords"),
            "fallback_used": focused_context.get("fallback_used"),
            "concepts_used": len(
                focused_context.get("relevant_enterprise_concepts", [])
            ),
            "findings_used": len(focused_context.get("relevant_findings", [])),
            "fusion_links_used": len(
                focused_context.get("relevant_intelligence_links", [])
            ),
            "question": question,
            "answer": ai_response["answer"],
        }