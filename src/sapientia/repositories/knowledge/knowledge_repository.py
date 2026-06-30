"""
Module: knowledge_repository.py

Purpose:
Persists acquired enterprise knowledge, document chunks, evidence,
confidence scores, and knowledge relationships into ekr_knowledge.
"""

import json
from sqlalchemy import text


class KnowledgeRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert_document(
        self,
        project_id: int,
        document,
        business_domain_id: int,
    ) -> int:
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
            self.connection.execute(
                text("""
                    UPDATE ekr_knowledge.document
                    SET
                        business_domain_id = :business_domain_id,
                        title = :title,
                        document_type = :document_type,
                        source_type = :source_type,
                        content_hash = :content_hash,
                        updated_at = NOW()
                    WHERE document_id = :document_id
                """),
                {
                    "document_id": existing.document_id,
                    "business_domain_id": business_domain_id,
                    "title": document.title,
                    "document_type": document.document_type,
                    "source_type": document.source_type,
                    "content_hash": document.content_hash,
                },
            )

            return existing.document_id

        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.document
                (
                    project_id,
                    business_domain_id,
                    title,
                    document_type,
                    source_type,
                    source_location,
                    content_hash
                )
                VALUES
                (
                    :project_id,
                    :business_domain_id,
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
                "business_domain_id": business_domain_id,
                "title": document.title,
                "document_type": document.document_type,
                "source_type": document.source_type,
                "source_location": document.source_location,
                "content_hash": document.content_hash,
            },
        )

        return result.scalar_one()

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
                    content,
                    start_line_number,
                    end_line_number
                )
                VALUES
                (
                    :document_id,
                    :chunk_number,
                    :heading,
                    :content,
                    :start_line_number,
                    :end_line_number
                )
                ON CONFLICT (document_id, chunk_number)
                DO UPDATE SET
                    heading = EXCLUDED.heading,
                    content = EXCLUDED.content,
                    start_line_number = EXCLUDED.start_line_number,
                    end_line_number = EXCLUDED.end_line_number
                RETURNING document_chunk_id
            """),
            {
                "document_id": document_id,
                "chunk_number": chunk_number,
                "heading": heading,
                "content": content,
                "start_line_number": start_line_number,
                "end_line_number": end_line_number,
            },
        )

        return result.scalar_one()

    def insert_knowledge_item(
        self,
        project_id: int,
        item,
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
                "status": getattr(item, "status", "ACTIVE"),
                "canonical_flag": getattr(item, "canonical_flag", True),
                "knowledge_json": json.dumps(
                    getattr(item, "knowledge_json", {}),
                    default=str,
                ),
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
                "evidence_json": json.dumps(
                    getattr(evidence, "evidence_json", {}),
                    default=str,
                ),
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
                "confidence_json": json.dumps(
                    getattr(confidence, "confidence_json", {}),
                    default=str,
                ),
            },
        )

        return result.scalar_one()

    def insert_knowledge_relationship(
        self,
        source_knowledge_item_id: int,
        target_knowledge_item_id: int,
        relationship_type: str,
        confidence_score: float | None = None,
        reasoning: str | None = None,
        relationship_json: dict | None = None,
    ) -> int:
        result = self.connection.execute(
            text("""
                INSERT INTO ekr_knowledge.knowledge_relationship
                (
                    source_knowledge_item_id,
                    target_knowledge_item_id,
                    relationship_type,
                    confidence_score,
                    reasoning,
                    relationship_json
                )
                VALUES
                (
                    :source_knowledge_item_id,
                    :target_knowledge_item_id,
                    :relationship_type,
                    :confidence_score,
                    :reasoning,
                    CAST(:relationship_json AS JSONB)
                )
                RETURNING knowledge_relationship_id
            """),
            {
                "source_knowledge_item_id": source_knowledge_item_id,
                "target_knowledge_item_id": target_knowledge_item_id,
                "relationship_type": relationship_type,
                "confidence_score": confidence_score,
                "reasoning": reasoning,
                "relationship_json": json.dumps(
                    relationship_json or {},
                    default=str,
                ),
            },
        )

        return result.scalar_one()