"""Persistence for immutable Enterprise Understanding snapshots."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sapientia.engines.enterprise_understanding.foundation_models import (
    UnderstandingSnapshotRecord,
)


class UnderstandingSnapshotRepository:
    def __init__(self, connection: Connection) -> None:
        if connection is None:
            raise ValueError("A database connection is required.")
        self.connection = connection

    def create_draft(
        self,
        source_run_id: int,
        summary: dict[str, Any] | None = None,
    ) -> UnderstandingSnapshotRecord:
        run = self.connection.execute(
            text("""
                SELECT
                    understanding_run_id,
                    project_id,
                    scope_type,
                    scope_reference,
                    scope_key,
                    model_version,
                    run_status
                FROM ekr_understanding.understanding_run
                WHERE understanding_run_id = :source_run_id
            """),
            {"source_run_id": source_run_id},
        ).mappings().one_or_none()

        if run is None:
            raise ValueError(f"Understanding run {source_run_id} was not found.")

        if run["run_status"] != "RUNNING":
            raise ValueError(
                "A draft snapshot can only be created from a RUNNING run."
            )

        lock_key = f"{run['project_id']}:{run['scope_key']}"
        self.connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": lock_key},
        )

        next_version = self.connection.execute(
            text("""
                SELECT COALESCE(MAX(snapshot_version), 0) + 1
                FROM ekr_understanding.understanding_snapshot
                WHERE project_id = :project_id
                  AND scope_key = :scope_key
            """),
            {
                "project_id": run["project_id"],
                "scope_key": run["scope_key"],
            },
        ).scalar_one()

        row = self.connection.execute(
            text("""
                INSERT INTO ekr_understanding.understanding_snapshot
                (
                    project_id,
                    source_run_id,
                    scope_type,
                    scope_reference,
                    scope_key,
                    snapshot_version,
                    snapshot_status,
                    model_version,
                    summary_json
                )
                VALUES
                (
                    :project_id,
                    :source_run_id,
                    :scope_type,
                    :scope_reference,
                    :scope_key,
                    :snapshot_version,
                    'DRAFT',
                    :model_version,
                    CAST(:summary_json AS JSONB)
                )
                RETURNING *
            """),
            {
                "project_id": run["project_id"],
                "source_run_id": source_run_id,
                "scope_type": run["scope_type"],
                "scope_reference": run["scope_reference"],
                "scope_key": run["scope_key"],
                "snapshot_version": int(next_version),
                "model_version": run["model_version"],
                "summary_json": json.dumps(summary or {}),
            },
        ).mappings().one()

        return self._to_record(row)

    def publish_snapshot(
        self,
        understanding_snapshot_id: int,
    ) -> UnderstandingSnapshotRecord:
        snapshot = self.get_snapshot(understanding_snapshot_id)

        if snapshot.snapshot_status != "DRAFT":
            raise ValueError("Only a DRAFT snapshot can be published.")

        self.connection.execute(
            text("""
                UPDATE ekr_understanding.understanding_snapshot
                SET snapshot_status = 'RETIRED',
                    retired_at = NOW()
                WHERE project_id = :project_id
                  AND scope_key = :scope_key
                  AND snapshot_status = 'PUBLISHED'
            """),
            {
                "project_id": snapshot.project_id,
                "scope_key": snapshot.scope_key,
            },
        )

        row = self.connection.execute(
            text("""
                UPDATE ekr_understanding.understanding_snapshot
                SET snapshot_status = 'PUBLISHED',
                    published_at = NOW()
                WHERE understanding_snapshot_id = :snapshot_id
                  AND snapshot_status = 'DRAFT'
                RETURNING *
            """),
            {"snapshot_id": understanding_snapshot_id},
        ).mappings().one_or_none()

        if row is None:
            raise RuntimeError("Snapshot publication failed.")
        return self._to_record(row)

    def get_snapshot(
        self,
        understanding_snapshot_id: int,
    ) -> UnderstandingSnapshotRecord:
        row = self.connection.execute(
            text("""
                SELECT *
                FROM ekr_understanding.understanding_snapshot
                WHERE understanding_snapshot_id = :snapshot_id
            """),
            {"snapshot_id": understanding_snapshot_id},
        ).mappings().one_or_none()

        if row is None:
            raise ValueError(
                f"Understanding snapshot {understanding_snapshot_id} was not found."
            )
        return self._to_record(row)

    def get_latest_published(
        self,
        project_id: int,
        scope_key: str,
    ) -> UnderstandingSnapshotRecord | None:
        row = self.connection.execute(
            text("""
                SELECT *
                FROM ekr_understanding.understanding_snapshot
                WHERE project_id = :project_id
                  AND scope_key = :scope_key
                  AND snapshot_status = 'PUBLISHED'
                ORDER BY snapshot_version DESC
                LIMIT 1
            """),
            {"project_id": project_id, "scope_key": scope_key},
        ).mappings().one_or_none()

        return self._to_record(row) if row else None

    @staticmethod
    def _to_record(row) -> UnderstandingSnapshotRecord:
        return UnderstandingSnapshotRecord(
            understanding_snapshot_id=int(
                row["understanding_snapshot_id"]
            ),
            project_id=int(row["project_id"]),
            source_run_id=int(row["source_run_id"]),
            scope_type=str(row["scope_type"]),
            scope_reference=row["scope_reference"],
            scope_key=str(row["scope_key"]),
            snapshot_version=int(row["snapshot_version"]),
            snapshot_status=str(row["snapshot_status"]),
            model_version=str(row["model_version"]),
            object_count=int(row["object_count"] or 0),
            relationship_count=int(row["relationship_count"] or 0),
            summary=dict(row["summary_json"] or {}),
            effective_at=row["effective_at"],
            published_at=row["published_at"],
        )
