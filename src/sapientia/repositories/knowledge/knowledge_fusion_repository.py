"""
Module: knowledge_fusion_repository.py

Purpose:
Repository for Knowledge Fusion.

This repository keeps compatibility with the legacy
knowledge_asset_link table while also persisting the new
intelligence_link model.
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
                ki.project_id,
                ki.knowledge_type,
                ki.name,
                ki.description,
                ki.knowledge_json
            FROM ekr_knowledge.knowledge_item ki
            WHERE ki.project_id = :project_id
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

        rows = self.connection.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows]

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
                d.location,
                d.business_domain_id,
                bd.domain_code,
                bd.domain_name,
                c.column_id,
                c.name AS column_name,
                c.data_type,
                c.ordinal_position,
                cs.semantic_type,
                cs.business_meaning,
                cs.business_domain AS semantic_business_domain,
                cs.is_pii,
                cs.sensitivity_level,
                cs.is_key_candidate,
                cs.key_type,
                cs.confidence_score AS semantic_confidence_score
            FROM ekr_core.dataset d
            JOIN ekr_core.source_system ss
                ON ss.source_system_id = d.source_system_id
            LEFT JOIN ekr_business.business_domain bd
                ON bd.business_domain_id = d.business_domain_id
            LEFT JOIN ekr_core."column" c
                ON c.dataset_id = d.dataset_id
            LEFT JOIN ekr_semantic.column_semantic cs
                ON cs.column_id = c.column_id
            WHERE ss.project_id = :project_id
        """

        params = {"project_id": project_id}

        if dataset_id is not None:
            sql += " AND d.dataset_id = :dataset_id"
            params["dataset_id"] = dataset_id

        rows = self.connection.execute(text(sql), params).mappings().all()
        return [dict(row) for row in rows]

    def delete_existing_links(
        self,
        project_id: int,
        dataset_id: int | None = None,
        document_id: int | None = None,
    ) -> None:
        knowledge_item_ids = self._get_scoped_knowledge_item_ids(
            project_id=project_id,
            document_id=document_id,
        )

        if not knowledge_item_ids:
            return

        params = {
            "project_id": project_id,
            "knowledge_item_ids": tuple(knowledge_item_ids),
        }

        legacy_sql = """
            DELETE FROM ekr_knowledge.knowledge_asset_link
            WHERE knowledge_item_id IN :knowledge_item_ids
        """

        intelligence_sql = """
            DELETE FROM ekr_knowledge.intelligence_link
            WHERE project_id = :project_id
              AND knowledge_item_id IN :knowledge_item_ids
        """

        if dataset_id is not None:
            legacy_sql += " AND dataset_id = :dataset_id"
            intelligence_sql += " AND dataset_id = :dataset_id"
            params["dataset_id"] = dataset_id

        self.connection.execute(
            text(legacy_sql),
            params,
        )

        self.connection.execute(
            text(intelligence_sql),
            params,
        )

    def insert_asset_link(self, link) -> int:
        """
        Inserts a Fusion link into both:
        - legacy ekr_knowledge.knowledge_asset_link
        - new ekr_knowledge.intelligence_link

        This preserves existing behaviour while enabling the new Fusion model.
        """

        knowledge_item_id = self._value(link, "knowledge_item_id")
        dataset_id = self._value(link, "dataset_id")
        column_id = self._value(link, "column_id")
        link_type = self._value(link, "link_type", "KNOWLEDGE_ASSET_LINK")
        resolution_status = self._value(link, "resolution_status", "RESOLVED")
        match_strategy = self._value(link, "match_strategy", "UNKNOWN")
        confidence_score = self._value(link, "confidence_score")
        reasoning = self._value(link, "reasoning")
        reasoning_json = self._value(link, "reasoning_json", {})
        created_by_engine = self._value(
            link,
            "created_by_engine",
            "Knowledge Fusion Engine",
        )
        engine_version = self._value(link, "engine_version", "1.0")

        legacy_link_id = self._insert_legacy_asset_link(
            knowledge_item_id=knowledge_item_id,
            dataset_id=dataset_id,
            column_id=column_id,
            link_type=link_type,
            resolution_status=resolution_status,
            match_strategy=match_strategy,
            confidence_score=confidence_score,
            reasoning=reasoning,
            reasoning_json=reasoning_json,
            created_by_engine=created_by_engine,
            engine_version=engine_version,
        )

        project_id, business_domain_id = self._resolve_project_and_domain(
            knowledge_item_id=knowledge_item_id,
            dataset_id=dataset_id,
        )

        intelligence_link_id = self._insert_intelligence_link(
            project_id=project_id,
            business_domain_id=business_domain_id,
            knowledge_item_id=knowledge_item_id,
            dataset_id=dataset_id,
            column_id=column_id,
            link_type=link_type,
            resolution_status=resolution_status,
            match_strategy=match_strategy,
            confidence_score=confidence_score,
            reasoning=reasoning,
            reasoning_json=reasoning_json,
            created_by_engine=created_by_engine,
            engine_version=engine_version,
        )

        self._insert_intelligence_link_evidence(
            intelligence_link_id=intelligence_link_id,
            evidence_type="FUSION_REASONING",
            evidence_source=created_by_engine,
            evidence_text=reasoning,
            evidence_json=reasoning_json,
            confidence_contribution=confidence_score,
        )

        return legacy_link_id

    def _insert_legacy_asset_link(
        self,
        knowledge_item_id: int,
        dataset_id: int | None,
        column_id: int | None,
        link_type: str,
        resolution_status: str,
        match_strategy: str,
        confidence_score: float | None,
        reasoning: str | None,
        reasoning_json: dict | str | None,
        created_by_engine: str,
        engine_version: str,
    ) -> int:
        result = self.connection.execute(
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
                RETURNING knowledge_asset_link_id
            """),
            {
                "knowledge_item_id": knowledge_item_id,
                "dataset_id": dataset_id,
                "column_id": column_id,
                "link_type": link_type,
                "resolution_status": resolution_status,
                "match_strategy": match_strategy,
                "confidence_score": confidence_score,
                "reasoning": reasoning,
                "reasoning_json": self._json(reasoning_json),
                "created_by_engine": created_by_engine,
                "engine_version": engine_version,
            },
        )

        return result.scalar_one()

    def _insert_intelligence_link(
        self,
        project_id: int,
        business_domain_id: int | None,
        knowledge_item_id: int,
        dataset_id: int | None,
        column_id: int | None,
        link_type: str,
        resolution_status: str,
        match_strategy: str,
        confidence_score: float | None,
        reasoning: str | None,
        reasoning_json: dict | str | None,
        created_by_engine: str,
        engine_version: str,
    ) -> int:
        target_object_type = "COLUMN" if column_id is not None else "DATASET"
        target_object_id = column_id if column_id is not None else dataset_id

        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.intelligence_link
                (
                    project_id,
                    business_domain_id,
                    source_object_type,
                    source_object_id,
                    target_object_type,
                    target_object_id,
                    dataset_id,
                    column_id,
                    knowledge_item_id,
                    link_type,
                    resolution_status,
                    match_strategy,
                    confidence_score,
                    trust_level,
                    reasoning,
                    reasoning_json,
                    created_by_engine,
                    engine_version
                )
                VALUES
                (
                    :project_id,
                    :business_domain_id,
                    'KNOWLEDGE_ITEM',
                    :knowledge_item_id,
                    :target_object_type,
                    :target_object_id,
                    :dataset_id,
                    :column_id,
                    :knowledge_item_id,
                    :link_type,
                    :resolution_status,
                    :match_strategy,
                    :confidence_score,
                    'INFERRED',
                    :reasoning,
                    CAST(:reasoning_json AS JSONB),
                    :created_by_engine,
                    :engine_version
                )
                RETURNING intelligence_link_id
            """),
            {
                "project_id": project_id,
                "business_domain_id": business_domain_id,
                "knowledge_item_id": knowledge_item_id,
                "target_object_type": target_object_type,
                "target_object_id": target_object_id,
                "dataset_id": dataset_id,
                "column_id": column_id,
                "link_type": link_type,
                "resolution_status": resolution_status,
                "match_strategy": match_strategy,
                "confidence_score": confidence_score,
                "reasoning": reasoning,
                "reasoning_json": self._json(reasoning_json),
                "created_by_engine": created_by_engine,
                "engine_version": engine_version,
            },
        )

        return result.scalar_one()

    def _insert_intelligence_link_evidence(
        self,
        intelligence_link_id: int,
        evidence_type: str,
        evidence_source: str,
        evidence_text: str | None,
        evidence_json: dict | str | None,
        confidence_contribution: float | None,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.intelligence_link_evidence
                (
                    intelligence_link_id,
                    evidence_type,
                    evidence_source,
                    evidence_text,
                    evidence_json,
                    confidence_contribution
                )
                VALUES
                (
                    :intelligence_link_id,
                    :evidence_type,
                    :evidence_source,
                    :evidence_text,
                    CAST(:evidence_json AS JSONB),
                    :confidence_contribution
                )
                RETURNING intelligence_link_evidence_id
            """),
            {
                "intelligence_link_id": intelligence_link_id,
                "evidence_type": evidence_type,
                "evidence_source": evidence_source,
                "evidence_text": evidence_text,
                "evidence_json": self._json(evidence_json),
                "confidence_contribution": confidence_contribution,
            },
        )

        return result.scalar_one()

    def _resolve_project_and_domain(
        self,
        knowledge_item_id: int,
        dataset_id: int | None,
    ) -> tuple[int, int | None]:
        row = self.connection.execute(
            text("""
                SELECT
                    ki.project_id,
                    d.business_domain_id
                FROM ekr_knowledge.knowledge_item ki
                LEFT JOIN ekr_core.dataset d
                    ON d.dataset_id = :dataset_id
                WHERE ki.knowledge_item_id = :knowledge_item_id
            """),
            {
                "knowledge_item_id": knowledge_item_id,
                "dataset_id": dataset_id,
            },
        ).fetchone()

        if not row:
            raise ValueError(
                f"Unable to resolve project/domain for knowledge_item_id={knowledge_item_id}"
            )

        return row.project_id, row.business_domain_id

    def _get_scoped_knowledge_item_ids(
        self,
        project_id: int,
        document_id: int | None,
    ) -> list[int]:
        sql = """
            SELECT DISTINCT ki.knowledge_item_id
            FROM ekr_knowledge.knowledge_item ki
            WHERE ki.project_id = :project_id
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
        return [row.knowledge_item_id for row in rows]

    def _value(self, obj, key: str, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)

    def _json(self, value) -> str:
        if value is None:
            return "{}"

        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except json.JSONDecodeError:
                return json.dumps({"value": value}, default=str)

        return json.dumps(value, default=str)