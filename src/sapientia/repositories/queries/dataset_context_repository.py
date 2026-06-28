"""
Module: dataset_context_repository.py

Purpose:
Reads dataset context required by engines that need source location,
source type and dataset metadata before execution.
"""

from sqlalchemy import text


class DatasetContextRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_dataset_context(self, dataset_id: int) -> dict | None:
        row = self.connection.execute(
            text("""
                SELECT
                    d.dataset_id,
                    d.name AS dataset_name,
                    d.location,
                    d.object_type,
                    ss.source_type
                FROM ekr_core.dataset d
                JOIN ekr_core.source_system ss
                    ON ss.source_system_id = d.source_system_id
                WHERE d.dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        ).fetchone()

        if not row:
            return None

        return dict(row._mapping)