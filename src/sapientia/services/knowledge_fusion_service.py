"""
Module: knowledge_fusion_service.py

Purpose:
Service layer facade for Knowledge Fusion workflows.
"""

from sapientia.engines.knowledge_fusion.knowledge_fusion_engine import KnowledgeFusionEngine


class KnowledgeFusionService:
    def __init__(self):
        self.engine = KnowledgeFusionEngine()

    def fuse_project(self, project_id: int) -> dict:
        return self.engine.fuse_project(project_id)