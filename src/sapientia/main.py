"""
Module: main.py

Purpose:
Application entry point used to execute and test metadata
ingestion and semantic analysis workflows.
"""

import argparse
from sapientia.services.metadata_service import MetadataService
from sapientia.services.semantic_service import SemanticService


def main():
    parser = argparse.ArgumentParser(description="Sapientia CLI")

    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest metadata from a source")
    ingest_parser.add_argument("--project-id", type=int, required=True)
    ingest_parser.add_argument("--file-path", type=str, required=True)
    ingest_parser.add_argument("--source-type", type=str, required=True, choices=["csv", "json"])

    semantic_parser = subparsers.add_parser("semantic", help="Run semantic analysis")
    semantic_parser.add_argument("--dataset-id", type=int, required=True)

    args = parser.parse_args()

    if args.command == "ingest":
        metadata_service = MetadataService()

        if args.source_type == "csv":
            result = metadata_service.ingest_csv(
                project_id=args.project_id,
                file_path=args.file_path,
            )
        elif args.source_type == "json":
            result = metadata_service.ingest_json(
                project_id=args.project_id,
                file_path=args.file_path,
            )
        else:
            raise ValueError(f"Unsupported source type: {args.source_type}")

    elif args.command == "semantic":
        semantic_service = SemanticService()

        result = semantic_service.analyse_dataset(
            dataset_id=args.dataset_id,
        )

    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print("Execution completed.")
    print(result)


if __name__ == "__main__":
    main()