"""
Module: knowledge_engine.py

Purpose:
Coordinates acquisition of enterprise knowledge from external sources
into the Enterprise Knowledge Repository.
"""

from sapientia.db.connection import get_engine
from sapientia.engines.knowledge_acquisition.connectors.text_connector import TextKnowledgeConnector
from sapientia.engines.knowledge_acquisition.extractors.simple_knowledge_extractor import SimpleKnowledgeExtractor
from sapientia.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeAcquisitionEngine:
    def acquire_local_document(self, project_id: int, file_path: str) -> dict:
        connector = TextKnowledgeConnector()
        extractor = SimpleKnowledgeExtractor()

        document = connector.load_document(file_path)
        document.knowledge_items = extractor.extract(document.chunks)

        engine = get_engine()

        with engine.begin() as connection:
            repository = KnowledgeRepository(connection)

            document_id = repository.upsert_document(
                project_id=project_id,
                document=document,
            )

            chunk_id_by_number = {}

            for chunk in document.chunks:
                document_chunk_id = repository.insert_document_chunk(
                    document_id=document_id,
                    chunk_number=chunk.chunk_number,
                    heading=chunk.heading,
                    content=chunk.content,
                    start_line_number=chunk.start_line_number,
                    end_line_number=chunk.end_line_number,
                )

                chunk_id_by_number[chunk.chunk_number] = document_chunk_id

            for item in document.knowledge_items:
                knowledge_item_id = repository.insert_knowledge_item(
                    project_id=project_id,
                    item=item,
                )

                repository.insert_knowledge_confidence(
                    knowledge_item_id=knowledge_item_id,
                    confidence=item.confidence,
                )

                for evidence in item.evidence:
                    chunk_number = evidence.evidence_json.get("chunk_number")
                    document_chunk_id = chunk_id_by_number.get(chunk_number)

                    repository.insert_knowledge_evidence(
                        knowledge_item_id=knowledge_item_id,
                        document_id=document_id,
                        document_chunk_id=document_chunk_id,
                        evidence=evidence,
                    )

        return {
            "document_id": document_id,
            "title": document.title,
            "document_type": document.document_type,
            "chunks_created": len(document.chunks),
            "knowledge_items_created": len(document.knowledge_items),
        }