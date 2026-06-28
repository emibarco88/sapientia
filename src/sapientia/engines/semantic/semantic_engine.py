"""
Module: semantic_engine.py

Purpose:
Coordinates semantic analysis using EKR Core and EKR Profile as input,
then persists semantic understanding into EKR Semantic.
"""

from sapientia.db.connection import get_engine
from sapientia.repositories.semantic_repository import SemanticRepository
from sapientia.engines.semantic.semantic_analyzer import SemanticAnalyzer


class SemanticEngine:
    def analyse_dataset(self, dataset_id: int) -> dict:
        engine = get_engine()
        analyzer = SemanticAnalyzer()

        with engine.begin() as connection:
            repository = SemanticRepository(connection)

            columns = repository.get_columns_for_dataset(dataset_id)

            analysed_count = 0

            for column in columns:
                semantic = analyzer.analyse_column(column)
                repository.upsert_column_semantic(semantic)
                analysed_count += 1

        return {
            "dataset_id": dataset_id,
            "columns_analysed": analysed_count,
        }