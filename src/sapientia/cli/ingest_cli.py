"""
Module: ingest_cli.py

Purpose:
CLI handler for Enterprise Asset Discovery workflows.

The CLI command remains `ingest` for backwards compatibility, but the
underlying capability is Enterprise Asset Discovery.
"""

from sapientia.services.enterprise_asset_discovery_service import (
    EnterpriseAssetDiscoveryService,
)
from sapientia.services.semantic_service import SemanticService


def run_ingest(args) -> dict:
    discovery_service = EnterpriseAssetDiscoveryService()

    run_profiling = not args.skip_profiling

    if args.source_type == "csv":
        result = discovery_service.discover_csv(
            project_id=args.project_id,
            file_path=args.file_path,
            run_profiling=run_profiling,
            business_domain=args.business_domain,
        )

        dataset_id = result["dataset_id"]

    elif args.source_type == "json":
        result = discovery_service.discover_json(
            project_id=args.project_id,
            file_path=args.file_path,
            run_profiling=run_profiling,
            business_domain=args.business_domain,
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