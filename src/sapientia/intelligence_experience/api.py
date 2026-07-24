from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.engine import Connection

from api.auth import require_auth
from api.database import get_connection

from .service import IntelligenceExperienceService

router = APIRouter(
    prefix="/intelligence-experience",
    tags=["enterprise-intelligence-experience"],
    dependencies=[Depends(require_auth)],
)


class StoryRequest(BaseModel):
    assessment_id: int | None = Field(default=None, ge=1)
    force_refresh: bool = False
    tone: Literal["executive", "detailed"] = "executive"
    ai_mode: Literal["deterministic", "enriched"] = "deterministic"


def get_service(
    connection: Connection = Depends(get_connection),
) -> IntelligenceExperienceService:
    return IntelligenceExperienceService(connection)


def raise_not_found(exc: LookupError) -> None:
    raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/domains/{domain_code}/narrative")
def get_narrative(
    domain_code: str,
    project_id: int = Query(1, ge=1),
    assessment_id: int | None = Query(None, ge=1),
    ai_mode: Literal["deterministic", "enriched"] = "deterministic",
    service: IntelligenceExperienceService = Depends(get_service),
):
    try:
        return service.narrative(project_id, domain_code, assessment_id, ai_mode)
    except LookupError as exc:
        raise_not_found(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/domains/{domain_code}/story")
def tell_story(
    domain_code: str,
    body: StoryRequest | None = None,
    project_id: int = Query(1, ge=1),
    service: IntelligenceExperienceService = Depends(get_service),
):
    request = body or StoryRequest()
    try:
        return service.narrative(
            project_id,
            domain_code,
            request.assessment_id,
            request.ai_mode,
            request.force_refresh,
            request.tone,
        )
    except LookupError as exc:
        raise_not_found(exc)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/domains/{domain_code}/health")
def get_health(
    domain_code: str,
    project_id: int = Query(1, ge=1),
    assessment_id: int | None = Query(None, ge=1),
    service: IntelligenceExperienceService = Depends(get_service),
):
    try:
        return service.health(project_id, domain_code, assessment_id)
    except LookupError as exc:
        raise_not_found(exc)


@router.get("/domains/{domain_code}/timeline")
def get_timeline(
    domain_code: str,
    project_id: int = Query(1, ge=1),
    limit: int = Query(30, ge=1, le=100),
    service: IntelligenceExperienceService = Depends(get_service),
):
    return service.timeline(project_id, domain_code, limit)


@router.get("/business-objects/{enterprise_object_id}/profile")
def get_business_object_profile(
    enterprise_object_id: int,
    domain_code: str = Query(...),
    project_id: int = Query(1, ge=1),
    assessment_id: int | None = Query(None, ge=1),
    service: IntelligenceExperienceService = Depends(get_service),
):
    try:
        return service.business_object_profile(
            project_id, domain_code, enterprise_object_id, assessment_id
        )
    except LookupError as exc:
        raise_not_found(exc)


@router.post("/statements/{statement_id}/explain")
def explain_statement(
    statement_id: str,
    service: IntelligenceExperienceService = Depends(get_service),
):
    try:
        return service.explain(statement_id)
    except LookupError as exc:
        raise_not_found(exc)
