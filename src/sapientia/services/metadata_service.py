"""
Module: metadata_service.py

Purpose:
Coordinates metadata extraction and persistence into the
Operational Metadata Repository (OMD).
"""

from sapientia.db.connection import get_engine

from sapientia.connectors.csv.csv_connector import CSVConnector
from sapientia.connectors.json.json_connector import JSONConnector

from sapientia.repositories.relationship_repository import RelationshipRepository
from sapientia.repositories.source_system_repository import SourceSystemRepository
from sapientia.repositories.dataset_repository import DatasetRepository
from sapientia.repositories.column_repository import ColumnRepository
from sapientia.repositories.profile_repository import ProfileRepository

from sapientia.profiling.generic_profiler import GenericProfiler


class MetadataService:

    def _persist_profile(self, dataset_id: int, records: list[dict], connection) -> None:
        if not records:
            return

        profiler = GenericProfiler()
        profile = profiler.profile_records(records)

        profile_repo = ProfileRepository(connection)
        profile_repo.refresh_profile(dataset_id, profile)

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

            self._persist_profile(
                dataset_id=dataset_id,
                records=dataset_metadata.records,
                connection=connection,
            )

        return {
            "source_system_id": source_system_id,
            "dataset_id": dataset_id,
            "columns_refreshed": len(dataset_metadata.columns),
            "profiled": True,
        }

    def ingest_json(self, project_id: int, file_path: str) -> dict:
        connector = JSONConnector()
        dataset_metadata = connector.extract_metadata(file_path)

        engine = get_engine()

        with engine.begin() as connection:
            source_repo = SourceSystemRepository(connection)
            dataset_repo = DatasetRepository(connection)
            column_repo = ColumnRepository(connection)
            relationship_repo = RelationshipRepository(connection)

            source_system_id = source_repo.create_or_get(
                project_id=project_id,
                name=f"JSON Source - {dataset_metadata.name}",
                source_type="JSON",
                description="JSON file ingested by Sapientia metadata engine",
            )

            parent_dataset_id = dataset_repo.create_or_update(
                source_system_id=source_system_id,
                name=dataset_metadata.name,
                object_type=dataset_metadata.object_type,
                location=dataset_metadata.location,
                row_count=dataset_metadata.row_count,
                column_count=dataset_metadata.column_count,
                file_size_bytes=dataset_metadata.file_size_bytes,
            )

            column_repo.refresh_columns(
                dataset_id=parent_dataset_id,
                columns=dataset_metadata.columns,
            )

            self._persist_profile(
                dataset_id=parent_dataset_id,
                records=dataset_metadata.records,
                connection=connection,
            )

            relationship_repo.delete_by_parent_dataset(parent_dataset_id)

            child_dataset_ids = {}

            for child_dataset in dataset_metadata.child_datasets:
                child_dataset_id = dataset_repo.create_or_update(
                    source_system_id=source_system_id,
                    name=child_dataset.name,
                    object_type=child_dataset.object_type,
                    location=child_dataset.location,
                    row_count=child_dataset.row_count,
                    column_count=child_dataset.column_count,
                    file_size_bytes=child_dataset.file_size_bytes,
                )

                column_repo.refresh_columns(
                    dataset_id=child_dataset_id,
                    columns=child_dataset.columns,
                )

                self._persist_profile(
                    dataset_id=child_dataset_id,
                    records=child_dataset.records,
                    connection=connection,
                )

                child_dataset_ids[child_dataset.name] = child_dataset_id

            for relationship in dataset_metadata.relationships:
                child_dataset_id = child_dataset_ids.get(relationship.child_dataset_name)

                if child_dataset_id:
                    relationship_repo.create(
                        parent_dataset_id=parent_dataset_id,
                        child_dataset_id=child_dataset_id,
                        relationship=relationship,
                    )

        return {
            "source_system_id": source_system_id,
            "parent_dataset_id": parent_dataset_id,
            "child_datasets_created_or_updated": len(dataset_metadata.child_datasets),
            "relationships_created": len(dataset_metadata.relationships),
            "parent_columns_refreshed": len(dataset_metadata.columns),
            "profiled": True,
        }