from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

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
    force: bool = False


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
                force=payload.force,
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


@router.get("/reports/{report_id}")
def get_intelligence_report(
    report_id: int,
    project_id: int = Query(
        default=1,
        ge=1,
    ),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    try:
        report = connection.execute(
            text("""
                SELECT
                    ir.intelligence_report_id,
                    ir.project_id,
                    ir.business_domain_id,

                    bd.domain_code,
                    bd.domain_name,

                    ir.report_scope,
                    ir.report_type,
                    ir.report_title,
                    ir.summary_text,
                    ir.report_json,
                    ir.ai_context_json,
                    ir.created_at

                FROM
                    ekr_intelligence.intelligence_report ir

                JOIN
                    ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     ir.business_domain_id

                WHERE ir.intelligence_report_id =
                      :report_id

                  AND ir.project_id =
                      :project_id
            """),
            {
                "report_id": report_id,
                "project_id": project_id,
            },
        ).mappings().fetchone()

        if not report:
            raise HTTPException(
                status_code=404,
                detail="Intelligence report not found",
            )

        findings = connection.execute(
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
                    f.finding_json,
                    f.created_at,

                    COUNT(
                        DISTINCT
                        ie.intelligence_evidence_id
                    ) AS evidence_count

                FROM
                    ekr_intelligence.intelligence_finding f

                LEFT JOIN
                    ekr_intelligence.intelligence_evidence ie
                  ON ie.intelligence_finding_id =
                     f.intelligence_finding_id

                WHERE f.intelligence_report_id =
                      :report_id

                  AND f.project_id =
                      :project_id

                GROUP BY
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
                    f.finding_json,
                    f.created_at

                ORDER BY
                    CASE
                        WHEN UPPER(
                            COALESCE(
                                f.severity_level,
                                ''
                            )
                        ) = 'CRITICAL'
                        THEN 1

                        WHEN UPPER(
                            COALESCE(
                                f.severity_level,
                                ''
                            )
                        ) = 'HIGH'
                        THEN 2

                        WHEN UPPER(
                            COALESCE(
                                f.severity_level,
                                ''
                            )
                        ) = 'MEDIUM'
                        THEN 3

                        WHEN UPPER(
                            COALESCE(
                                f.severity_level,
                                ''
                            )
                        ) = 'LOW'
                        THEN 4

                        ELSE 5
                    END,

                    f.confidence_score
                    DESC NULLS LAST,

                    f.intelligence_finding_id
            """),
            {
                "report_id": report_id,
                "project_id": project_id,
            },
        ).mappings().all()

        concepts = connection.execute(
            text("""
                SELECT
                    ec.enterprise_concept_id,
                    ec.concept_name,
                    ec.concept_type,
                    ec.concept_description,
                    ec.confidence_score,
                    ec.concept_status,

                    COUNT(
                        DISTINCT
                        ece.enterprise_concept_evidence_id
                    ) AS evidence_count

                FROM
                    ekr_intelligence.enterprise_concept ec

                LEFT JOIN
                    ekr_intelligence
                    .enterprise_concept_evidence ece
                  ON ece.enterprise_concept_id =
                     ec.enterprise_concept_id

                WHERE ec.project_id =
                      :project_id

                  AND ec.business_domain_id =
                      :business_domain_id

                GROUP BY
                    ec.enterprise_concept_id,
                    ec.concept_name,
                    ec.concept_type,
                    ec.concept_description,
                    ec.confidence_score,
                    ec.concept_status

                ORDER BY
                    ec.confidence_score
                    DESC NULLS LAST,

                    ec.concept_name
            """),
            {
                "project_id": project_id,
                "business_domain_id":
                    report["business_domain_id"],
            },
        ).mappings().all()

        return {
            "report": dict(report),
            "findings": [
                dict(row)
                for row in findings
            ],
            "concepts": [
                dict(row)
                for row in concepts
            ],
        }

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve the intelligence "
                f"report: {exc}"
            ),
        ) from exc


@router.get(
    "/findings/{finding_id}/evidence"
)
def get_finding_evidence(
    finding_id: int,
    project_id: int = Query(
        default=1,
        ge=1,
    ),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    try:
        finding = connection.execute(
            text("""
                SELECT
                    f.intelligence_finding_id,
                    f.intelligence_report_id,
                    f.project_id,
                    f.finding_type,
                    f.finding_title,
                    f.finding_description,
                    f.finding_interpretation,
                    f.confidence_score,
                    f.severity_level

                FROM
                    ekr_intelligence.intelligence_finding f

                WHERE f.intelligence_finding_id =
                      :finding_id

                  AND f.project_id =
                      :project_id
            """),
            {
                "finding_id": finding_id,
                "project_id": project_id,
            },
        ).mappings().fetchone()

        if not finding:
            raise HTTPException(
                status_code=404,
                detail="Intelligence finding not found",
            )

        evidence = connection.execute(
            text("""
                SELECT
                    ie.intelligence_evidence_id,
                    ie.intelligence_finding_id,
                    ie.evidence_type,
                    ie.evidence_source,
                    ie.evidence_text,

                    ie.dataset_id,
                    d.name AS dataset_name,

                    ie.column_id,
                    c.name AS column_name,

                    ie.document_id,

                    CAST(
                        NULL AS VARCHAR
                    ) AS document_name,

                    ie.knowledge_item_id,
                    ki.name AS knowledge_item_name,

                    ie.intelligence_link_id,
                    ie.confidence_score,
                    ie.evidence_json

                FROM
                    ekr_intelligence.intelligence_evidence ie

                LEFT JOIN
                    ekr_core.dataset d
                  ON d.dataset_id =
                     ie.dataset_id

                LEFT JOIN
                    ekr_core."column" c
                  ON c.column_id =
                     ie.column_id

                LEFT JOIN
                    ekr_knowledge.knowledge_item ki
                  ON ki.knowledge_item_id =
                     ie.knowledge_item_id

                WHERE ie.intelligence_finding_id =
                      :finding_id

                ORDER BY
                    ie.confidence_score
                    DESC NULLS LAST,

                    ie.intelligence_evidence_id
            """),
            {
                "finding_id": finding_id,
            },
        ).mappings().all()

        return {
            "finding": dict(finding),
            "evidence": [
                dict(row)
                for row in evidence
            ],
        }

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve supporting "
                f"evidence: {exc}"
            ),
        ) from exc


@router.get("/{domain_code}/latest")
def get_latest_intelligence_report(
    domain_code: str,
    project_id: int = Query(
        default=1,
        ge=1,
    ),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    try:
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
                    ir.created_at,

                    COUNT(
                        DISTINCT
                        f.intelligence_finding_id
                    ) AS findings

                FROM
                    ekr_intelligence.intelligence_report ir

                JOIN
                    ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     ir.business_domain_id

                LEFT JOIN
                    ekr_intelligence.intelligence_finding f
                  ON f.intelligence_report_id =
                     ir.intelligence_report_id

                WHERE ir.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :domain_code
                  )

                GROUP BY
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

                ORDER BY
                    ir.created_at DESC,
                    ir.intelligence_report_id DESC

                LIMIT 1
            """),
            {
                "project_id": project_id,
                "domain_code": domain_code,
            },
        ).mappings().fetchone()

        return (
            dict(row)
            if row
            else {}
        )

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve the latest "
                f"intelligence report: {exc}"
            ),
        ) from exc


