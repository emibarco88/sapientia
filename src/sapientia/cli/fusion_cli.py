"""
Module: fusion_cli.py

Purpose:
CLI handler for Knowledge Fusion Engine workflows.
"""

from sapientia.services.knowledge_fusion_service import KnowledgeFusionService


def run_fusion(args) -> dict:
    service = KnowledgeFusionService()

    return service.fuse_project(
        project_id=args.project_id,
    )