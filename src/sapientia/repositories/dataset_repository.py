"""
Module: dataset_repository.py

Purpose:
Provides CRUD operations for the omd_core.dataset table.
"""
from sqlalchemy import text


class DatasetRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_by_location(self, source_system_id: int, location: str):
        sql = text("""
            SELECT dataset_id
            FROM omd_core.dataset
            WHERE source_system_id = :source_system_id
              AND location = :location
        """)

        result = self.connection.execute(sql, {
            "source_system_id": source_system_id,
            "location": location
        }).fetchone()

        return result[0] if result else None

    def create(
        self,
        source_system_id: int,
        name: str,
        object_type: str,
        location: str,
        row_count: int,
        column_count: int,
        file_size_bytes: int = None,
    ) -> int:
        sql = text("""
            INSERT INTO omd_core.dataset
            (
                source_system_id,
                name,
                object_type,
                location,
                row_count,
                column_count,
                file_size_bytes
            )
            VALUES
            (
                :source_system_id,
                :name,
                :object_type,
                :location,
                :row_count,
                :column_count,
                :file_size_bytes
            )
            RETURNING dataset_id
        """)

        result = self.connection.execute(sql, {
            "source_system_id": source_system_id,
            "name": name,
            "object_type": object_type,
            "location": location,
            "row_count": row_count,
            "column_count": column_count,
            "file_size_bytes": file_size_bytes,
        })

        return result.scalar_one()

    def update(
        self,
        dataset_id: int,
        row_count: int,
        column_count: int,
        file_size_bytes: int = None,
    ) -> None:
        sql = text("""
            UPDATE omd_core.dataset
            SET
                row_count = :row_count,
                column_count = :column_count,
                file_size_bytes = :file_size_bytes,
                updated_at = NOW()
            WHERE dataset_id = :dataset_id
        """)

        self.connection.execute(sql, {
            "dataset_id": dataset_id,
            "row_count": row_count,
            "column_count": column_count,
            "file_size_bytes": file_size_bytes,
        })

    def create_or_update(
        self,
        source_system_id: int,
        name: str,
        object_type: str,
        location: str,
        row_count: int,
        column_count: int,
        file_size_bytes: int = None,
    ) -> int:
        existing_id = self.get_by_location(source_system_id, location)

        if existing_id:
            self.update(
                dataset_id=existing_id,
                row_count=row_count,
                column_count=column_count,
                file_size_bytes=file_size_bytes,
            )
            return existing_id

        return self.create(
            source_system_id=source_system_id,
            name=name,
            object_type=object_type,
            location=location,
            row_count=row_count,
            column_count=column_count,
            file_size_bytes=file_size_bytes,
        )