"""
Module: json_engine.py

Purpose:
Coordinates JSON loading, flattening, child dataset detection and metadata creation.
"""

import os
from sapientia.models.metadata import DatasetMetadata, ColumnMetadata, RelationshipMetadata
from sapientia.connectors.json.json_loader import JSONLoader
from sapientia.connectors.json.json_flattener import JSONFlattener
from sapientia.connectors.json.json_type_inferer import JSONTypeInferer


class JSONEngine:
    def __init__(self):
        self.loader = JSONLoader()
        self.flattener = JSONFlattener()
        self.type_inferer = JSONTypeInferer()

    def extract(self, file_path: str, include_records: bool = False) -> DatasetMetadata:
        data = self.loader.load(file_path)

        root_name = os.path.basename(file_path)
        root_records = self.flattener.normalise_root(data)

        parent_records, child_records_by_dataset = self.flattener.flatten_records(
            records=root_records,
            root_dataset_name=root_name,
        )

        parent_columns = self._build_columns(parent_records)

        child_datasets = []
        relationships = []

        for child_name, child_records in child_records_by_dataset.items():
            child_columns = self._build_columns(child_records)

            child_datasets.append(
                DatasetMetadata(
                    name=child_name,
                    object_type="JSON",
                    location=f"{file_path}#{child_name}",
                    row_count=len(child_records),
                    column_count=len(child_columns),
                    file_size_bytes=None,
                    columns=child_columns,
                    records=child_records if include_records else [],
                )
            )

            relationships.append(
                RelationshipMetadata(
                    parent_dataset_name=root_name,
                    child_dataset_name=child_name,
                    relationship_type="PARENT_CHILD",
                    description=f"Nested JSON array extracted from {root_name}",
                    confidence=1.0,
                )
            )

            return DatasetMetadata(
                name=root_name,
                object_type="JSON",
                location=file_path,
                row_count=len(parent_records),
                column_count=len(parent_columns),
                file_size_bytes=os.path.getsize(file_path),
                columns=parent_columns,
                child_datasets=child_datasets,
                relationships=relationships,
                records=parent_records if include_records else [],
            )

    def _build_columns(self, records: list[dict]) -> list[ColumnMetadata]:
        column_names = self._all_column_names(records)
        columns = []

        for index, column_name in enumerate(column_names, start=1):
            values = [record.get(column_name) for record in records]

            columns.append(
                ColumnMetadata(
                    name=column_name,
                    ordinal_position=index,
                    data_type=self.type_inferer.infer(values),
                    nullable=any(value is None for value in values),
                    length=self.type_inferer.max_length(values),
                )
            )

        return columns

    def _all_column_names(self, records: list[dict]) -> list[str]:
        column_names = []

        for record in records:
            for key in record.keys():
                if key not in column_names:
                    column_names.append(key)

        return column_names