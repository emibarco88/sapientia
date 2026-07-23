"""Persistence adapter for the Enterprise Knowledge Graph Builder."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection


class KnowledgeGraphBuilderRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def create_run(self, project_id: int, business_domain: str) -> int:
        return int(
            self.connection.execute(
                text("""
                    INSERT INTO ekr_understanding.knowledge_graph_build_run
                    (project_id, business_domain)
                    VALUES (:project_id, :business_domain)
                    RETURNING knowledge_graph_build_run_id
                """),
                {"project_id": project_id, "business_domain": business_domain},
            ).scalar_one()
        )

    def set_stage(self, run_id: int, stage: str) -> None:
        self.connection.execute(
            text("""
                UPDATE ekr_understanding.knowledge_graph_build_run
                SET current_stage = :stage, updated_at = NOW()
                WHERE knowledge_graph_build_run_id = :run_id
            """),
            {"run_id": run_id, "stage": stage},
        )

    def complete_run(self, run_id: int, result: dict[str, Any]) -> None:
        self.connection.execute(
            text("""
                UPDATE ekr_understanding.knowledge_graph_build_run
                SET run_status = 'COMPLETED',
                    current_stage = 'COMPLETED',
                    objects_generated = :objects_generated,
                    relationships_generated = :relationships_generated,
                    evidence_links_generated = :evidence_links_generated,
                    warnings_count = :warnings_count,
                    result_json = CAST(:result_json AS JSONB),
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE knowledge_graph_build_run_id = :run_id
            """),
            {
                "run_id": run_id,
                "objects_generated": result["objects_generated"],
                "relationships_generated": result["relationships_generated"],
                "evidence_links_generated": result["evidence_links_generated"],
                "warnings_count": len(result.get("warnings", [])),
                "result_json": json.dumps(result),
            },
        )

    def fail_run(self, run_id: int, error_message: str) -> None:
        self.connection.execute(
            text("""
                UPDATE ekr_understanding.knowledge_graph_build_run
                SET run_status = 'FAILED',
                    current_stage = 'FAILED',
                    error_message = :error_message,
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE knowledge_graph_build_run_id = :run_id
            """),
            {"run_id": run_id, "error_message": error_message[:8000]},
        )

    def get_latest_run(self, project_id: int, business_domain: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            text("""
                SELECT *
                FROM ekr_understanding.knowledge_graph_build_run
                WHERE project_id = :project_id
                  AND UPPER(business_domain) = UPPER(:business_domain)
                ORDER BY started_at DESC
                LIMIT 1
            """),
            {"project_id": project_id, "business_domain": business_domain},
        ).mappings().one_or_none()
        return dict(row) if row else None

    def load_column_evidence(self, project_id: int, business_domain: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            text("""
                SELECT
                    c.column_id,
                    c.name AS column_name,
                    c.data_type,
                    c.ordinal_position,
                    d.dataset_id,
                    d.name AS dataset_name,
                    d.object_type AS dataset_object_type,
                    d.location AS dataset_location,
                    ss.source_system_id,
                    ss.name AS source_system_name,
                    ss.source_type,
                    bd.domain_code,
                    cs.semantic_type,
                    cs.business_meaning,
                    cs.business_domain AS semantic_business_domain,
                    cs.is_key_candidate,
                    cs.key_type,
                    cs.confidence_score,
                    cs.detection_method,
                    cs.reasoning,
                    eo.enterprise_object_id AS evidence_enterprise_object_id
                FROM ekr_core."column" c
                JOIN ekr_core.dataset d
                  ON d.dataset_id = c.dataset_id
                JOIN ekr_core.source_system ss
                  ON ss.source_system_id = d.source_system_id
                LEFT JOIN ekr_business.business_domain bd
                  ON bd.business_domain_id = d.business_domain_id
                LEFT JOIN ekr_semantic.column_semantic cs
                  ON cs.column_id = c.column_id
                LEFT JOIN ekr_understanding.enterprise_object eo
                  ON eo.project_id = ss.project_id
                 AND eo.source_schema = 'ekr_core'
                 AND LOWER(eo.source_table) IN ('column', '"column"')
                 AND eo.source_object_id = c.column_id
                WHERE ss.project_id = :project_id
                  AND UPPER(COALESCE(bd.domain_code, cs.business_domain, '')) =
                      UPPER(:business_domain)
                ORDER BY d.dataset_id, c.ordinal_position, c.column_id
            """),
            {"project_id": project_id, "business_domain": business_domain},
        ).mappings().all()
        return [dict(row) for row in rows]

    def deactivate_generated_scope(self, project_id: int, business_domain: str) -> None:
        self.connection.execute(
            text("""
                UPDATE ekr_understanding.operational_relationship
                SET status = 'INACTIVE', updated_at = NOW()
                WHERE project_id = :project_id
                  AND generation_method = 'KNOWLEDGE_GRAPH_BUILDER'
                  AND (
                    source_enterprise_object_id IN (
                        SELECT enterprise_object_id
                        FROM ekr_understanding.enterprise_object
                        WHERE project_id = :project_id
                          AND UPPER(COALESCE(business_domain, '')) = UPPER(:business_domain)
                          AND object_type_code LIKE 'BUSINESS_%'
                    )
                    OR target_enterprise_object_id IN (
                        SELECT enterprise_object_id
                        FROM ekr_understanding.enterprise_object
                        WHERE project_id = :project_id
                          AND UPPER(COALESCE(business_domain, '')) = UPPER(:business_domain)
                          AND object_type_code LIKE 'BUSINESS_%'
                    )
                  )
            """),
            {"project_id": project_id, "business_domain": business_domain},
        )
        self.connection.execute(
            text("""
                UPDATE ekr_understanding.enterprise_object
                SET status = 'INACTIVE', updated_at = NOW()
                WHERE project_id = :project_id
                  AND UPPER(COALESCE(business_domain, '')) = UPPER(:business_domain)
                  AND object_type_code LIKE 'BUSINESS_%'
                  AND metadata_json ->> 'generated_by' = 'KNOWLEDGE_GRAPH_BUILDER'
            """),
            {"project_id": project_id, "business_domain": business_domain},
        )

    def upsert_business_object(
        self,
        *,
        project_id: int,
        object_type_code: str,
        canonical_name: str,
        canonical_key: str,
        source_object_id: int,
        description: str,
        business_domain: str,
        metadata: dict[str, Any],
    ) -> int:
        return int(
            self.connection.execute(
                text("""
                    INSERT INTO ekr_understanding.enterprise_object
                    (
                        project_id, object_type_code, source_schema, source_table,
                        source_object_id, canonical_name, canonical_key,
                        description, business_domain, status, metadata_json
                    )
                    VALUES
                    (
                        :project_id, :object_type_code, 'ekr_understanding',
                        'knowledge_graph_business_object', :source_object_id,
                        :canonical_name, :canonical_key, :description,
                        :business_domain, 'ACTIVE', CAST(:metadata_json AS JSONB)
                    )
                    ON CONFLICT (project_id, canonical_key)
                    DO UPDATE SET
                        object_type_code = EXCLUDED.object_type_code,
                        canonical_name = EXCLUDED.canonical_name,
                        description = EXCLUDED.description,
                        business_domain = EXCLUDED.business_domain,
                        status = 'ACTIVE',
                        metadata_json = EXCLUDED.metadata_json,
                        updated_at = NOW()
                    RETURNING enterprise_object_id
                """),
                {
                    "project_id": project_id,
                    "object_type_code": object_type_code,
                    "source_object_id": source_object_id,
                    "canonical_name": canonical_name,
                    "canonical_key": canonical_key,
                    "description": description,
                    "business_domain": business_domain,
                    "metadata_json": json.dumps(metadata),
                },
            ).scalar_one()
        )

    def upsert_object_evidence(
        self,
        *,
        business_object_id: int,
        evidence_object_id: int | None,
        source_record_id: int,
        evidence_key: str,
        score: float,
        reasoning: str,
        evidence: dict[str, Any],
        build_run_id: int,
    ) -> None:
        self.connection.execute(
            text("""
                INSERT INTO ekr_understanding.business_object_evidence
                (
                    business_enterprise_object_id,
                    evidence_enterprise_object_id,
                    source_schema,
                    source_table,
                    source_record_id,
                    evidence_type,
                    evidence_key,
                    evidence_score,
                    reasoning,
                    evidence_json,
                    build_run_id
                )
                VALUES
                (
                    :business_object_id,
                    :evidence_object_id,
                    'ekr_core',
                    'column',
                    :source_record_id,
                    'COLUMN_SEMANTIC_EVIDENCE',
                    :evidence_key,
                    :score,
                    :reasoning,
                    CAST(:evidence_json AS JSONB),
                    :build_run_id
                )
                ON CONFLICT (business_enterprise_object_id, evidence_key)
                DO UPDATE SET
                    evidence_enterprise_object_id = EXCLUDED.evidence_enterprise_object_id,
                    evidence_score = EXCLUDED.evidence_score,
                    reasoning = EXCLUDED.reasoning,
                    evidence_json = EXCLUDED.evidence_json,
                    build_run_id = EXCLUDED.build_run_id,
                    updated_at = NOW()
            """),
            {
                "business_object_id": business_object_id,
                "evidence_object_id": evidence_object_id,
                "source_record_id": source_record_id,
                "evidence_key": evidence_key,
                "score": score,
                "reasoning": reasoning,
                "evidence_json": json.dumps(evidence),
                "build_run_id": build_run_id,
            },
        )

    def upsert_relationship(
        self,
        *,
        project_id: int,
        source_id: int,
        target_id: int,
        relationship_type: str,
        confidence: float,
        reasoning: str,
        metadata: dict[str, Any],
        run_id: int,
    ) -> int:
        return int(
            self.connection.execute(
                text("""
                    INSERT INTO ekr_understanding.operational_relationship
                    (
                        project_id,
                        source_enterprise_object_id,
                        target_enterprise_object_id,
                        relationship_type_code,
                        discovery_class,
                        generation_method,
                        confidence_score,
                        status,
                        reasoning,
                        metadata_json,
                        first_discovered_run_id,
                        last_confirmed_run_id
                    )
                    VALUES
                    (
                        :project_id, :source_id, :target_id, :relationship_type,
                        'INFERRED', 'KNOWLEDGE_GRAPH_BUILDER', :confidence,
                        'ACTIVE', :reasoning, CAST(:metadata_json AS JSONB),
                        NULL, NULL
                    )
                    ON CONFLICT
                    (
                        project_id,
                        source_enterprise_object_id,
                        target_enterprise_object_id,
                        relationship_type_code
                    )
                    DO UPDATE SET
                        discovery_class = 'INFERRED',
                        generation_method = 'KNOWLEDGE_GRAPH_BUILDER',
                        confidence_score = EXCLUDED.confidence_score,
                        status = 'ACTIVE',
                        reasoning = EXCLUDED.reasoning,
                        metadata_json = EXCLUDED.metadata_json,
                        updated_at = NOW()
                    RETURNING operational_relationship_id
                """),
                {
                    "project_id": project_id,
                    "source_id": source_id,
                    "target_id": target_id,
                    "relationship_type": relationship_type,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "metadata_json": json.dumps({**metadata, "build_run_id": run_id}),
                },
            ).scalar_one()
        )

    def upsert_relationship_evidence(
        self,
        *,
        relationship_id: int,
        evidence_key: str,
        score: float,
        reasoning: str,
        evidence: dict[str, Any],
    ) -> None:
        self.connection.execute(
            text("""
                INSERT INTO ekr_understanding.relationship_evidence
                (
                    operational_relationship_id,
                    evidence_type,
                    source_schema,
                    source_table,
                    evidence_key,
                    evidence_score,
                    reasoning,
                    evidence_json
                )
                VALUES
                (
                    :relationship_id,
                    'ONTOLOGY_AND_COOCCURRENCE',
                    'ekr_understanding',
                    'knowledge_graph_builder',
                    :evidence_key,
                    :score,
                    :reasoning,
                    CAST(:evidence_json AS JSONB)
                )
                ON CONFLICT (operational_relationship_id, evidence_key)
                DO UPDATE SET
                    evidence_score = EXCLUDED.evidence_score,
                    reasoning = EXCLUDED.reasoning,
                    evidence_json = EXCLUDED.evidence_json
            """),
            {
                "relationship_id": relationship_id,
                "evidence_key": evidence_key,
                "score": score,
                "reasoning": reasoning,
                "evidence_json": json.dumps(evidence),
            },
        )
