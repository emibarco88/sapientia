"""
Module: main.py

Purpose:
Application entry point used to execute and test metadata
ingestion workflows.
"""

import argparse
from sapientia.services.metadata_service import MetadataService


def main():
    parser = argparse.ArgumentParser(description="Sapientia Metadata Ingestion")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--file-path", type=str, required=True)
    parser.add_argument("--source-type", type=str, required=True, choices=["csv", "json"])

    args = parser.parse_args()

    service = MetadataService()

    if args.source_type == "csv":
        result = service.ingest_csv(
            project_id=args.project_id,
            file_path=args.file_path,
        )
    elif args.source_type == "json":
        result = service.ingest_json(
            project_id=args.project_id,
            file_path=args.file_path,
        )
    else:
        raise ValueError(f"Unsupported source type: {args.source_type}")

    print("Metadata ingestion completed.")
    print(result)


if __name__ == "__main__":
    main()