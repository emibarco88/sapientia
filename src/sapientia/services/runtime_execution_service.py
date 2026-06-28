"""
Module: runtime_execution_service.py

Purpose:
Provides a reusable execution tracking wrapper for Sapientia runtime components.
"""

from sapientia.db.connection import get_engine
from sapientia.repositories.runtime_repository import RuntimeRepository


class RuntimeExecutionService:

    def run_tracked(
        self,
        component_code: str,
        operation,
        project_id: int | None = None,
        dataset_id: int | None = None,
        document_id: int | None = None,
        parent_runtime_execution_id: int | None = None,
        execution_level: int = 1,
        input_json: dict | None = None,
        execution_source: str = "CLI",
    ) -> dict:
        engine = get_engine()

        with engine.begin() as connection:
            repository = RuntimeRepository(connection)

            runtime_execution_id = repository.start_execution(
                component_code=component_code,
                project_id=project_id,
                dataset_id=dataset_id,
                document_id=document_id,
                parent_runtime_execution_id=parent_runtime_execution_id,
                execution_level=execution_level,
                input_json=input_json,
                execution_source=execution_source,
            )

        try:
            result = operation()

            with engine.begin() as connection:
                repository = RuntimeRepository(connection)

                repository.finish_execution(
                    runtime_execution_id=runtime_execution_id,
                    status="SUCCESS",
                    output_json=result,
                )

            result["runtime_execution_id"] = runtime_execution_id
            return result

        except Exception as error:
            with engine.begin() as connection:
                repository = RuntimeRepository(connection)

                repository.finish_execution(
                    runtime_execution_id=runtime_execution_id,
                    status="FAILED",
                    output_json={},
                    error_message=str(error),
                )

            raise