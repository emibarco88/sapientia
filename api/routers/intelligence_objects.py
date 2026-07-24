"""Structured Enterprise Intelligence object API."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import require_auth
from sapientia.services.intelligence.intelligence_object_service import (
    EnterpriseIntelligenceObjectService,
)

router = APIRouter(prefix="/intelligence", tags=["intelligence-objects"])


@router.get("/assessments/{assessment_id}/objects/summary")
def get_object_summary(
    assessment_id: int,
    project_id: int = Query(default=1, ge=1),
    user=Depends(require_auth),
):
    return EnterpriseIntelligenceObjectService().summary(assessment_id, project_id)


@router.get("/assessments/{assessment_id}/objects")
def list_assessment_objects(
    assessment_id: int,
    project_id: int = Query(default=1, ge=1),
    object_type: str | None = Query(default=None),
    user=Depends(require_auth),
):
    try:
        objects = EnterpriseIntelligenceObjectService().list_objects(
            assessment_id, project_id, object_type
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "assessment_id": assessment_id,
        "project_id": project_id,
        "object_type": object_type.upper() if object_type else None,
        "objects": objects,
    }


@router.get("/objects/{object_id}")
def get_intelligence_object(
    object_id: int,
    project_id: int = Query(default=1, ge=1),
    user=Depends(require_auth),
):
    item = EnterpriseIntelligenceObjectService().get_object(object_id, project_id)
    if not item:
        raise HTTPException(status_code=404, detail="Enterprise Intelligence object not found")
    return item
