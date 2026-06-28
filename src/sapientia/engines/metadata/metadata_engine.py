"""
Module: metadata_engine.py

Purpose:
Coordinates metadata ingestion from connectors into EKR Core and
optionally triggers profiling through the Profiling Engine.
"""

from sapientia.db.connection import get_engine
from sapientia.config.profiling_config import ProfilingConfig

from sapientia.connectors.csv.csv_connector import CSVConnector
from sapientia.connectors.json.json_connector import JSONConnector

from sapientia.repositories.source_system_repository import SourceSystemRepository
from sapientia.repositories.dataset_repository import DatasetRepository
from sapientia.repositories.column_repository import ColumnRepository
from sapientia.repositories.relationship_repository import RelationshipRepository

from sapientia.engines.profiling.profiling_engine import ProfilingEngine


class MetadataEngine:
    def __init__(self):
        self.profiling_engine = ProfilingEngine()

    def ingest_csv(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
    ) -> dict:
        connector = CSVConnector()

        dataset_metadata = connector.extract_schema(file_path)
        profile_records = []

        if run_profiling:
            profile_records = connector.extract_records(
                source=file_path,
                limit=ProfilingConfig.SAMPLE_SIZE,
            )

        engine = get_engine()

        with engine.begin() as connection:
            source_repo = SourceSystemRepository(connection)
            dataset_repo = DatasetRepository(connection)
            column_repo = ColumnRepository(connection)

            source_system_id = source_repo.create_or_get(
                project_id=project_id,
                name=f"CSV Source - {dataset_metadata.name}",
                source_type="CSV",
                description="CSV file ingested by Sapientia Metadata Engine",
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

            if run_profiling:
                self.profiling_engine.profile_dataset(
                    dataset_id=dataset_id,
                    records=profile_records,
                    connection=connection,
                )

        return {
            "source_system_id": source_system_id,
            "dataset_id": dataset_id,
            "columns_refreshed": len(dataset_metadata.columns),
            "profiled_records": len(profile_records),
            "profile_record_limit": ProfilingConfig.SAMPLE_SIZE if run_profiling else 0,
            "profiled": run_profiling,
        }

    def ingest_json(
        self,
        project_id: int,
        file_path: str,
        run_profiling: bool = True,
    ) -> dict:
        connector = JSONConnector()

        dataset_metadata = connector.extract_schema(file_path)

        profile_records = []
        profile_child_records = {}

        if run_profiling:
            profile_dataset_metadata = connector.engine.extract(
                file_path=file_path,
                include_records=True,
            )

            profile_records = profile_dataset_metadata.records

            profile_child_records = {
                child.name: child.records
                for child in profile_dataset_metadata.child_datasets
            }

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
                description="JSON file ingested by Sapientia Metadata Engine",
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

            if run_profiling:
                self.profiling_engine.profile_dataset(
                    dataset_id=parent_dataset_id,
                    records=profile_records,
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

                if run_profiling:
                    child_records = profile_child_records.get(child_dataset.name, [])

                    self.profiling_engine.profile_dataset(
                        dataset_id=child_dataset_id,
                        records=child_records,
                        connection=connection,
                    )

                child_dataset_ids[child_dataset.name] = child_dataset_id

            for relationship in dataset_metadata.relationships:
                child_dataset_id = child_dataset_ids.get(
                    relationship.child_dataset_name
                )

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
            "profiled_records": len(profile_records),
            "profile_record_limit": ProfilingConfig.SAMPLE_SIZE if run_profiling else 0,
            "profiled": run_profiling,
        }