@router.get("/{domain_code}/findings")
def get_findings(
    domain_code: str,
    project_id: int = Query(
        default=1,
        ge=1,
    ),
    report_id: int | None = None,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    try:
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
                    f.created_at,

                    COUNT(
                        DISTINCT
                        ie.intelligence_evidence_id
                    ) AS evidence_count

                FROM
                    ekr_intelligence.intelligence_finding f

                JOIN
                    ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     f.business_domain_id

                LEFT JOIN
                    ekr_intelligence.intelligence_evidence ie
                  ON ie.intelligence_finding_id =
                     f.intelligence_finding_id

                WHERE f.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :domain_code
                  )

                  AND (
                        :report_id IS NULL
                        OR
                        f.intelligence_report_id =
                        :report_id
                  )

                GROUP BY
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

                ORDER BY
                    f.created_at DESC,
                    f.intelligence_finding_id DESC

                LIMIT 200
            """),
            {
                "project_id": project_id,
                "domain_code": domain_code,
                "report_id": report_id,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve intelligence "
                f"findings: {exc}"
            ),
        ) from exc


@router.get("/{domain_code}/reports")
def get_intelligence_reports(
    domain_code: str,
    project_id: int = Query(
        default=1,
        ge=1,
    ),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    try:
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
                    ) AS findings,

                    COUNT(
                        DISTINCT
                        ie.intelligence_evidence_id
                    ) AS evidence_items,

                    COUNT(
                        DISTINCT
                        CASE
                            WHEN UPPER(
                                COALESCE(
                                    f.severity_level,
                                    ''
                                )
                            ) IN (
                                'CRITICAL',
                                'HIGH'
                            )
                            THEN
                                f.intelligence_finding_id
                        END
                    ) AS high_priority_findings

                FROM
                    ekr_intelligence.intelligence_report ir

                JOIN
                    ekr_business.business_domain bd
                  ON bd.business_domain_id =
                     ir.business_domain_id

                LEFT JOIN
                    ekr_intelligence.intelligence_finding f
                  ON f.intelligence_report_id =
                     ir.intelligence_report_id

                LEFT JOIN
                    ekr_intelligence.intelligence_evidence ie
                  ON ie.intelligence_finding_id =
                     f.intelligence_finding_id

                WHERE ir.project_id =
                      :project_id

                  AND UPPER(
                      bd.domain_code
                  ) = UPPER(
                      :domain_code
                  )

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

                LIMIT 100
            """),
            {
                "project_id": project_id,
                "domain_code": domain_code,
            },
        ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to retrieve intelligence "
                f"reports: {exc}"
            ),
        ) from exc