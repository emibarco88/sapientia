"""
Module: knowledge_cli.py

Purpose:
CLI handler for Knowledge Acquisition Engine workflows.
"""

from sapientia.services.knowledge_service import KnowledgeService
from sapientia.services.runtime_execution_service import RuntimeExecutionService


def run_knowledge(args) -> dict:
    service = KnowledgeService()
    tracker = RuntimeExecutionService()

    return tracker.run_tracked(
        component_code="KNOWLEDGE_ACQUISITION",
        project_id=args.project_id,
        input_json={
            "project_id": args.project_id,
            "file_path": args.file_path,
            "business_domain": args.business_domain,
        },
        operation=lambda: service.acquire_local_document(
            project_id=args.project_id,
            file_path=args.file_path,
            business_domain=args.business_domain,
        ),
    )