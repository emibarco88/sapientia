"""
Module: semantic_repository.py

Purpose:
Persists semantic analysis results into omd_semantic tables.
"""

import json
from sqlalchemy import text
from sapientia.models.semantic import ColumnSemantic


class SemanticRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_columns_for_dataset(self, dataset_id: int) -> list[dict]:
        sql = text("""
            SELECT
                c.column_id,
                c.name AS column_name,
                c.data_type AS source_data_type,
                cp.inferred_data_type,
                cp.null_percentage,
                cp.unique_percentage,
                cp.completeness_score,
                cp.quality_score,
                cp.pattern_summary,
                cp.numeric_summary,
                cp.date_summary,
                cp.top_values
            FROM omd_core."column" c
            LEFT JOIN omd_profile.column_profile cp
                ON cp.column_id = c.column_id
            WHERE c.dataset_id = :dataset_id
            ORDER BY c.ordinal_position
        """)

        rows = self.connection.execute(sql, {"dataset_id": dataset_id}).fetchall()

        return [dict(row._mapping) for row in rows]

    def upsert_column_semantic(self, semantic: ColumnSemantic) -> None:
        sql = text("""
            INSERT INTO omd_semantic.column_semantic
            (
                column_id,
                semantic_type,
                business_meaning,
                business_domain,
                is_pii,
                sensitivity_level,
                is_key_candidate,
                key_type,
                confidence_score,
                detection_method,
                reasoning,
                semantic_json,
                updated_at
            )
            VALUES
            (
                :column_id,
                :semantic_type,
                :business_meaning,
                :business_domain,
                :is_pii,
                :sensitivity_level,
                :is_key_candidate,
                :key_type,
                :confidence_score,
                :detection_method,
                :reasoning,
                CAST(:semantic_json AS JSONB),
                NOW()
            )
            ON CONFLICT (column_id)
            DO UPDATE SET
                semantic_type = EXCLUDED.semantic_type,
                business_meaning = EXCLUDED.business_meaning,
                business_domain = EXCLUDED.business_domain,
                is_pii = EXCLUDED.is_pii,
                sensitivity_level = EXCLUDED.sensitivity_level,
                is_key_candidate = EXCLUDED.is_key_candidate,
                key_type = EXCLUDED.key_type,
                confidence_score = EXCLUDED.confidence_score,
                detection_method = EXCLUDED.detection_method,
                reasoning = EXCLUDED.reasoning,
                semantic_json = EXCLUDED.semantic_json,
                updated_at = NOW()
        """)

        self.connection.execute(
            sql,
            {
                "column_id": semantic.column_id,
                "semantic_type": semantic.semantic_type,
                "business_meaning": semantic.business_meaning,
                "business_domain": semantic.business_domain,
                "is_pii": semantic.is_pii,
                "sensitivity_level": semantic.sensitivity_level,
                "is_key_candidate": semantic.is_key_candidate,
                "key_type": semantic.key_type,
                "confidence_score": semantic.confidence_score,
                "detection_method": semantic.detection_method,
                "reasoning": semantic.reasoning,
                "semantic_json": json.dumps(semantic.semantic_json, default=str, allow_nan=False),
            },
        )