from fastapi import APIRouter, Depends
from sqlalchemy import text

from api.auth import require_auth
from api.database import get_connection


router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/{domain_code}/latest")
def get_latest_intelligence_report(
    domain_code: str,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    row = connection.execute(
        text("""
            SELECT
                ir.intelligence_report_id,
                bd.domain_code,
                ir.report_title,
                ir.summary_text,
                ir.report_json,
                ir.ai_context_json,
                ir.created_at
            FROM ekr_intelligence.intelligence_report ir
            JOIN ekr_business.business_domain bd
                ON bd.business_domain_id = ir.business_domain_id
            WHERE bd.domain_code = :domain_code
            ORDER BY ir.created_at DESC
            LIMIT 1
        """),
        {"domain_code": domain_code.upper()},
    ).mappings().fetchone()

    return dict(row) if row else {}


@router.get("/{domain_code}/findings")
def get_findings(
    domain_code: str,
    connection=Depends(get_connection),
    user=Depends(require_auth),
):
    rows = connection.execute(
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
            JOIN ekr_business.business_domain bd
                ON bd.business_domain_id = f.business_domain_id
            WHERE bd.domain_code = :domain_code
            ORDER BY f.intelligence_finding_id DESC
            LIMIT 100
        """),
        {"domain_code": domain_code.upper()},
    ).mappings().all()

    return [dict(row) for row in rows]