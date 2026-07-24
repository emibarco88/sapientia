"""Phase 3 final product APIs: overview, timeline, explainability and advisor context."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection

router = APIRouter(prefix="/phase3", tags=["phase3-final"])


def _domain(connection, project_id: int, domain_code: str):
    row = connection.execute(
        text("""
            SELECT business_domain_id, domain_code, domain_name
            FROM ekr_business.business_domain
            WHERE UPPER(domain_code) = UPPER(:domain_code)
            LIMIT 1
        """),
        {"domain_code": domain_code},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Business domain not found")
    return dict(row)


@router.get("/domains/{domain_code}/overview")
def domain_overview(
    domain_code: str,
    project_id: int = Query(default=1, ge=1),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    domain = _domain(connection, project_id, domain_code)
    domain_id = domain["business_domain_id"]

    current = connection.execute(
        text("""
            SELECT *
            FROM ekr_intelligence.v_domain_intelligence_current
            WHERE project_id = :project_id
              AND business_domain_id = :domain_id
            LIMIT 1
        """),
        {"project_id": project_id, "domain_id": domain_id},
    ).mappings().first()

    counts = connection.execute(
        text("""
            WITH latest AS (
              SELECT assessment_id
              FROM ekr_intelligence.enterprise_intelligence_assessment
              WHERE project_id=:project_id AND business_domain_id=:domain_id
              ORDER BY assessment_version DESC LIMIT 1
            )
            SELECT
              COUNT(*) AS total_objects,
              COUNT(*) FILTER (WHERE object_type='RISK') AS risks,
              COUNT(*) FILTER (WHERE object_type='OPPORTUNITY') AS opportunities,
              COUNT(*) FILTER (WHERE object_type='RECOMMENDATION') AS recommendations,
              COUNT(*) FILTER (WHERE UPPER(COALESCE(severity,'')) IN ('HIGH','CRITICAL')) AS high_severity
            FROM ekr_intelligence.enterprise_intelligence_object
            WHERE assessment_id=(SELECT assessment_id FROM latest)
        """),
        {"project_id": project_id, "domain_id": domain_id},
    ).mappings().first()

    top_items = connection.execute(
        text("""
            WITH latest AS (
              SELECT assessment_id
              FROM ekr_intelligence.enterprise_intelligence_assessment
              WHERE project_id=:project_id AND business_domain_id=:domain_id
              ORDER BY assessment_version DESC LIMIT 1
            )
            SELECT intelligence_object_id, object_type, title, description,
                   severity, priority, confidence_score
            FROM ekr_intelligence.enterprise_intelligence_object
            WHERE assessment_id=(SELECT assessment_id FROM latest)
            ORDER BY
              CASE UPPER(COALESCE(severity,''))
                WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
              confidence_score DESC NULLS LAST,
              sequence_number
            LIMIT 8
        """),
        {"project_id": project_id, "domain_id": domain_id},
    ).mappings().all()

    return {
        "domain": domain,
        "current": dict(current) if current else None,
        "summary": dict(counts or {}),
        "priority_items": [dict(row) for row in top_items],
    }


@router.get("/domains/{domain_code}/timeline")
def domain_timeline(
    domain_code: str,
    project_id: int = Query(default=1, ge=1),
    limit: int = Query(default=30, ge=1, le=100),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    domain = _domain(connection, project_id, domain_code)
    rows = connection.execute(
        text("""
            SELECT * FROM (
              SELECT
                'KNOWLEDGE' AS event_type,
                k.knowledge_version_id AS event_id,
                k.knowledge_version AS version,
                k.created_at AS event_at,
                'Enterprise Knowledge updated' AS title,
                jsonb_build_object(
                  'dataset_count',k.dataset_count,
                  'column_count',k.column_count,
                  'object_count',k.object_count,
                  'relationship_count',k.relationship_count,
                  'concept_count',k.concept_count
                ) AS details
              FROM ekr_knowledge.enterprise_knowledge_version k
              WHERE k.project_id=:project_id AND k.business_domain_id=:domain_id
              UNION ALL
              SELECT
                'ASSESSMENT', a.assessment_id, a.assessment_version, a.generated_at,
                a.assessment_title,
                jsonb_build_object(
                  'status',a.assessment_status,
                  'confidence',a.overall_confidence,
                  'knowledge_version_id',a.knowledge_version_id,
                  'report_id',a.intelligence_report_id
                )
              FROM ekr_intelligence.enterprise_intelligence_assessment a
              WHERE a.project_id=:project_id AND a.business_domain_id=:domain_id
            ) timeline
            ORDER BY event_at DESC
            LIMIT :limit
        """),
        {"project_id": project_id, "domain_id": domain["business_domain_id"], "limit": limit},
    ).mappings().all()
    return {"domain": domain, "timeline": [dict(row) for row in rows]}


@router.get("/intelligence-objects/{object_id}/explain")
def explain_intelligence_object(
    object_id: int,
    project_id: int = Query(default=1, ge=1),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    item = connection.execute(
        text("""
            SELECT o.*, a.project_id, a.assessment_version, a.knowledge_version_id,
                   bd.domain_code, bd.domain_name
            FROM ekr_intelligence.enterprise_intelligence_object o
            JOIN ekr_intelligence.enterprise_intelligence_assessment a
              ON a.assessment_id=o.assessment_id
            JOIN ekr_business.business_domain bd
              ON bd.business_domain_id=a.business_domain_id
            WHERE o.intelligence_object_id=:object_id AND a.project_id=:project_id
        """),
        {"object_id": object_id, "project_id": project_id},
    ).mappings().first()
    if not item:
        raise HTTPException(status_code=404, detail="Intelligence object not found")

    evidence = connection.execute(
        text("""
            SELECT intelligence_evidence_id, evidence_type, evidence_source,
                   evidence_text, confidence_score, enterprise_object_id,
                   dataset_id, column_id, knowledge_item_id,
                   source_schema, source_table, source_record_id, evidence_json
            FROM ekr_intelligence.enterprise_intelligence_evidence_reference
            WHERE intelligence_object_id=:object_id
            ORDER BY confidence_score DESC NULLS LAST, intelligence_evidence_id
        """),
        {"object_id": object_id},
    ).mappings().all()

    relations = connection.execute(
        text("""
            SELECT r.relation_type,
                   src.intelligence_object_id AS source_id, src.object_type AS source_type, src.title AS source_title,
                   tgt.intelligence_object_id AS target_id, tgt.object_type AS target_type, tgt.title AS target_title,
                   r.confidence_score
            FROM ekr_intelligence.enterprise_intelligence_object_relation r
            JOIN ekr_intelligence.enterprise_intelligence_object src
              ON src.intelligence_object_id=r.source_intelligence_object_id
            JOIN ekr_intelligence.enterprise_intelligence_object tgt
              ON tgt.intelligence_object_id=r.target_intelligence_object_id
            WHERE r.source_intelligence_object_id=:object_id
               OR r.target_intelligence_object_id=:object_id
            ORDER BY r.confidence_score DESC NULLS LAST
        """),
        {"object_id": object_id},
    ).mappings().all()

    return {
        "intelligence_object": dict(item),
        "reasoning_chain": [dict(row) for row in relations],
        "evidence": [dict(row) for row in evidence],
        "provenance": {
            "assessment_version": item["assessment_version"],
            "knowledge_version_id": item["knowledge_version_id"],
            "domain_code": item["domain_code"],
            "evidence_count": len(evidence),
            "relation_count": len(relations),
        },
    }


@router.get("/ai-advisor/domains/{domain_code}/context")
def advisor_context(
    domain_code: str,
    project_id: int = Query(default=1, ge=1),
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    overview = domain_overview(domain_code, project_id, connection, user)
    timeline = domain_timeline(domain_code, project_id, 12, connection, user)
    return {
        "domain": overview["domain"],
        "current_state": overview["current"],
        "priority_items": overview["priority_items"],
        "recent_timeline": timeline["timeline"],
        "grounding_mode": "KNOWLEDGE_AND_ASSESSMENT_HISTORY",
    }
