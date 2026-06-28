"""
Module: knowledge_fusion_repository.py

Purpose:
Reads EKR Core, Profile, Semantic and Knowledge data, and persists
resolved knowledge-to-asset links.
"""

import json
from sqlalchemy import text


class KnowledgeFusionRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_knowledge_items(
        self,
        project_id: int,
        document_id: int | None = None,
    ) -> list[dict]:
        sql = """
            SELECT
                ki.knowledge_item_id,
                ki.knowledge_type,
                ki.name,
                ki.description,
                ki.knowledge_json,
                kc.final_score AS knowledge_confidence_score
            FROM ekr_knowledge.knowledge_item ki
            LEFT JOIN ekr_knowledge.knowledge_confidence kc
                ON kc.knowledge_item_id = ki.knowledge_item_id
            WHERE ki.project_id = :project_id
              AND ki.status = 'ACTIVE'
        """

        params = {"project_id": project_id}

        if document_id is not None:
            sql += """
              AND EXISTS (
                  SELECT 1
                  FROM ekr_knowledge.knowledge_evidence ke
                  WHERE ke.knowledge_item_id = ki.knowledge_item_id
                    AND ke.document_id = :document_id
              )
            """
            params["document_id"] = document_id

        rows = self.connection.execute(text(sql), params).fetchall()

        return [dict(row._mapping) for row in rows]

    def get_data_assets(
        self,
        project_id: int,
        dataset_id: int | None = None,
    ) -> list[dict]:
        sql = """
            SELECT
                d.dataset_id,
                d.name AS dataset_name,
                d.object_type,
                c.column_id,
                c.name AS column_name,
                c.data_type AS source_data_type,

                cp.inferred_data_type,
                cp.null_percentage,
                cp.unique_percentage,
                cp.quality_score,

                cs.semantic_type,
                cs.business_meaning,
                cs.business_domain,
                cs.is_pii,
                cs.is_key_candidate,
                cs.confidence_score AS semantic_confidence_score
            FROM ekr_core.source_system ss
            JOIN ekr_core.dataset d
                ON d.source_system_id = ss.source_system_id
            JOIN ekr_core."column" c
                ON c.dataset_id = d.dataset_id
            LEFT JOIN ekr_profile.column_profile cp
                ON cp.column_id = c.column_id
            LEFT JOIN ekr_semantic.column_semantic cs
                ON cs.column_id = c.column_id
            WHERE ss.project_id = :project_id
        """

        params = {"project_id": project_id}

        if dataset_id is not None:
            sql += """
              AND d.dataset_id = :dataset_id
            """
            params["dataset_id"] = dataset_id

        sql += """
            ORDER BY d.dataset_id, c.ordinal_position
        """

        rows = self.connection.execute(text(sql), params).fetchall()

        return [dict(row._mapping) for row in rows]

    def delete_existing_links(
        self,
        project_id: int,
        document_id: int | None = None,
        dataset_id: int | None = None,
    ) -> None:
        sql = """
            DELETE FROM ekr_knowledge.knowledge_asset_link kal
            USING ekr_knowledge.knowledge_item ki
            WHERE kal.knowledge_item_id = ki.knowledge_item_id
              AND ki.project_id = :project_id
        """

        params = {"project_id": project_id}

        if document_id is not None:
            sql += """
              AND EXISTS (
                  SELECT 1
                  FROM ekr_knowledge.knowledge_evidence ke
                  WHERE ke.knowledge_item_id = ki.knowledge_item_id
                    AND ke.document_id = :document_id
              )
            """
            params["document_id"] = document_id

        if dataset_id is not None:
            sql += """
              AND kal.dataset_id = :dataset_id
            """
            params["dataset_id"] = dataset_id

        self.connection.execute(text(sql), params)

    def insert_asset_link(self, link: dict) -> None:
        self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.knowledge_asset_link
                (
                    knowledge_item_id,
                    dataset_id,
                    column_id,
                    link_type,
                    resolution_status,
                    match_strategy,
                    confidence_score,
                    reasoning,
                    reasoning_json,
                    created_by_engine,
                    engine_version
                )
                VALUES
                (
                    :knowledge_item_id,
                    :dataset_id,
                    :column_id,
                    :link_type,
                    :resolution_status,
                    :match_strategy,
                    :confidence_score,
                    :reasoning,
                    CAST(:reasoning_json AS JSONB),
                    :created_by_engine,
                    :engine_version
                )
            """),
            {
                "knowledge_item_id": link["knowledge_item_id"],
                "dataset_id": link.get("dataset_id"),
                "column_id": link.get("column_id"),
                "link_type": link["link_type"],
                "resolution_status": link["resolution_status"],
                "match_strategy": link["match_strategy"],
                "confidence_score": link["confidence_score"],
                "reasoning": link["reasoning"],
                "reasoning_json": json.dumps(link["reasoning_json"], default=str, allow_nan=False),
                "created_by_engine": link["created_by_engine"],
                "engine_version": link["engine_version"],
            },
        )