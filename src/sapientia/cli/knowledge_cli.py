"""
Module: knowledge_cli.py

Purpose:
CLI handler for Knowledge Acquisition Engine workflows.
"""

from sapientia.services.knowledge_service import KnowledgeService


def run_knowledge(args) -> dict:
    service = KnowledgeService()

    return service.acquire_local_document(
        project_id=args.project_id,
        file_path=args.file_path,
    )