"""Persistence for Enterprise Understanding run lifecycle."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sapientia.engines.enterprise_understanding.foundation_models import (
    UnderstandingRunRecord,
    UnderstandingScope,
)


class UnderstandingRunRepository:
    def __init__(self, connection: Connection) -> None:
        if connection is None:
            raise ValueError("A database connection is required.")
        self.connection = connection

    def create_run(
        self,
        scope: UnderstandingScope,
        model_version: str = "1.0",
        configuration: dict[str, Any] | None = None,
    ) -> UnderstandingRunRecord:
        scope.validate()
        self._validate_project_exists(scope.project_id)
        self._validate_dataset_scope(scope)

        row = self.connection.execute(
            text("""
                INSERT INTO ekr_understanding.understanding_run
                (
                    project_id,
                    scope_type,
                    scope_reference,
                    scope_key,
                    run_status,
                    current_stage,
                    model_version,
                    requested_dataset_ids,
                    configuration_json
                )
                VALUES
                (
                    :project_id,
                    :scope_type,
                    :scope_reference,
                    :scope_key,
                    'RUNNING',
                    'INITIALISING',
                    :model_version,
                    CAST(:requested_dataset_ids AS JSONB),
                    CAST(:configuration_json AS JSONB)
                )
                RETURNING *
            """),
            {
                "project_id": scope.project_id,
                "scope_type": scope.scope_type,
                "scope_reference": scope.scope_reference,
                "scope_key": scope.scope_key,
                "model_version": model_version,
                "requested_dataset_ids": json.dumps(list(scope.dataset_ids)),
                "configuration_json": json.dumps(configuration or {}),
            },
        ).mappings().one()

        return self._to_record(row)

    def get_run(self, understanding_run_id: int) -> UnderstandingRunRecord:
        row = self.connection.execute(
            text("""
                SELECT *
                FROM ekr_understanding.understanding_run
                WHERE understanding_run_id = :understanding_run_id
            """),
            {"understanding_run_id": understanding_run_id},
        ).mappings().one_or_none()

        if row is None:
            raise ValueError(
                f"Understanding run {understanding_run_id} was not found."
            )
        return self._to_record(row)

    def update_stage(
        self,
        understanding_run_id: int,
        current_stage: str,
    ) -> UnderstandingRunRecord:
        row = self.connection.execute(
            text("""
                UPDATE ekr_understanding.understanding_run
                SET current_stage = :current_stage,
                    updated_at = NOW()
                WHERE understanding_run_id = :understanding_run_id
                  AND run_status = 'RUNNING'
                RETURNING *
            """),
            {
                "understanding_run_id": understanding_run_id,
                "current_stage": current_stage,
            },
        ).mappings().one_or_none()

        if row is None:
            raise ValueError(
                f"Understanding run {understanding_run_id} is not RUNNING."
            )
        return self._to_record(row)

    def complete_run(
        self,
        understanding_run_id: int,
        result: dict[str, Any] | None = None,
        objects_generated: int = 0,
        relationships_generated: int = 0,
        warnings_count: int = 0,
    ) -> UnderstandingRunRecord:
        row = self.connection.execute(
            text("""
                UPDATE ekr_understanding.understanding_run
                SET run_status = 'COMPLETED',
                    current_stage = 'COMPLETED',
                    result_json = CAST(:result_json AS JSONB),
                    objects_generated = :objects_generated,
                    relationships_generated = :relationships_generated,
                    warnings_count = :warnings_count,
                    completed_at = NOW(),
                    updated_at = NOW(),
                    error_message = NULL
                WHERE understanding_run_id = :understanding_run_id
                  AND run_status = 'RUNNING'
                RETURNING *
            """),
            {
                "understanding_run_id": understanding_run_id,
                "result_json": json.dumps(result or {}),
                "objects_generated": objects_generated,
                "relationships_generated": relationships_generated,
                "warnings_count": warnings_count,
            },
        ).mappings().one_or_none()

        if row is None:
            raise ValueError(
                f"Understanding run {understanding_run_id} is not RUNNING."
            )
        return self._to_record(row)

    def fail_run(
        self,
        understanding_run_id: int,
        error_message: str,
    ) -> UnderstandingRunRecord:
        row = self.connection.execute(
            text("""
                UPDATE ekr_understanding.understanding_run
                SET run_status = 'FAILED',
                    current_stage = 'FAILED',
                    completed_at = NOW(),
                    updated_at = NOW(),
                    error_message = :error_message
                WHERE understanding_run_id = :understanding_run_id
                  AND run_status IN ('PENDING', 'RUNNING')
                RETURNING *
            """),
            {
                "understanding_run_id": understanding_run_id,
                "error_message": error_message[:8000],
            },
        ).mappings().one_or_none()

        if row is None:
            return self.get_run(understanding_run_id)
        return self._to_record(row)

    def _validate_project_exists(self, project_id: int) -> None:
        exists = self.connection.execute(
            text("""
                SELECT 1
                FROM ekr_core.project
                WHERE project_id = :project_id
            """),
            {"project_id": project_id},
        ).scalar_one_or_none()

        if exists is None:
            raise ValueError(f"Project {project_id} was not found.")

    def _validate_dataset_scope(self, scope: UnderstandingScope) -> None:
        if not scope.dataset_ids:
            return

        rows = self.connection.execute(
            text("""
                SELECT d.dataset_id
                FROM ekr_core.dataset d
                JOIN ekr_core.source_system ss
                  ON ss.source_system_id = d.source_system_id
                WHERE ss.project_id = :project_id
                  AND d.dataset_id = ANY(:dataset_ids)
            """),
            {
                "project_id": scope.project_id,
                "dataset_ids": list(scope.dataset_ids),
            },
        ).scalars().all()

        found = {int(value) for value in rows}
        missing = sorted(set(scope.dataset_ids) - found)
        if missing:
            raise ValueError(
                "The following datasets do not belong to the project or "
                f"do not exist: {missing}"
            )

    @staticmethod
    def _to_record(row) -> UnderstandingRunRecord:
        return UnderstandingRunRecord(
            understanding_run_id=int(row["understanding_run_id"]),
            project_id=int(row["project_id"]),
            scope_type=str(row["scope_type"]),
            scope_reference=row["scope_reference"],
            scope_key=str(row["scope_key"]),
            run_status=str(row["run_status"]),
            current_stage=str(row["current_stage"]),
            model_version=str(row["model_version"]),
            requested_dataset_ids=list(row["requested_dataset_ids"] or []),
            configuration=dict(row["configuration_json"] or {}),
            result=dict(row["result_json"] or {}),
            objects_generated=int(row["objects_generated"] or 0),
            relationships_generated=int(
                row["relationships_generated"] or 0
            ),
            warnings_count=int(row["warnings_count"] or 0),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            error_message=row["error_message"],
        )
