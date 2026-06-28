"""
Module: runtime_repository.py

Purpose:
Persists runtime execution history, logs and component registry lookups.
Also reads runtime configuration values from ekr_runtime.
"""

import json
from sqlalchemy import text


class RuntimeRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_component_id(self, component_code: str) -> int:
        row = self.connection.execute(
            text("""
                SELECT runtime_component_id
                FROM ekr_runtime.runtime_component
                WHERE component_code = :component_code
                  AND is_active = TRUE
            """),
            {"component_code": component_code},
        ).fetchone()

        if not row:
            raise ValueError(f"Runtime component not registered or inactive: {component_code}")

        return row.runtime_component_id

    def get_component_configuration(self, component_code: str) -> dict:
        rows = self.connection.execute(
            text("""
                SELECT
                    rc.parameter_name,
                    rc.parameter_value,
                    rc.parameter_type
                FROM ekr_runtime.runtime_configuration rc
                JOIN ekr_runtime.runtime_component comp
                    ON comp.runtime_component_id = rc.runtime_component_id
                WHERE comp.component_code = :component_code
                  AND comp.is_active = TRUE
                  AND rc.is_active = TRUE
            """),
            {"component_code": component_code},
        ).fetchall()

        return {
            row.parameter_name: self._cast_value(
                value=row.parameter_value,
                value_type=row.parameter_type,
            )
            for row in rows
        }

    def start_execution(
        self,
        component_code: str,
        project_id: int | None = None,
        dataset_id: int | None = None,
        document_id: int | None = None,
        parent_runtime_execution_id: int | None = None,
        execution_level: int = 1,
        input_json: dict | None = None,
        execution_source: str = "CLI",
    ) -> int:
        component_id = self.get_component_id(component_code)

        result = self.connection.execute(
            text("""
                INSERT INTO ekr_runtime.runtime_execution
                (
                    runtime_component_id,
                    parent_runtime_execution_id,
                    project_id,
                    dataset_id,
                    document_id,
                    execution_status,
                    execution_level,
                    execution_source,
                    input_json
                )
                VALUES
                (
                    :runtime_component_id,
                    :parent_runtime_execution_id,
                    :project_id,
                    :dataset_id,
                    :document_id,
                    'RUNNING',
                    :execution_level,
                    :execution_source,
                    CAST(:input_json AS JSONB)
                )
                RETURNING runtime_execution_id
            """),
            {
                "runtime_component_id": component_id,
                "parent_runtime_execution_id": parent_runtime_execution_id,
                "project_id": project_id,
                "dataset_id": dataset_id,
                "document_id": document_id,
                "execution_level": execution_level,
                "execution_source": execution_source,
                "input_json": json.dumps(input_json or {}, default=str, allow_nan=False),
            },
        )

        return result.scalar_one()

    def finish_execution(
        self,
        runtime_execution_id: int,
        status: str,
        output_json: dict | None = None,
        error_message: str | None = None,
    ) -> None:
        self.connection.execute(
            text("""
                UPDATE ekr_runtime.runtime_execution
                SET
                    execution_status = :status,
                    finished_at = NOW(),
                    duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000,
                    output_json = CAST(:output_json AS JSONB),
                    error_message = :error_message
                WHERE runtime_execution_id = :runtime_execution_id
            """),
            {
                "runtime_execution_id": runtime_execution_id,
                "status": status,
                "output_json": json.dumps(output_json or {}, default=str, allow_nan=False),
                "error_message": error_message,
            },
        )

    def log(
        self,
        runtime_execution_id: int,
        message: str,
        log_level: str = "INFO",
        log_json: dict | None = None,
    ) -> None:
        self.connection.execute(
            text("""
                INSERT INTO ekr_runtime.runtime_execution_log
                (
                    runtime_execution_id,
                    log_level,
                    message,
                    log_json
                )
                VALUES
                (
                    :runtime_execution_id,
                    :log_level,
                    :message,
                    CAST(:log_json AS JSONB)
                )
            """),
            {
                "runtime_execution_id": runtime_execution_id,
                "log_level": log_level,
                "message": message,
                "log_json": json.dumps(log_json or {}, default=str, allow_nan=False),
            },
        )

    def _cast_value(self, value: str, value_type: str):
        value_type = str(value_type or "STRING").upper()

        if value_type == "INTEGER":
            return int(value)

        if value_type in ["DECIMAL", "NUMERIC", "FLOAT"]:
            return float(value)

        if value_type == "BOOLEAN":
            return str(value).lower() in ["true", "1", "yes", "y"]

        if value_type == "JSON":
            return json.loads(value)

        return value