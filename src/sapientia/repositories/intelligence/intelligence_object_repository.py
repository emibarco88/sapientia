"""Persistence for structured objects within an Enterprise Intelligence Assessment."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text


class EnterpriseIntelligenceObjectRepository:
    def __init__(self, connection):
        self.connection = connection

    def replace_assessment_objects(self, assessment_id: int) -> None:
        self.connection.execute(
            text("DELETE FROM ekr_intelligence.enterprise_intelligence_object WHERE assessment_id = :assessment_id"),
            {"assessment_id": assessment_id},
        )

    def create_object(self, assessment_id: int, payload: dict[str, Any]) -> int:
        row = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_intelligence_object (
                    assessment_id, parent_object_id, object_type, object_key, title,
                    description, interpretation, status, category, severity, priority,
                    confidence_score, probability_score, impact_score, estimated_value,
                    estimated_value_currency, enterprise_object_id, source_object_type,
                    source_object_id, source_schema, source_table, source_record_id,
                    sequence_number, object_json
                ) VALUES (
                    :assessment_id, :parent_object_id, :object_type, :object_key, :title,
                    :description, :interpretation, :status, :category, :severity, :priority,
                    :confidence_score, :probability_score, :impact_score, :estimated_value,
                    :estimated_value_currency, :enterprise_object_id, :source_object_type,
                    :source_object_id, :source_schema, :source_table, :source_record_id,
                    :sequence_number, CAST(:object_json AS JSONB)
                )
                ON CONFLICT (assessment_id, object_key) DO UPDATE SET
                    object_type = EXCLUDED.object_type,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    interpretation = EXCLUDED.interpretation,
                    status = EXCLUDED.status,
                    category = EXCLUDED.category,
                    severity = EXCLUDED.severity,
                    priority = EXCLUDED.priority,
                    confidence_score = EXCLUDED.confidence_score,
                    probability_score = EXCLUDED.probability_score,
                    impact_score = EXCLUDED.impact_score,
                    estimated_value = EXCLUDED.estimated_value,
                    estimated_value_currency = EXCLUDED.estimated_value_currency,
                    enterprise_object_id = EXCLUDED.enterprise_object_id,
                    source_object_type = EXCLUDED.source_object_type,
                    source_object_id = EXCLUDED.source_object_id,
                    source_schema = EXCLUDED.source_schema,
                    source_table = EXCLUDED.source_table,
                    source_record_id = EXCLUDED.source_record_id,
                    sequence_number = EXCLUDED.sequence_number,
                    object_json = EXCLUDED.object_json,
                    updated_at = NOW()
                RETURNING intelligence_object_id
            """),
            {
                "assessment_id": assessment_id,
                "parent_object_id": payload.get("parent_object_id"),
                "object_type": payload["object_type"],
                "object_key": payload["object_key"],
                "title": payload["title"],
                "description": payload.get("description"),
                "interpretation": payload.get("interpretation"),
                "status": payload.get("status") or "ACTIVE",
                "category": payload.get("category"),
                "severity": payload.get("severity"),
                "priority": payload.get("priority"),
                "confidence_score": payload.get("confidence_score"),
                "probability_score": payload.get("probability_score"),
                "impact_score": payload.get("impact_score"),
                "estimated_value": payload.get("estimated_value"),
                "estimated_value_currency": payload.get("estimated_value_currency"),
                "enterprise_object_id": payload.get("enterprise_object_id"),
                "source_object_type": payload.get("source_object_type"),
                "source_object_id": payload.get("source_object_id"),
                "source_schema": payload.get("source_schema"),
                "source_table": payload.get("source_table"),
                "source_record_id": payload.get("source_record_id"),
                "sequence_number": payload.get("sequence_number") or 0,
                "object_json": json.dumps(payload.get("object_json") or {}, default=str),
            },
        ).scalar_one()
        return int(row)

    def create_evidence(self, assessment_id: int, object_id: int, payload: dict[str, Any]) -> int:
        row = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_intelligence_evidence_reference (
                    assessment_id, intelligence_object_id, evidence_type, evidence_source,
                    evidence_text, confidence_score, enterprise_object_id, dataset_id,
                    column_id, knowledge_item_id, source_schema, source_table,
                    source_record_id, evidence_json
                ) VALUES (
                    :assessment_id, :object_id, :evidence_type, :evidence_source,
                    :evidence_text, :confidence_score, :enterprise_object_id, :dataset_id,
                    :column_id, :knowledge_item_id, :source_schema, :source_table,
                    :source_record_id, CAST(:evidence_json AS JSONB)
                ) RETURNING intelligence_evidence_id
            """),
            {
                "assessment_id": assessment_id,
                "object_id": object_id,
                "evidence_type": payload.get("evidence_type") or "SOURCE",
                "evidence_source": payload.get("evidence_source"),
                "evidence_text": payload.get("evidence_text"),
                "confidence_score": payload.get("confidence_score"),
                "enterprise_object_id": payload.get("enterprise_object_id"),
                "dataset_id": payload.get("dataset_id"),
                "column_id": payload.get("column_id"),
                "knowledge_item_id": payload.get("knowledge_item_id"),
                "source_schema": payload.get("source_schema"),
                "source_table": payload.get("source_table"),
                "source_record_id": payload.get("source_record_id"),
                "evidence_json": json.dumps(payload.get("evidence_json") or payload, default=str),
            },
        ).scalar_one()
        return int(row)

    def create_relation(
        self,
        assessment_id: int,
        source_object_id: int,
        target_object_id: int,
        relation_type: str,
        confidence_score: float | None = None,
        relation_json: dict[str, Any] | None = None,
    ) -> int:
        row = self.connection.execute(
            text("""
                INSERT INTO ekr_intelligence.enterprise_intelligence_object_relation (
                    assessment_id, source_intelligence_object_id,
                    target_intelligence_object_id, relation_type,
                    confidence_score, relation_json
                ) VALUES (
                    :assessment_id, :source_object_id, :target_object_id,
                    :relation_type, :confidence_score, CAST(:relation_json AS JSONB)
                )
                ON CONFLICT (assessment_id, source_intelligence_object_id,
                             target_intelligence_object_id, relation_type)
                DO UPDATE SET confidence_score = EXCLUDED.confidence_score,
                              relation_json = EXCLUDED.relation_json
                RETURNING intelligence_relation_id
            """),
            {
                "assessment_id": assessment_id,
                "source_object_id": source_object_id,
                "target_object_id": target_object_id,
                "relation_type": relation_type,
                "confidence_score": confidence_score,
                "relation_json": json.dumps(relation_json or {}, default=str),
            },
        ).scalar_one()
        return int(row)

    def list_objects(
        self,
        assessment_id: int,
        project_id: int,
        object_type: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            text("""
                SELECT o.*,
                       COUNT(DISTINCT e.intelligence_evidence_id)::INTEGER AS evidence_count,
                       COUNT(DISTINCT r1.intelligence_relation_id)::INTEGER AS outgoing_relation_count,
                       COUNT(DISTINCT r2.intelligence_relation_id)::INTEGER AS incoming_relation_count
                FROM ekr_intelligence.enterprise_intelligence_object o
                JOIN ekr_intelligence.enterprise_intelligence_assessment a
                  ON a.assessment_id = o.assessment_id
                LEFT JOIN ekr_intelligence.enterprise_intelligence_evidence_reference e
                  ON e.intelligence_object_id = o.intelligence_object_id
                LEFT JOIN ekr_intelligence.enterprise_intelligence_object_relation r1
                  ON r1.source_intelligence_object_id = o.intelligence_object_id
                LEFT JOIN ekr_intelligence.enterprise_intelligence_object_relation r2
                  ON r2.target_intelligence_object_id = o.intelligence_object_id
                WHERE o.assessment_id = :assessment_id
                  AND a.project_id = :project_id
                  AND (:object_type IS NULL OR o.object_type = :object_type)
                GROUP BY o.intelligence_object_id
                ORDER BY o.object_type, o.sequence_number, o.intelligence_object_id
            """),
            {"assessment_id": assessment_id, "project_id": project_id, "object_type": object_type},
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_object(self, object_id: int, project_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            text("""
                SELECT o.*
                FROM ekr_intelligence.enterprise_intelligence_object o
                JOIN ekr_intelligence.enterprise_intelligence_assessment a
                  ON a.assessment_id = o.assessment_id
                WHERE o.intelligence_object_id = :object_id
                  AND a.project_id = :project_id
            """),
            {"object_id": object_id, "project_id": project_id},
        ).mappings().fetchone()
        if not row:
            return {}
        result = dict(row)
        result["evidence"] = [dict(item) for item in self.connection.execute(
            text("""
                SELECT * FROM ekr_intelligence.enterprise_intelligence_evidence_reference
                WHERE intelligence_object_id = :object_id
                ORDER BY intelligence_evidence_id
            """), {"object_id": object_id}
        ).mappings().all()]
        result["relations"] = [dict(item) for item in self.connection.execute(
            text("""
                SELECT r.*, s.title AS source_title, s.object_type AS source_type,
                       t.title AS target_title, t.object_type AS target_type
                FROM ekr_intelligence.enterprise_intelligence_object_relation r
                JOIN ekr_intelligence.enterprise_intelligence_object s
                  ON s.intelligence_object_id = r.source_intelligence_object_id
                JOIN ekr_intelligence.enterprise_intelligence_object t
                  ON t.intelligence_object_id = r.target_intelligence_object_id
                WHERE r.source_intelligence_object_id = :object_id
                   OR r.target_intelligence_object_id = :object_id
                ORDER BY r.intelligence_relation_id
            """), {"object_id": object_id}
        ).mappings().all()]
        return result

    def summary(self, assessment_id: int, project_id: int) -> dict[str, Any]:
        rows = self.connection.execute(
            text("""
                SELECT o.object_type, COUNT(*)::INTEGER AS object_count,
                       COUNT(*) FILTER (WHERE o.severity IN ('HIGH', 'CRITICAL'))::INTEGER AS high_severity_count,
                       COALESCE(SUM(evidence_counts.evidence_count), 0)::INTEGER AS evidence_count
                FROM ekr_intelligence.enterprise_intelligence_object o
                JOIN ekr_intelligence.enterprise_intelligence_assessment a
                  ON a.assessment_id = o.assessment_id
                LEFT JOIN (
                    SELECT intelligence_object_id, COUNT(*)::INTEGER AS evidence_count
                    FROM ekr_intelligence.enterprise_intelligence_evidence_reference
                    GROUP BY intelligence_object_id
                ) evidence_counts ON evidence_counts.intelligence_object_id = o.intelligence_object_id
                WHERE o.assessment_id = :assessment_id AND a.project_id = :project_id
                GROUP BY o.object_type
                ORDER BY o.object_type
            """),
            {"assessment_id": assessment_id, "project_id": project_id},
        ).mappings().all()
        by_type = {row["object_type"]: dict(row) for row in rows}
        return {
            "assessment_id": assessment_id,
            "total_objects": sum(int(row["object_count"]) for row in rows),
            "total_evidence": sum(int(row["evidence_count"]) for row in rows),
            "by_type": by_type,
        }
