"""
Module: enterprise_concept_repository.py

Purpose:
Reads semantic, knowledge and fusion outputs and persists consolidated
enterprise concepts into ekr_intelligence.
"""

import json
from sqlalchemy import text


class EnterpriseConceptRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_business_domain(self, business_domain: str) -> dict:
        row = self.connection.execute(
            text("""
                SELECT business_domain_id, domain_code, domain_name
                FROM ekr_business.business_domain
                WHERE domain_code = :business_domain
            """),
            {"business_domain": business_domain},
        ).mappings().fetchone()

        return dict(row) if row else {}

    def get_semantic_columns(self, project_id: int, business_domain: str) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT
                    d.dataset_id,
                    d.name AS dataset_name,
                    c.column_id,
                    c.name AS column_name,
                    cs.semantic_type,
                    cs.business_meaning,
                    cs.is_key_candidate,
                    cs.is_pii,
                    cs.confidence_score
                FROM ekr_semantic.column_semantic cs
                JOIN ekr_core."column" c
                    ON c.column_id = cs.column_id
                JOIN ekr_core.dataset d
                    ON d.dataset_id = c.dataset_id
                JOIN ekr_core.source_system ss
                    ON ss.source_system_id = d.source_system_id
                JOIN ekr_business.business_domain bd
                    ON bd.business_domain_id = d.business_domain_id
                WHERE ss.project_id = :project_id
                  AND bd.domain_code = :business_domain
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def get_knowledge_items(self, project_id: int, business_domain: str) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT DISTINCT
                    ki.knowledge_item_id,
                    ki.knowledge_type,
                    ki.name,
                    ki.description
                FROM ekr_knowledge.knowledge_item ki
                JOIN ekr_knowledge.knowledge_evidence ke
                    ON ke.knowledge_item_id = ki.knowledge_item_id
                JOIN ekr_knowledge.document d
                    ON d.document_id = ke.document_id
                JOIN ekr_business.business_domain bd
                    ON bd.business_domain_id = d.business_domain_id
                WHERE ki.project_id = :project_id
                  AND bd.domain_code = :business_domain
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def get_intelligence_links(self, project_id: int, business_domain: str) -> list[dict]:
        rows = self.connection.execute(
            text("""
                SELECT *
                FROM ekr_knowledge.vw_fusion_links
                WHERE project_id = :project_id
                  AND domain_code = :business_domain
            """),
            {
                "project_id": project_id,
                "business_domain": business_domain,
            },
        ).mappings().all()

        return [dict(row) for row in rows]

    def delete_existing_concepts(
        self,
        project_id: int,
        business_domain_id: int | None,
    ) -> None:
        self.connection.execute(
            text("""
                DELETE FROM ekr_intelligence.enterprise_concept
                WHERE project_id = :project_id
                  AND (
                        business_domain_id = :business_domain_id
                        OR (:business_domain_id IS NULL AND business_domain_id IS NULL)
                  )
            """),
            {
                "project_id": project_id,
                "business_domain_id": business_domain_id,
            },
        )

    def create_concept(
        self,
        project_id: int,
        business_domain_id: int | None,
        concept: dict,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_concept
                (
                    project_id,
                    business_domain_id,
                    concept_name,
                    concept_type,
                    concept_description,
                    confidence_score,
                    concept_json
                )
                VALUES
                (
                    :project_id,
                    :business_domain_id,
                    :concept_name,
                    :concept_type,
                    :concept_description,
                    :confidence_score,
                    CAST(:concept_json AS JSONB)
                )
                RETURNING enterprise_concept_id
            """),
            {
                "project_id": project_id,
                "business_domain_id": business_domain_id,
                "concept_name": concept["concept_name"],
                "concept_type": concept["concept_type"],
                "concept_description": concept.get("concept_description"),
                "confidence_score": concept.get("confidence_score"),
                "concept_json": json.dumps(concept, default=str),
            },
        )

        return result.scalar_one()

    def create_evidence(
        self,
        enterprise_concept_id: int,
        evidence: dict,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_concept_evidence
                (
                    enterprise_concept_id,
                    evidence_type,
                    evidence_source,
                    evidence_text,
                    dataset_id,
                    column_id,
                    knowledge_item_id,
                    intelligence_link_id,
                    confidence_score,
                    evidence_json
                )
                VALUES
                (
                    :enterprise_concept_id,
                    :evidence_type,
                    :evidence_source,
                    :evidence_text,
                    :dataset_id,
                    :column_id,
                    :knowledge_item_id,
                    :intelligence_link_id,
                    :confidence_score,
                    CAST(:evidence_json AS JSONB)
                )
                RETURNING enterprise_concept_evidence_id
            """),
            {
                "enterprise_concept_id": enterprise_concept_id,
                "evidence_type": evidence.get("evidence_type"),
                "evidence_source": evidence.get("evidence_source"),
                "evidence_text": evidence.get("evidence_text"),
                "dataset_id": evidence.get("dataset_id"),
                "column_id": evidence.get("column_id"),
                "knowledge_item_id": evidence.get("knowledge_item_id"),
                "intelligence_link_id": evidence.get("intelligence_link_id"),
                "confidence_score": evidence.get("confidence_score"),
                "evidence_json": json.dumps(evidence, default=str),
            },
        )

        return result.scalar_one()