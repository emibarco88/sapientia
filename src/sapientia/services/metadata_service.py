"""
Module: metadata_service.py

Purpose:
Coordinates metadata extraction and persistence into the
Operational Metadata Repository (OMD).
"""
from sapientia.db.connection import get_engine
from sapientia.connectors.csv.csv_connector import CSVConnector
from sapientia.repositories.source_system_repository import SourceSystemRepository
from sapientia.repositories.dataset_repository import DatasetRepository
from sapientia.repositories.column_repository import ColumnRepository


class MetadataService:
    def ingest_csv(self, project_id: int, file_path: str) -> dict:
        connector = CSVConnector()
        dataset_metadata = connector.extract_metadata(file_path)

        engine = get_engine()

        with engine.begin() as connection:
            source_repo = SourceSystemRepository(connection)
            dataset_repo = DatasetRepository(connection)
            column_repo = ColumnRepository(connection)

            source_system_id = source_repo.create_or_get(
                project_id=project_id,
                name=f"CSV Source - {dataset_metadata.name}",
                source_type="CSV",
                description="CSV file ingested by Sapientia metadata engine",
            )

            dataset_id = dataset_repo.create_or_update(
                source_system_id=source_system_id,
                name=dataset_metadata.name,
                object_type=dataset_metadata.object_type,
                location=dataset_metadata.location,
                row_count=dataset_metadata.row_count,
                column_count=dataset_metadata.column_count,
                file_size_bytes=dataset_metadata.file_size_bytes,
            )

            column_repo.refresh_columns(
                dataset_id=dataset_id,
                columns=dataset_metadata.columns,
            )

        return {
            "source_system_id": source_system_id,
            "dataset_id": dataset_id,
            "columns_refreshed": len(dataset_metadata.columns),
        }