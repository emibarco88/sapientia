from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection
from sapientia.services.ai_advisor_service import AIAdvisorService


router = APIRouter(prefix="/ai-advisor", tags=["ai-advisor"])


class AskRequest(BaseModel):
    project_id: int
    business_domain: str
    question: str


@router.post("/ask")
def ask_ai_advisor(
    payload: AskRequest,
    user=Depends(require_auth),
):
    service = AIAdvisorService()

    return service.ask_domain_question(
        project_id=payload.project_id,
        business_domain=payload.business_domain,
        question=payload.question,
        persist=True,
    )


@router.get("/responses")
def get_ai_responses(
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                ai.ai_advisor_response_id,
                bd.domain_code,
                ai.intelligence_report_id,
                ai.question,
                ai.answer,
                ai.model_name,
                ai.response_json,
                ai.created_at
            FROM ekr_intelligence.ai_advisor_response ai
            LEFT JOIN ekr_business.business_domain bd
                ON bd.business_domain_id = ai.business_domain_id
            WHERE ai.project_id = :project_id
            ORDER BY ai.ai_advisor_response_id DESC
            LIMIT 50
        """),
        {"project_id": project_id},
    ).mappings().all()

    return [dict(row) for row in rows]