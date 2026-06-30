"""
Module: dataset_repository.py

Purpose:
Persists discovered Enterprise Assets into ekr_core.dataset.
"""

from sqlalchemy import text


class DatasetRepository:

    def __init__(self, connection):
        self.connection = connection

    def create_or_update(
        self,
        source_system_id: int,
        business_domain_id: int,
        name: str,
        object_type: str,
        location: str,
        row_count: int | None,
        column_count: int |None,
        file_size_bytes: int | None,
    ) -> int:

        existing = self.connection.execute(
            text(
                """
                SELECT dataset_id
                FROM ekr_core.dataset
                WHERE source_system_id = :source_system_id
                  AND name = :name
                  AND location = :location
                """
            ),
            {
                "source_system_id": source_system_id,
                "name": name,
                "location": location,
            },
        ).fetchone()

        if existing:

            self.connection.execute(
                text(
                    """
                    UPDATE ekr_core.dataset
                    SET
                        business_domain_id = :business_domain_id,
                        object_type        = :object_type,
                        row_count          = :row_count,
                        column_count       = :column_count,
                        file_size_bytes    = :file_size_bytes,
                        updated_at         = NOW()
                    WHERE dataset_id = :dataset_id
                    """
                ),
                {
                    "dataset_id": existing.dataset_id,
                    "business_domain_id": business_domain_id,
                    "object_type": object_type,
                    "row_count": row_count,
                    "column_count": column_count,
                    "file_size_bytes": file_size_bytes,
                },
            )

            return existing.dataset_id

        result = self.connection.execute(
            text(
                """
                INSERT INTO ekr_core.dataset
                (
                    source_system_id,
                    business_domain_id,
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
                    :business_domain_id,
                    :name,
                    :object_type,
                    :location,
                    :row_count,
                    :column_count,
                    :file_size_bytes
                )
                RETURNING dataset_id
                """
            ),
            {
                "source_system_id": source_system_id,
                "business_domain_id": business_domain_id,
                "name": name,
                "object_type": object_type,
                "location": location,
                "row_count": row_count,
                "column_count": column_count,
                "file_size_bytes": file_size_bytes,
            },
        )

        return result.scalar_one()