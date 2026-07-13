from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection

from sapientia.services.enterprise_intelligence_generation_service import (
    EnterpriseIntelligenceGenerationService,
)


router = APIRouter(
    prefix="/intelligence",
    tags=["intelligence"],
)


class GenerateIntelligenceRequest(BaseModel):
    project_id: int = 1
    persist: bool = True


@router.post("/{domain_code}/generate")
def generate_intelligence(
    domain_code: str,
    payload: GenerateIntelligenceRequest,
    user=Depends(require_auth),
):
    try:
        return (
            EnterpriseIntelligenceGenerationService()
            .generate_domain_intelligence(
                project_id=payload.project_id,
                business_domain=domain_code,
                persist=payload.persist,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Enterprise Intelligence "
                f"generation failed: {exc}"
            ),
        ) from exc


@router.get("/{domain_code}/latest")
def get_latest_intelligence_report(
    domain_code: str,
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    row = connection.execute(
        text("""
            SELECT
                ir.intelligence_report_id,
                ir.project_id,
                bd.domain_code,
                bd.domain_name,
                ir.report_scope,
                ir.report_type,
                ir.report_title,
                ir.summary_text,
                ir.report_json,
                ir.ai_context_json,
                ir.created_at

            FROM ekr_intelligence.intelligence_report ir

            JOIN ekr_business.business_domain bd
              ON bd.business_domain_id =
                 ir.business_domain_id

            WHERE ir.project_id = :project_id

              AND UPPER(bd.domain_code) =
                  UPPER(:domain_code)

            ORDER BY
                ir.created_at DESC,
                ir.intelligence_report_id DESC

            LIMIT 1
        """),
        {
            "project_id":
                project_id,

            "domain_code":
                domain_code,
        },
    ).mappings().fetchone()

    return dict(row) if row else {}


@router.get("/{domain_code}/findings")
def get_findings(
    domain_code: str,
    project_id: int = 1,
    report_id: int | None = None,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                f.intelligence_finding_id,
                f.intelligence_report_id,
                f.finding_type,
                f.finding_title,
                f.finding_description,
                f.finding_interpretation,
                f.confidence_score,
                f.severity_level,
                f.source_object_type,
                f.source_object_id,
                f.created_at

            FROM ekr_intelligence.intelligence_finding f

            JOIN ekr_business.business_domain bd
              ON bd.business_domain_id =
                 f.business_domain_id

            WHERE f.project_id = :project_id

              AND UPPER(bd.domain_code) =
                  UPPER(:domain_code)

              AND (
                    :report_id IS NULL
                    OR
                    f.intelligence_report_id =
                    :report_id
              )

            ORDER BY
                f.created_at DESC,
                f.intelligence_finding_id DESC

            LIMIT 200
        """),
        {
            "project_id":
                project_id,

            "domain_code":
                domain_code,

            "report_id":
                report_id,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


@router.get("/{domain_code}/reports")
def get_intelligence_reports(
    domain_code: str,
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                ir.intelligence_report_id,
                ir.report_scope,
                ir.report_type,
                ir.report_title,
                ir.summary_text,
                ir.created_at,

                COUNT(
                    DISTINCT
                    f.intelligence_finding_id
                ) AS findings

            FROM ekr_intelligence.intelligence_report ir

            JOIN ekr_business.business_domain bd
              ON bd.business_domain_id =
                 ir.business_domain_id

            LEFT JOIN
                ekr_intelligence.intelligence_finding f
              ON f.intelligence_report_id =
                 ir.intelligence_report_id

            WHERE ir.project_id = :project_id

              AND UPPER(bd.domain_code) =
                  UPPER(:domain_code)

            GROUP BY
                ir.intelligence_report_id,
                ir.report_scope,
                ir.report_type,
                ir.report_title,
                ir.summary_text,
                ir.created_at

            ORDER BY
                ir.created_at DESC,
                ir.intelligence_report_id DESC

            LIMIT 50
        """),
        {
            "project_id":
                project_id,

            "domain_code":
                domain_code,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]