"""
Module: ai_advisor_repository.py

Purpose:
Reads AI-ready intelligence context and persists AI Advisor responses.
"""

import json
from sqlalchemy import text


class AIAdvisorRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_latest_domain_context(
        self,
        project_id: int,
        business_domain: str,
    ) -> dict:
        row = self.connection.execute(
            text("""
                SELECT
                    ir.intelligence_report_id,
                    ir.project_id,
                    ir.business_domain_id,
                    bd.domain_code,
                    bd.domain_name,
                    ir.ai_context_json,
                    ir.created_at
                FROM ekr_intelligence.intelligence_report ir
                JOIN ekr_business.business_domain bd
                    ON bd.business_domain_id = ir.business_domain_id
                WHERE ir.project_id = :project_id
                  AND bd.domain_code = :business_domain
                ORDER BY ir.created_at DESC
                LIMIT 1
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).mappings().fetchone()

        if not row:
            return {}

        return dict(row)

    def create_response(
        self,
        project_id: int,
        business_domain_id: int | None,
        intelligence_report_id: int | None,
        question: str,
        answer: str,
        model_name: str,
        prompt_text: str,
        response_json: dict,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.ai_advisor_response
                (
                    project_id,
                    business_domain_id,
                    intelligence_report_id,
                    question,
                    answer,
                    model_name,
                    prompt_text,
                    response_json
                )
                VALUES
                (
                    :project_id,
                    :business_domain_id,
                    :intelligence_report_id,
                    :question,
                    :answer,
                    :model_name,
                    :prompt_text,
                    CAST(:response_json AS JSONB)
                )
                RETURNING ai_advisor_response_id
            """),
            {
                "project_id": project_id,
                "business_domain_id": business_domain_id,
                "intelligence_report_id": intelligence_report_id,
                "question": question,
                "answer": answer,
                "model_name": model_name,
                "prompt_text": prompt_text,
                "response_json": json.dumps(response_json, default=str),
            },
        )

        return result.scalar_one()