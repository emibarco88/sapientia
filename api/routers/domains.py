from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection


router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("")
def get_domains(
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    """
    Return the business domains available to a project together with
    dataset, enterprise concept, and intelligence report counts.

    Datasets do not store project_id directly. Project ownership is
    resolved through ekr_core.source_system.
    """

    rows = connection.execute(
        text("""
            SELECT
                bd.business_domain_id,
                bd.domain_code,
                bd.domain_name,

                (
                    SELECT COUNT(DISTINCT d.dataset_id)
                    FROM ekr_core.dataset d
                    JOIN ekr_core.source_system ss
                      ON ss.source_system_id = d.source_system_id
                    WHERE d.business_domain_id = bd.business_domain_id
                      AND ss.project_id = :project_id
                ) AS datasets,

                (
                    SELECT COUNT(DISTINCT ec.enterprise_concept_id)
                    FROM ekr_intelligence.enterprise_concept ec
                    WHERE ec.business_domain_id = bd.business_domain_id
                      AND ec.project_id = :project_id
                ) AS concepts,

                (
                    SELECT COUNT(DISTINCT ir.intelligence_report_id)
                    FROM ekr_intelligence.intelligence_report ir
                    WHERE ir.business_domain_id = bd.business_domain_id
                      AND ir.project_id = :project_id
                ) AS intelligence_reports

            FROM ekr_business.business_domain bd
            WHERE EXISTS
            (
                SELECT 1
                FROM ekr_core.dataset d
                JOIN ekr_core.source_system ss
                  ON ss.source_system_id = d.source_system_id
                WHERE d.business_domain_id = bd.business_domain_id
                  AND ss.project_id = :project_id
            )
            OR EXISTS
            (
                SELECT 1
                FROM ekr_intelligence.enterprise_concept ec
                WHERE ec.business_domain_id = bd.business_domain_id
                  AND ec.project_id = :project_id
            )
            OR EXISTS
            (
                SELECT 1
                FROM ekr_intelligence.intelligence_report ir
                WHERE ir.business_domain_id = bd.business_domain_id
                  AND ir.project_id = :project_id
            )

            ORDER BY bd.domain_code
        """),
        {
            "project_id": project_id,
        },
    ).mappings().all()

    return [dict(row) for row in rows]


@router.get("/{domain_code}/workspace")
def get_domain_workspace(
    domain_code: str,
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    """
    Return the consolidated Enterprise Workspace context for a business
    domain.

    The response includes:
    - workspace summary
    - datasets
    - enterprise concepts
    - intelligence findings
    - latest intelligence report
    """

    normalized_domain = domain_code.strip().upper()

    domain = connection.execute(
        text("""
            SELECT
                business_domain_id,
                domain_code,
                domain_name
            FROM ekr_business.business_domain
            WHERE UPPER(domain_code) = :domain_code
            LIMIT 1
        """),
        {
            "domain_code": normalized_domain,
        },
    ).mappings().fetchone()

    if not domain:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Business domain '{normalized_domain}' "
                "was not found."
            ),
        )

    business_domain_id = domain["business_domain_id"]

    summary = connection.execute(
        text("""
            SELECT
                :domain_code AS domain_code,
                :domain_name AS domain_name,

                (
                    SELECT COUNT(DISTINCT d.dataset_id)
                    FROM ekr_core.dataset d
                    JOIN ekr_core.source_system ss
                      ON ss.source_system_id = d.source_system_id
                    WHERE d.business_domain_id = :business_domain_id
                      AND ss.project_id = :project_id
                ) AS datasets,

                (
                    SELECT COUNT(DISTINCT c.column_id)
                    FROM ekr_core."column" c
                    JOIN ekr_core.dataset d
                      ON d.dataset_id = c.dataset_id
                    JOIN ekr_core.source_system ss
                      ON ss.source_system_id = d.source_system_id
                    WHERE d.business_domain_id = :business_domain_id
                      AND ss.project_id = :project_id
                ) AS columns,

                (
                    SELECT COUNT(DISTINCT cs.column_semantic_id)
                    FROM ekr_semantic.column_semantic cs
                    JOIN ekr_core."column" c
                      ON c.column_id = cs.column_id
                    JOIN ekr_core.dataset d
                      ON d.dataset_id = c.dataset_id
                    JOIN ekr_core.source_system ss
                      ON ss.source_system_id = d.source_system_id
                    WHERE d.business_domain_id = :business_domain_id
                      AND ss.project_id = :project_id
                ) AS semantic_columns,

                (
                    SELECT COUNT(DISTINCT il.intelligence_link_id)
                    FROM ekr_knowledge.intelligence_link il
                    JOIN ekr_core.dataset d
                      ON d.dataset_id = il.dataset_id
                    JOIN ekr_core.source_system ss
                      ON ss.source_system_id = d.source_system_id
                    WHERE d.business_domain_id = :business_domain_id
                      AND ss.project_id = :project_id
                ) AS intelligence_links,

                (
                    SELECT COUNT(DISTINCT ec.enterprise_concept_id)
                    FROM ekr_intelligence.enterprise_concept ec
                    WHERE ec.business_domain_id = :business_domain_id
                      AND ec.project_id = :project_id
                ) AS enterprise_concepts,

                (
                    SELECT COUNT(DISTINCT f.intelligence_finding_id)
                    FROM ekr_intelligence.intelligence_finding f
                    WHERE f.business_domain_id = :business_domain_id
                      AND f.project_id = :project_id
                ) AS findings,

                (
                    SELECT COUNT(DISTINCT ir.intelligence_report_id)
                    FROM ekr_intelligence.intelligence_report ir
                    WHERE ir.business_domain_id = :business_domain_id
                      AND ir.project_id = :project_id
                ) AS reports
        """),
        {
            "project_id": project_id,
            "business_domain_id": business_domain_id,
            "domain_code": domain["domain_code"],
            "domain_name": domain["domain_name"],
        },
    ).mappings().one()

    datasets = connection.execute(
        text("""
            SELECT
                d.dataset_id,
                d.name,
                d.object_type,
                d.location,
                d.row_count,
                d.column_count,
                d.created_at,
                ss.name AS source_system_name,
                ss.source_type
            FROM ekr_core.dataset d
            JOIN ekr_core.source_system ss
              ON ss.source_system_id = d.source_system_id
            WHERE d.business_domain_id = :business_domain_id
              AND ss.project_id = :project_id
            ORDER BY
                d.created_at DESC NULLS LAST,
                d.dataset_id DESC
            LIMIT 50
        """),
        {
            "project_id": project_id,
            "business_domain_id": business_domain_id,
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

                (
                    SELECT COUNT(*)
                    FROM ekr_intelligence.enterprise_concept_evidence ece
                    WHERE ece.enterprise_concept_id =
                          ec.enterprise_concept_id
                ) AS evidence_count

            FROM ekr_intelligence.enterprise_concept ec
            WHERE ec.business_domain_id = :business_domain_id
              AND ec.project_id = :project_id
            ORDER BY
                ec.confidence_score DESC NULLS LAST,
                ec.concept_type,
                ec.concept_name
            LIMIT 50
        """),
        {
            "project_id": project_id,
            "business_domain_id": business_domain_id,
        },
    ).mappings().all()

    findings = connection.execute(
        text("""
            SELECT
                f.intelligence_finding_id,
                f.finding_type,
                f.finding_title,
                f.finding_description,
                f.finding_interpretation,
                f.confidence_score,
                f.severity_level,
                f.created_at
            FROM ekr_intelligence.intelligence_finding f
            WHERE f.business_domain_id = :business_domain_id
              AND f.project_id = :project_id
            ORDER BY
                f.created_at DESC NULLS LAST,
                f.intelligence_finding_id DESC
            LIMIT 50
        """),
        {
            "project_id": project_id,
            "business_domain_id": business_domain_id,
        },
    ).mappings().all()

    latest_report = connection.execute(
        text("""
            SELECT
                ir.intelligence_report_id,
                ir.report_title,
                ir.summary_text,
                ir.created_at
            FROM ekr_intelligence.intelligence_report ir
            WHERE ir.business_domain_id = :business_domain_id
              AND ir.project_id = :project_id
            ORDER BY
                ir.created_at DESC NULLS LAST,
                ir.intelligence_report_id DESC
            LIMIT 1
        """),
        {
            "project_id": project_id,
            "business_domain_id": business_domain_id,
        },
    ).mappings().fetchone()

    return {
        "domain": dict(domain),
        "summary": dict(summary),
        "datasets": [dict(row) for row in datasets],
        "concepts": [dict(row) for row in concepts],
        "findings": [dict(row) for row in findings],
        "latest_report": (
            dict(latest_report)
            if latest_report
            else None
        ),
    }


@router.get("/{domain_code}/summary")
def get_domain_summary(
    domain_code: str,
    project_id: int = 1,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    """
    Return only the summary portion of the workspace payload.
    """

    workspace = get_domain_workspace(
        domain_code=domain_code,
        project_id=project_id,
        connection=connection,
        user=user,
    )

    return workspace["summary"]