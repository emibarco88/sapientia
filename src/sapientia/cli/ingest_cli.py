"""
Module: ingest_cli.py

Purpose:
CLI handler for ingestion workflows.
"""

from sapientia.services.metadata_service import MetadataService
from sapientia.services.semantic_service import SemanticService


def run_ingest(args) -> dict:
    metadata_service = MetadataService()

    if args.source_type == "csv":
        result = metadata_service.ingest_csv(
            project_id=args.project_id,
            file_path=args.file_path,
        )

        dataset_id = result["dataset_id"]

    elif args.source_type == "json":
        result = metadata_service.ingest_json(
            project_id=args.project_id,
            file_path=args.file_path,
        )

        dataset_id = result["parent_dataset_id"]

    else:
        raise ValueError(f"Unsupported source type: {args.source_type}")

    if args.run_semantic:
        semantic_service = SemanticService()

        result["semantic"] = semantic_service.analyse_dataset(
            dataset_id=dataset_id,
        )

    return result