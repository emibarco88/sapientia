"""
Module: context_retrieval_repository.py

Purpose:
Retrieves question-relevant Enterprise Intelligence context for AI Advisor.
"""

from sqlalchemy import text


class ContextRetrievalRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_latest_report(self, project_id: int, business_domain: str) -> dict:
        row = self.connection.execute(
            text("""
                SELECT
                    ir.intelligence_report_id,
                    ir.project_id,
                    ir.business_domain_id,
                    bd.domain_code,
                    bd.domain_name,
                    ir.ai_context_json,
                    ir.created_at
                FROM ekr_intelligence.intelligence_report ir
                JOIN ekr_business.business_domain bd
                    ON bd.business_domain_id = ir.business_domain_id
                WHERE ir.project_id = :project_id
                  AND bd.domain_code = :business_domain
                ORDER BY ir.created_at DESC
                LIMIT 1
            """),
            {"project_id": project_id, "business_domain": business_domain},
        ).mappings().fetchone()

        return dict(row) if row else {}

    def search_concepts(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 10,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT
                    ec.enterprise_concept_id,
                    ec.concept_name,
                    ec.concept_type,
                    ec.concept_description,
                    ec.confidence_score,
                    ec.concept_json
                FROM ekr_intelligence.enterprise_concept ec
                JOIN ekr_business.business_domain bd
                    ON bd.business_domain_id = ec.business_domain_id
                WHERE ec.project_id = :project_id
                  AND bd.domain_code = :business_domain
                  AND (
                    LOWER(ec.concept_name) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(ec.concept_description, '')) LIKE ANY(:patterns)
                    OR LOWER(CAST(ec.concept_json AS TEXT)) LIKE ANY(:patterns)
                  )
                ORDER BY ec.confidence_score DESC NULLS LAST
                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": [f"%{keyword.lower()}%" for keyword in keywords],
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def search_findings(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 20,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT
                    f.intelligence_finding_id,
                    f.finding_type,
                    f.finding_title,
                    f.finding_description,
                    f.finding_interpretation,
                    f.confidence_score,
                    f.severity_level,
                    f.finding_json
                FROM ekr_intelligence.intelligence_finding f
                JOIN ekr_business.business_domain bd
                    ON bd.business_domain_id = f.business_domain_id
                WHERE f.project_id = :project_id
                  AND bd.domain_code = :business_domain
                  AND (
                    LOWER(f.finding_title) LIKE ANY(:patterns)
                    OR LOWER(f.finding_description) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(f.finding_interpretation, '')) LIKE ANY(:patterns)
                    OR LOWER(CAST(f.finding_json AS TEXT)) LIKE ANY(:patterns)
                  )
                ORDER BY f.confidence_score DESC NULLS LAST,
                         f.intelligence_finding_id DESC
                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": [f"%{keyword.lower()}%" for keyword in keywords],
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def search_fusion_links(
        self,
        project_id: int,
        business_domain: str,
        keywords: list[str],
        limit: int = 20,
    ) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT *
                FROM ekr_knowledge.vw_fusion_links
                WHERE project_id = :project_id
                  AND domain_code = :business_domain
                  AND (
                    LOWER(COALESCE(dataset_name, '')) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(column_name, '')) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(semantic_type, '')) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(business_meaning, '')) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(knowledge_name, '')) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(knowledge_description, '')) LIKE ANY(:patterns)
                    OR LOWER(COALESCE(reasoning, '')) LIKE ANY(:patterns)
                  )
                ORDER BY fusion_confidence_score DESC NULLS LAST
                LIMIT :limit
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "patterns": [f"%{keyword.lower()}%" for keyword in keywords],
                "limit": limit,
            },
        ).mappings().all()

        return [dict(row) for row in rows]