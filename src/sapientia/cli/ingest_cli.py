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
    dataset_id = None

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

    elif args.source_type == "snowflake":
        result = discovery_service.discover_snowflake(
            project_id=args.project_id,
            database_name=args.snowflake_database,
            schema_name=args.snowflake_schema,
            table_name=args.snowflake_table,
            run_profiling=run_profiling,
            business_domain=args.business_domain,
            table_limit=args.table_limit,
        )

        dataset_id = result["assets"][0]["dataset_id"] if result["assets"] else None

    else:
        raise ValueError(f"Unsupported source type: {args.source_type}")

    if args.run_semantic and dataset_id:
        semantic_service = SemanticService()

        result["semantic"] = semantic_service.analyse_dataset(
            dataset_id=dataset_id,
        )

    return result