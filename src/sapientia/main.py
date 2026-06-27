import argparse
from sapientia.services.metadata_service import MetadataService


def main():
    parser = argparse.ArgumentParser(description="Sapientia CSV Metadata Ingestion")
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--file-path", type=str, required=True)

    args = parser.parse_args()

    service = MetadataService()

    result = service.ingest_csv(
        project_id=args.project_id,
        file_path=args.file_path,
    )

    print("CSV metadata ingestion completed.")
    print(result)


if __name__ == "__main__":
    main()