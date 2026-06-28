"""
Module: semantic_cli.py

Purpose:
CLI handler for semantic analysis workflows.
"""

from sapientia.services.semantic_service import SemanticService
from sapientia.services.runtime_execution_service import RuntimeExecutionService


def run_semantic(args) -> dict:
    service = SemanticService()
    tracker = RuntimeExecutionService()

    return tracker.run_tracked(
        component_code="SEMANTIC",
        dataset_id=args.dataset_id,
        input_json={"dataset_id": args.dataset_id},
        operation=lambda: service.analyse_dataset(
            dataset_id=args.dataset_id,
        ),
    )