"""
Module: column_repository.py

Purpose:
Provides CRUD operations for the ekr_core.column table.
"""
from sqlalchemy import text
from sapientia.models.metadata import ColumnMetadata


class ColumnRepository:
    def __init__(self, connection):
        self.connection = connection

    def delete_by_dataset(self, dataset_id: int) -> None:
        sql = text("""
            DELETE FROM ekr_core."column"
            WHERE dataset_id = :dataset_id
        """)

        self.connection.execute(sql, {"dataset_id": dataset_id})

    def create_many(self, dataset_id: int, columns: list[ColumnMetadata]) -> None:
        sql = text("""
            INSERT INTO ekr_core."column"
            (
                dataset_id,
                name,
                ordinal_position,
                data_type,
                nullable,
                length,
                precision_value,
                scale_value,
                description,
                is_primary_key,
                is_foreign_key
            )
            VALUES
            (
                :dataset_id,
                :name,
                :ordinal_position,
                :data_type,
                :nullable,
                :length,
                :precision_value,
                :scale_value,
                :description,
                false,
                false
            )
        """)

        rows = [
            {
                "dataset_id": dataset_id,
                "name": column.name,
                "ordinal_position": column.ordinal_position,
                "data_type": column.data_type,
                "nullable": column.nullable,
                "length": column.length,
                "precision_value": column.precision_value,
                "scale_value": column.scale_value,
                "description": column.description,
            }
            for column in columns
        ]

        self.connection.execute(sql, rows)

    def refresh_columns(self, dataset_id: int, columns: list[ColumnMetadata]) -> None:
        self.delete_by_dataset(dataset_id)
        self.create_many(dataset_id, columns)