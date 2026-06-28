"""
Module: semantic_service.py

Purpose:
Service layer facade for semantic analysis workflows.
"""

from sapientia.engines.semantic.semantic_engine import SemanticEngine


class SemanticService:
    def __init__(self):
        self.semantic_engine = SemanticEngine()

    def analyse_dataset(self, dataset_id: int) -> dict:
        return self.semantic_engine.analyse_dataset(dataset_id)