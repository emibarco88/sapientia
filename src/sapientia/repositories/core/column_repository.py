"""
Module: column_repository.py

Purpose:
Persists column-level technical metadata for discovered Enterprise Assets
into ekr_core.column.
"""

import json
from sqlalchemy import text


class ColumnRepository:
    def __init__(self, connection):
        self.connection = connection

    def delete_by_dataset(self, dataset_id: int) -> None:
        self.connection.execute(
            text("""
                DELETE FROM ekr_core."column"
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        )

    def create_many(self, dataset_id: int, columns: list) -> None:
        if not columns:
            return

        sql = text("""
            INSERT INTO ekr_core."column"
            (
                dataset_id,
                name,
                data_type,
                ordinal_position,
                nullable_flag,
                max_length,
                precision_value,
                scale_value,
                raw_metadata
            )
            VALUES
            (
                :dataset_id,
                :name,
                :data_type,
                :ordinal_position,
                :nullable_flag,
                :max_length,
                :precision_value,
                :scale_value,
                CAST(:raw_metadata AS JSONB)
            )
        """)

        rows = []

        for column in columns:
            precision_value = getattr(column, "precision", None)
            if precision_value is None:
                precision_value = getattr(column, "precision_value", None)

            scale_value = getattr(column, "scale", None)
            if scale_value is None:
                scale_value = getattr(column, "scale_value", None)

            max_length = getattr(column, "length", None)
            if max_length is None:
                max_length = getattr(column, "max_length", None)

            nullable_flag = getattr(column, "nullable", None)
            if nullable_flag is None:
                nullable_flag = getattr(column, "nullable_flag", None)

            raw_metadata = getattr(column, "raw_metadata", None) or {}

            rows.append(
                {
                    "dataset_id": dataset_id,
                    "name": column.name,
                    "data_type": column.data_type,
                    "ordinal_position": column.ordinal_position,
                    "nullable_flag": nullable_flag,
                    "max_length": max_length,
                    "precision_value": precision_value,
                    "scale_value": scale_value,
                    "raw_metadata": json.dumps(raw_metadata, default=str),
                }
            )

        self.connection.execute(sql, rows)

    def refresh_columns(self, dataset_id: int, columns: list) -> None:
        self.delete_by_dataset(dataset_id)
        self.create_many(dataset_id, columns)