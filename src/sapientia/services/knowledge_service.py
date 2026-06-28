"""
Module: knowledge_service.py

Purpose:
Service layer facade for knowledge acquisition workflows.
"""

from sapientia.engines.knowledge_acquisition.knowledge_engine import KnowledgeAcquisitionEngine


class KnowledgeService:
    def __init__(self):
        self.knowledge_engine = KnowledgeAcquisitionEngine()

    def acquire_local_document(self, project_id: int, file_path: str) -> dict:
        return self.knowledge_engine.acquire_local_document(
            project_id=project_id,
            file_path=file_path,
        )