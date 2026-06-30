"""
Module: asset_lineage_repository.py

Purpose:
Persists lineage evidence for discovered Enterprise Assets.
"""

import json
from sqlalchemy import text


class AssetLineageRepository:
    def __init__(self, connection):
        self.connection = connection

    def refresh_lineage(
        self,
        dataset_id: int,
        lineage_records: list[dict],
    ) -> None:
        self.connection.execute(
            text("""
                DELETE FROM ekr_core.asset_lineage
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id},
        )

        for record in lineage_records:
            self.connection.execute(
                text("""
                    INSERT INTO ekr_core.asset_lineage
                    (
                        dataset_id,
                        lineage_type,
                        source_type,
                        source_name,
                        source_query,
                        lineage_json
                    )
                    VALUES
                    (
                        :dataset_id,
                        :lineage_type,
                        :source_type,
                        :source_name,
                        :source_query,
                        CAST(:lineage_json AS JSONB)
                    )
                """),
                {
                    "dataset_id": dataset_id,
                    "lineage_type": record.get("lineage_type"),
                    "source_type": record.get("source_type"),
                    "source_name": record.get("source_name"),
                    "source_query": record.get("source_query"),
                    "lineage_json": json.dumps(
                        record.get("lineage_json", {}),
                        default=str,
                    ),
                },
            )