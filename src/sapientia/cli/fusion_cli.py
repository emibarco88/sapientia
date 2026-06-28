"""
Module: fusion_cli.py

Purpose:
CLI handler for Knowledge Fusion Engine workflows.
"""

from sapientia.services.knowledge_fusion_service import KnowledgeFusionService
from sapientia.services.runtime_execution_service import RuntimeExecutionService


def run_fusion(args) -> dict:
    service = KnowledgeFusionService()
    tracker = RuntimeExecutionService()

    return tracker.run_tracked(
        component_code="KNOWLEDGE_FUSION",
        project_id=args.project_id,
        dataset_id=args.dataset_id,
        document_id=args.document_id,
        input_json={
            "project_id": args.project_id,
            "dataset_id": args.dataset_id,
            "document_id": args.document_id,
        },
        operation=lambda: service.fuse_project(
            project_id=args.project_id,
            document_id=args.document_id,
            dataset_id=args.dataset_id,
        ),
    )