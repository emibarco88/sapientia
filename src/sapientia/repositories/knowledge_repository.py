"""
Module: knowledge_repository.py

Purpose:
Persists acquired knowledge into ekr_knowledge tables.
"""

import json
from sqlalchemy import text

from sapientia.models.knowledge import AcquiredDocument, KnowledgeItem


class KnowledgeRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert_document(self, project_id: int, document: AcquiredDocument) -> int:
        existing = self.connection.execute(
            text("""
                SELECT document_id
                FROM ekr_knowledge.document
                WHERE project_id = :project_id
                  AND source_location = :source_location
            """),
            {
                "project_id": project_id,
                "source_location": document.source_location,
            },
        ).fetchone()

        if existing:
            document_id = existing.document_id

            self.connection.execute(
                text("""
                    UPDATE ekr_knowledge.document
                    SET
                        title = :title,
                        document_type = :document_type,
                        source_type = :source_type,
                        content_hash = :content_hash,
                        updated_at = NOW()
                    WHERE document_id = :document_id
                """),
                {
                    "document_id": document_id,
                    "title": document.title,
                    "document_type": document.document_type,
                    "source_type": document.source_type,
                    "content_hash": document.content_hash,
                },
            )

            self.delete_document_children(document_id)

            return document_id

        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.document
                (
                    project_id,
                    title,
                    document_type,
                    source_type,
                    source_location,
                    content_hash
                )
                VALUES
                (
                    :project_id,
                    :title,
                    :document_type,
                    :source_type,
                    :source_location,
                    :content_hash
                )
                RETURNING document_id
            """),
            {
                "project_id": project_id,
                "title": document.title,
                "document_type": document.document_type,
                "source_type": document.source_type,
                "source_location": document.source_location,
                "content_hash": document.content_hash,
            },
        )

        return result.scalar_one()

    def delete_document_children(self, document_id: int) -> None:
        self.connection.execute(
            text("""
                DELETE FROM ekr_knowledge.knowledge_item
                WHERE knowledge_item_id IN (
                    SELECT knowledge_item_id
                    FROM ekr_knowledge.knowledge_item
                    WHERE project_id IN (
                        SELECT project_id
                        FROM ekr_knowledge.document
                        WHERE document_id = :document_id
                    )
                )
                AND knowledge_item_id IN (
                    SELECT knowledge_item_id
                    FROM ekr_knowledge.knowledge_evidence
                    WHERE document_id = :document_id
                )
            """),
            {"document_id": document_id},
        )

        self.connection.execute(
            text("""
                DELETE FROM ekr_knowledge.document_chunk
                WHERE document_id = :document_id
            """),
            {"document_id": document_id},
        )

    def insert_document_chunk(
        self,
        document_id: int,
        chunk_number: int,
        heading: str | None,
        content: str,
        start_line_number: int | None,
        end_line_number: int | None,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.document_chunk
                (
                    document_id,
                    chunk_number,
                    heading,
                    start_line_number,
                    end_line_number,
                    content
                )
                VALUES
                (
                    :document_id,
                    :chunk_number,
                    :heading,
                    :start_line_number,
                    :end_line_number,
                    :content
                )
                RETURNING document_chunk_id
            """),
            {
                "document_id": document_id,
                "chunk_number": chunk_number,
                "heading": heading,
                "start_line_number": start_line_number,
                "end_line_number": end_line_number,
                "content": content,
            },
        )

        return result.scalar_one()

    def insert_knowledge_item(
        self,
        project_id: int,
        item: KnowledgeItem,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.knowledge_item
                (
                    project_id,
                    knowledge_type,
                    name,
                    description,
                    status,
                    canonical_flag,
                    knowledge_json
                )
                VALUES
                (
                    :project_id,
                    :knowledge_type,
                    :name,
                    :description,
                    :status,
                    :canonical_flag,
                    CAST(:knowledge_json AS JSONB)
                )
                RETURNING knowledge_item_id
            """),
            {
                "project_id": project_id,
                "knowledge_type": item.knowledge_type,
                "name": item.name,
                "description": item.description,
                "status": item.status,
                "canonical_flag": item.canonical_flag,
                "knowledge_json": json.dumps(item.knowledge_json, default=str, allow_nan=False),
            },
        )

        return result.scalar_one()

    def insert_knowledge_evidence(
        self,
        knowledge_item_id: int,
        document_id: int,
        document_chunk_id: int | None,
        evidence,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.knowledge_evidence
                (
                    knowledge_item_id,
                    document_id,
                    document_chunk_id,
                    evidence_text,
                    start_line_number,
                    end_line_number,
                    rule_name,
                    rule_version,
                    extractor_name,
                    extraction_method,
                    evidence_json
                )
                VALUES
                (
                    :knowledge_item_id,
                    :document_id,
                    :document_chunk_id,
                    :evidence_text,
                    :start_line_number,
                    :end_line_number,
                    :rule_name,
                    :rule_version,
                    :extractor_name,
                    :extraction_method,
                    CAST(:evidence_json AS JSONB)
                )
                RETURNING knowledge_evidence_id
            """),
            {
                "knowledge_item_id": knowledge_item_id,
                "document_id": document_id,
                "document_chunk_id": document_chunk_id,
                "evidence_text": evidence.evidence_text,
                "start_line_number": evidence.start_line_number,
                "end_line_number": evidence.end_line_number,
                "rule_name": evidence.rule_name,
                "rule_version": evidence.rule_version,
                "extractor_name": evidence.extractor_name,
                "extraction_method": evidence.extraction_method,
                "evidence_json": json.dumps(evidence.evidence_json, default=str, allow_nan=False),
            },
        )

        return result.scalar_one()

    def insert_knowledge_confidence(
        self,
        knowledge_item_id: int,
        confidence,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.knowledge_confidence
                (
                    knowledge_item_id,
                    rule_score,
                    context_score,
                    structure_score,
                    frequency_score,
                    metadata_match_score,
                    semantic_match_score,
                    ai_validation_score,
                    final_score,
                    confidence_json
                )
                VALUES
                (
                    :knowledge_item_id,
                    :rule_score,
                    :context_score,
                    :structure_score,
                    :frequency_score,
                    :metadata_match_score,
                    :semantic_match_score,
                    :ai_validation_score,
                    :final_score,
                    CAST(:confidence_json AS JSONB)
                )
                RETURNING knowledge_confidence_id
            """),
            {
                "knowledge_item_id": knowledge_item_id,
                "rule_score": confidence.rule_score,
                "context_score": confidence.context_score,
                "structure_score": confidence.structure_score,
                "frequency_score": confidence.frequency_score,
                "metadata_match_score": confidence.metadata_match_score,
                "semantic_match_score": confidence.semantic_match_score,
                "ai_validation_score": confidence.ai_validation_score,
                "final_score": confidence.final_score,
                "confidence_json": json.dumps(confidence.confidence_json, default=str, allow_nan=False),
            },
        )

        return result.scalar_one()