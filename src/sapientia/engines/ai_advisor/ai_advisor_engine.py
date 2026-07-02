"""
Module: ai_advisor_engine.py

Purpose:
Grounds OpenAI answers in Sapientia Enterprise Intelligence.
"""

from sapientia.db.connection import get_engine
from sapientia.engines.ai_advisor.openai_client import SapientiaOpenAIClient
from sapientia.engines.ai_advisor.prompt_builder import AIAdvisorPromptBuilder
from sapientia.repositories.intelligence.ai_advisor_repository import (
    AIAdvisorRepository,
)


class AIAdvisorEngine:
    def __init__(self):
        self.prompt_builder = AIAdvisorPromptBuilder()
        self.openai_client = SapientiaOpenAIClient()

    def ask_domain_question(
        self,
        project_id: int,
        business_domain: str,
        question: str,
        persist: bool = True,
    ) -> dict:
        business_domain = business_domain.upper()

        engine = get_engine()

        with engine.begin() as connection:
            repository = AIAdvisorRepository(connection)

            context_record = repository.get_latest_domain_context(
                project_id=project_id,
                business_domain=business_domain,
            )

            if not context_record:
                raise ValueError(
                    "No Enterprise Intelligence context found for "
                    f"project_id={project_id}, business_domain={business_domain}. "
                    "Run the intelligence command first."
                )

            ai_context = context_record["ai_context_json"]

            prompt = self.prompt_builder.build_prompt(
                question=question,
                ai_context=ai_context,
            )

            ai_response = self.openai_client.generate_answer(prompt)

            response_id = None

            if persist:
                response_id = repository.create_response(
                    project_id=project_id,
                    business_domain_id=context_record.get("business_domain_id"),
                    intelligence_report_id=context_record.get(
                        "intelligence_report_id"
                    ),
                    question=question,
                    answer=ai_response["answer"],
                    model_name=ai_response["model"],
                    prompt_text=prompt,
                    response_json={
                        "response_id": ai_response.get("response_id"),
                        "model": ai_response.get("model"),
                    },
                )

        return {
            "ai_advisor_response_id": response_id,
            "project_id": project_id,
            "business_domain": business_domain,
            "intelligence_report_id": context_record.get(
                "intelligence_report_id"
            ),
            "model": ai_response["model"],
            "question": question,
            "answer": ai_response["answer"],
        }