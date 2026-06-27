"""
Module: csv_connector.py

Purpose:
Reads CSV files and converts their structure into the common
Sapientia metadata model.
"""
import os
import pandas as pd

from sapientia.models.metadata import DatasetMetadata, ColumnMetadata
from sapientia.connectors.base_connector import BaseConnector

class CSVConnector(BaseConnector):
    def extract_metadata(self, file_path: str) -> DatasetMetadata:
        df = pd.read_csv(file_path)
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        columns = []

        for index, column_name in enumerate(df.columns, start=1):
            series = df[column_name]

            columns.append(
                ColumnMetadata(
                    name=column_name,
                    ordinal_position=index,
                    data_type=self._map_dtype(series),
                    nullable=bool(series.isnull().any()),
                    length=self._max_length(series),
                )
            )

        return DatasetMetadata(
            name=os.path.basename(file_path),
            object_type="CSV",
            location=file_path,
            row_count=len(df),
            column_count=len(df.columns),
            file_size_bytes=os.path.getsize(file_path),
            columns=columns,
            records=records,
        )

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
        if pd.api.types.is_object_dtype(series):
            return int(series.astype(str).str.len().max())
        return None