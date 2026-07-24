"""Versioned Enterprise Intelligence Assessment API."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import require_auth
from sapientia.services.intelligence.assessment_service import (
    EnterpriseIntelligenceAssessmentService,
)

router = APIRouter(prefix="/intelligence/assessments", tags=["intelligence-assessments"])


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: int,
    project_id: int = Query(default=1, ge=1),
    user=Depends(require_auth),
):
    assessment = EnterpriseIntelligenceAssessmentService().get(assessment_id, project_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Enterprise Intelligence assessment not found")
    return assessment


@router.get("/domain/{domain_code}/latest")
def get_latest_assessment(
    domain_code: str,
    project_id: int = Query(default=1, ge=1),
    user=Depends(require_auth),
):
    assessment = EnterpriseIntelligenceAssessmentService().latest(project_id, domain_code)
    if not assessment:
        raise HTTPException(status_code=404, detail="No Enterprise Intelligence assessment exists for this domain")
    return assessment


@router.get("/domain/{domain_code}")
def list_assessments(
    domain_code: str,
    project_id: int = Query(default=1, ge=1),
    user=Depends(require_auth),
):
    return {
        "project_id": project_id,
        "business_domain": domain_code.upper(),
        "assessments": EnterpriseIntelligenceAssessmentService().list_domain(project_id, domain_code),
    }
