"""Persistence gateway for versioned Enterprise Intelligence Assessments."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


class EnterpriseIntelligenceAssessmentRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_domain(self, business_domain: str) -> dict[str, Any]:
        row = self.connection.execute(
            text("""
                SELECT business_domain_id, domain_code, domain_name
                FROM ekr_business.business_domain
                WHERE UPPER(domain_code) = UPPER(:business_domain)
            """),
            {"business_domain": business_domain},
        ).mappings().fetchone()
        return dict(row) if row else {}

    def next_version(self, project_id: int, business_domain_id: int) -> int:
        value = self.connection.execute(
            text("""
                SELECT COALESCE(MAX(assessment_version), 0) + 1
                FROM ekr_intelligence.enterprise_intelligence_assessment
                WHERE project_id = :project_id
                  AND business_domain_id = :business_domain_id
            """),
            {"project_id": project_id, "business_domain_id": business_domain_id},
        ).scalar_one()
        return int(value)

    def supersede_current(self, project_id: int, business_domain_id: int) -> int:
        result = self.connection.execute(
            text("""
                UPDATE ekr_intelligence.enterprise_intelligence_assessment
                   SET assessment_status = 'SUPERSEDED',
                       superseded_at = NOW(),
                       updated_at = NOW()
                 WHERE project_id = :project_id
                   AND business_domain_id = :business_domain_id
                   AND assessment_status IN ('GENERATED', 'PUBLISHED')
            """),
            {"project_id": project_id, "business_domain_id": business_domain_id},
        )
        return int(result.rowcount or 0)

    def create_assessment(
        self,
        *,
        project_id: int,
        business_domain_id: int,
        version: int,
        title: str,
        summary: str | None,
        confidence: float | None,
        enterprise_intelligence_run_id: int | None,
        intelligence_report_id: int | None,
        knowledge_version_id: int | None,
        assessment_json: dict[str, Any],
    ) -> int:
        row = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_intelligence_assessment (
                    project_id, business_domain_id, enterprise_intelligence_run_id,
                    intelligence_report_id, knowledge_version_id, assessment_version, assessment_status,
                    assessment_title, executive_summary, overall_confidence,
                    assessment_scope, assessment_json
                ) VALUES (
                    :project_id, :business_domain_id, :enterprise_intelligence_run_id,
                    :intelligence_report_id, :knowledge_version_id, :version, 'GENERATED',
                    :title, :summary, :confidence, 'DOMAIN', CAST(:assessment_json AS JSONB)
                )
                RETURNING assessment_id
            """),
            {
                "project_id": project_id,
                "business_domain_id": business_domain_id,
                "enterprise_intelligence_run_id": enterprise_intelligence_run_id,
                "intelligence_report_id": intelligence_report_id,
                "knowledge_version_id": knowledge_version_id,
                "version": version,
                "title": title,
                "summary": summary,
                "confidence": confidence,
                "assessment_json": json.dumps(assessment_json, default=str),
            },
        ).scalar_one()
        return int(row)

    def upsert_executive_summary(
        self,
        *,
        assessment_id: int,
        headline: str | None,
        summary_text: str,
        key_message: str | None,
        confidence_score: float | None,
        summary_json: dict[str, Any],
    ) -> None:
        self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_intelligence_executive_summary (
                    assessment_id, headline, summary_text, key_message,
                    confidence_score, summary_json
                ) VALUES (
                    :assessment_id, :headline, :summary_text, :key_message,
                    :confidence_score, CAST(:summary_json AS JSONB)
                )
                ON CONFLICT (assessment_id) DO UPDATE SET
                    headline = EXCLUDED.headline,
                    summary_text = EXCLUDED.summary_text,
                    key_message = EXCLUDED.key_message,
                    confidence_score = EXCLUDED.confidence_score,
                    summary_json = EXCLUDED.summary_json,
                    updated_at = NOW()
            """),
            {
                "assessment_id": assessment_id,
                "headline": headline,
                "summary_text": summary_text,
                "key_message": key_message,
                "confidence_score": confidence_score,
                "summary_json": json.dumps(summary_json, default=str),
            },
        )

    def get(self, assessment_id: int, project_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            text("""
                SELECT a.*, bd.domain_code, bd.domain_name,
                       es.headline, es.summary_text AS structured_summary_text,
                       es.key_message, es.confidence_score AS summary_confidence,
                       es.summary_json
                FROM ekr_intelligence.enterprise_intelligence_assessment a
                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id = a.business_domain_id
                LEFT JOIN ekr_intelligence.enterprise_intelligence_executive_summary es
                  ON es.assessment_id = a.assessment_id
                WHERE a.assessment_id = :assessment_id
                  AND a.project_id = :project_id
            """),
            {"assessment_id": assessment_id, "project_id": project_id},
        ).mappings().fetchone()
        return dict(row) if row else {}

    def list_domain(self, project_id: int, business_domain: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            text("""
                SELECT a.assessment_id, a.project_id, a.assessment_version,
                       a.assessment_status, a.assessment_title, a.executive_summary,
                       a.overall_confidence, a.assessment_scope, a.generated_at,
                       a.published_at, a.superseded_at, a.retired_at,
                       a.enterprise_intelligence_run_id, a.intelligence_report_id,
                       a.knowledge_version_id, kv.knowledge_version, kv.knowledge_fingerprint,
                       bd.domain_code, bd.domain_name
                FROM ekr_intelligence.enterprise_intelligence_assessment a
                JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id = a.business_domain_id
                LEFT JOIN ekr_knowledge.enterprise_knowledge_version kv
                  ON kv.knowledge_version_id = a.knowledge_version_id
                WHERE a.project_id = :project_id
                  AND UPPER(bd.domain_code) = UPPER(:business_domain)
                ORDER BY a.assessment_version DESC
            """),
            {"project_id": project_id, "business_domain": business_domain},
        ).mappings().all()
        return [dict(row) for row in rows]

    def latest(self, project_id: int, business_domain: str) -> dict[str, Any]:
        rows = self.list_domain(project_id, business_domain)
        return rows[0] if rows else {}
