from fastapi import APIRouter, Depends
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection


router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.get("/{domain_code}")
def get_concepts(
    domain_code: str,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                ec.enterprise_concept_id,
                bd.domain_code,
                ec.concept_name,
                ec.concept_type,
                ec.concept_description,
                ec.confidence_score,
                ec.concept_status,
                COUNT(ece.enterprise_concept_evidence_id) AS evidence_count
            FROM ekr_intelligence.enterprise_concept ec
            JOIN ekr_business.business_domain bd
                ON bd.business_domain_id = ec.business_domain_id
            LEFT JOIN ekr_intelligence.enterprise_concept_evidence ece
                ON ece.enterprise_concept_id = ec.enterprise_concept_id
            WHERE bd.domain_code = :domain_code
            GROUP BY
                ec.enterprise_concept_id,
                bd.domain_code,
                ec.concept_name,
                ec.concept_type,
                ec.concept_description,
                ec.confidence_score,
                ec.concept_status
            ORDER BY ec.concept_type, ec.concept_name
        """),
        {"domain_code": domain_code.upper()},
    ).mappings().all()

    return [dict(row) for row in rows]


@router.get("/{domain_code}/{concept_id}/evidence")
def get_concept_evidence(
    domain_code: str,
    concept_id: int,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
        text("""
            SELECT
                ece.enterprise_concept_evidence_id,
                ece.evidence_type,
                ece.evidence_source,
                ece.evidence_text,
                ece.dataset_id,
                ece.column_id,
                ece.knowledge_item_id,
                ece.intelligence_link_id,
                ece.confidence_score,
                ece.created_at
            FROM ekr_intelligence.enterprise_concept_evidence ece
            JOIN ekr_intelligence.enterprise_concept ec
                ON ec.enterprise_concept_id = ece.enterprise_concept_id
            JOIN ekr_business.business_domain bd
                ON bd.business_domain_id = ec.business_domain_id
            WHERE bd.domain_code = :domain_code
              AND ec.enterprise_concept_id = :concept_id
            ORDER BY ece.enterprise_concept_evidence_id
        """),
        {
            "domain_code": domain_code.upper(),
            "concept_id": concept_id,
        },
    ).mappings().all()

    return [dict(row) for row in rows]