"""
Module: csv_connector.py

Purpose:
Reads CSV files and converts their structure into the common
Sapientia metadata model.
"""

import os
import pandas as pd

from sapientia.config.metadata_config import MetadataConfig
from sapientia.connectors.base_connector import BaseConnector
from sapientia.models.metadata import DatasetMetadata, ColumnMetadata


class CSVConnector(BaseConnector):

    def extract_schema(self, source: str) -> DatasetMetadata:
        sample_df = pd.read_csv(
            source,
            nrows=MetadataConfig.SCHEMA_SAMPLE_SIZE,
        )

        columns = []

        for index, column_name in enumerate(sample_df.columns, start=1):
            series = sample_df[column_name]

            columns.append(
                ColumnMetadata(
                    name=column_name,
                    ordinal_position=index,
                    data_type=self._map_dtype(series),
                    nullable=bool(series.isnull().any()),
                    length=self._max_length(series),
                )
            )

        row_count = self._count_rows(source)

        return DatasetMetadata(
            name=os.path.basename(source),
            object_type="CSV",
            location=source,
            row_count=row_count,
            column_count=len(sample_df.columns),
            file_size_bytes=os.path.getsize(source),
            columns=columns,
            records=[],
        )

    def extract_records(self, source: str, limit: int | None = None) -> list[dict]:
        if limit:
            df = pd.read_csv(source, nrows=limit)
        else:
            df = pd.read_csv(source)

        return df.where(pd.notnull(df), None).to_dict(orient="records")

    def extract_metadata(self, source: str) -> DatasetMetadata:
        """
        Backward-compatible alias.
        Prefer extract_schema() in new code.
        """
        return self.extract_schema(source)

    def _count_rows(self, file_path: str) -> int:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            return max(sum(1 for _ in file) - 1, 0)

    def _map_dtype(self, series) -> str:
        if pd.api.types.is_integer_dtype(series):
            return "INTEGER"

        if pd.api.types.is_float_dtype(series):
            return "NUMERIC"

        if pd.api.types.is_bool_dtype(series):
            return "BOOLEAN"

        if pd.api.types.is_datetime64_any_dtype(series):
            return "TIMESTAMP"

        return "VARCHAR"

    def _max_length(self, series) -> int | None:
        non_null_series = series.dropna()

        if len(non_null_series) == 0:
            return None

        return int(non_null_series.astype(str).str.len().max())