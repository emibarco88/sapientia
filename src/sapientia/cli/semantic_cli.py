"""
Module: semantic_cli.py

Purpose:
CLI handler for semantic analysis workflows.
"""

from sapientia.services.semantic_service import SemanticService


def run_semantic(args) -> dict:
    semantic_service = SemanticService()

    return semantic_service.analyse_dataset(
        dataset_id=args.dataset_id,
    )