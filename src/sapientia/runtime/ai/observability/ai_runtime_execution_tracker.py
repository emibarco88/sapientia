"""
Module: ai_runtime_execution_tracker.py

Purpose:
Integrates the AI Runtime with Sapientia's existing runtime execution
framework.

The tracker records operational AI metadata without persisting complete
prompts or generated response content.
"""

from __future__ import annotations

from typing import Any

from sapientia.db.connection import get_engine
from sapientia.repositories.runtime.runtime_repository import (
    RuntimeRepository,
)
from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIResponse,
)


class AIRuntimeExecutionTracker:
    """
    Tracks AI executions using ekr_runtime.runtime_execution.

    Observability is intentionally best-effort. A database logging
    failure must not prevent an otherwise valid AI request from running,
    and it must not hide the original AI execution exception.
    """

    COMPONENT_CODE = "AI_RUNTIME"

    def __init__(self, engine_factory=get_engine) -> None:
        self._engine_factory = engine_factory

    def start(self, request: AIRequest) -> int | None:
        """
        Create a RUNNING runtime execution.

        Returns None when execution tracking cannot be started.
        """

        try:
            engine = self._engine_factory()

            with engine.begin() as connection:
                repository = RuntimeRepository(connection)

                runtime_execution_id = repository.start_execution(
                    component_code=self.COMPONENT_CODE,
                    project_id=request.runtime_context.project_id,
                    dataset_id=self._optional_integer_metadata(
                        request.metadata,
                        "dataset_id",
                    ),
                    document_id=self._optional_integer_metadata(
                        request.metadata,
                        "document_id",
                    ),
                    parent_runtime_execution_id=(
                        self._optional_integer_metadata(
                            request.metadata,
                            "parent_runtime_execution_id",
                        )
                    ),
                    execution_level=self._execution_level(request),
                    execution_source=self._execution_source(request),
                    input_json=self._build_input_json(request),
                )

                repository.log(
                    runtime_execution_id=runtime_execution_id,
                    log_level="INFO",
                    message="AI Runtime execution started.",
                    log_json={
                        "execution_id": request.execution_id,
                        "correlation_id": request.correlation_id,
                        "driver_name": request.driver_name,
                        "capability": (
                            request.runtime_context.capability
                        ),
                        "operation": (
                            request.runtime_context.operation
                        ),
                    },
                )

            return runtime_execution_id

        except Exception:
            # AI execution must remain available even when runtime
            # observability is temporarily unavailable.
            return None

    def complete(
        self,
        runtime_execution_id: int | None,
        request: AIRequest,
        response: AIResponse,
    ) -> None:
        """
        Mark an execution as successful.
        """

        if runtime_execution_id is None:
            return

        try:
            engine = self._engine_factory()

            with engine.begin() as connection:
                repository = RuntimeRepository(connection)

                repository.log(
                    runtime_execution_id=runtime_execution_id,
                    log_level="INFO",
                    message="AI Runtime execution completed successfully.",
                    log_json={
                        "execution_id": response.execution_id,
                        "driver": response.driver,
                        "model": response.model,
                        "latency_ms": response.latency_ms,
                        "finish_reason": response.finish_reason,
                    },
                )

                repository.finish_execution(
                    runtime_execution_id=runtime_execution_id,
                    status="SUCCESS",
                    output_json=self._build_output_json(
                        request=request,
                        response=response,
                    ),
                )

        except Exception:
            # Do not replace or alter a successful AI response because
            # persistence failed.
            return

    def fail(
        self,
        runtime_execution_id: int | None,
        request: AIRequest,
        error: Exception,
    ) -> None:
        """
        Mark an execution as failed.

        Any tracking error is swallowed so the original AI exception can
        be raised by AIRuntime.
        """

        if runtime_execution_id is None:
            return

        try:
            engine = self._engine_factory()

            with engine.begin() as connection:
                repository = RuntimeRepository(connection)

                error_payload = self._build_error_json(
                    request=request,
                    error=error,
                )

                repository.log(
                    runtime_execution_id=runtime_execution_id,
                    log_level="ERROR",
                    message="AI Runtime execution failed.",
                    log_json=error_payload,
                )

                repository.finish_execution(
                    runtime_execution_id=runtime_execution_id,
                    status="FAILED",
                    output_json=error_payload,
                    error_message=str(error),
                )

        except Exception:
            return

    def _build_input_json(
        self,
        request: AIRequest,
    ) -> dict[str, Any]:
        """
        Create non-sensitive execution metadata.

        Full prompt content is intentionally excluded.
        """

        context = request.runtime_context

        return {
            "execution_id": request.execution_id,
            "correlation_id": request.correlation_id,
            "project_id": context.project_id,
            "business_domain": context.business_domain,
            "capability": context.capability,
            "operation": context.operation,
            "driver_name": request.driver_name,
            "requested_model": request.model,
            "response_format": request.response_format,
            "temperature": request.temperature,
            "max_output_tokens": request.max_output_tokens,
            "timeout_seconds": request.timeout_seconds,
            "prompt_length": len(request.prompt),
            "metadata": self._safe_metadata(request.metadata),
        }

    def _build_output_json(
        self,
        request: AIRequest,
        response: AIResponse,
    ) -> dict[str, Any]:
        usage = response.usage

        return {
            "execution_id": response.execution_id,
            "correlation_id": request.correlation_id,
            "driver": response.driver,
            "model": response.model,
            "usage": {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "cached_input_tokens": usage.cached_input_tokens,
                "reasoning_tokens": usage.reasoning_tokens,
                "estimated_cost": self._serialisable_cost(
                    usage.estimated_cost
                ),
                "currency": usage.currency,
            },
            "finish_reason": response.finish_reason,
            "external_request_id": response.external_request_id,
            "latency_ms": response.latency_ms,
            "warning_count": len(response.warnings),
            "warnings": list(response.warnings),
            "structured_output_available": (
                response.parsed_content is not None
            ),
            "response_metadata": dict(response.metadata or {}),
        }

    def _build_error_json(
        self,
        request: AIRequest,
        error: Exception,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "execution_id": request.execution_id,
            "correlation_id": request.correlation_id,
            "driver_name": request.driver_name,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
        }

        to_dict = getattr(error, "to_dict", None)

        if callable(to_dict):
            try:
                payload["ai_error"] = to_dict()
            except Exception:
                pass

        return payload

    @staticmethod
    def _safe_metadata(
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Remove metadata entries likely to contain sensitive content.
        """

        excluded_keys = {
            "prompt",
            "prompt_text",
            "system_prompt",
            "document_text",
            "content",
            "response_content",
            "answer",
        }

        return {
            str(key): value
            for key, value in dict(metadata or {}).items()
            if str(key).lower() not in excluded_keys
        }

    @staticmethod
    def _optional_integer_metadata(
        metadata: dict[str, Any] | None,
        key: str,
    ) -> int | None:
        value = dict(metadata or {}).get(key)

        if value is None:
            return None

        try:
            converted = int(value)
        except (TypeError, ValueError):
            return None

        return converted if converted > 0 else None

    @staticmethod
    def _execution_level(request: AIRequest) -> int:
        value = dict(request.metadata or {}).get(
            "execution_level",
            1,
        )

        try:
            converted = int(value)
        except (TypeError, ValueError):
            return 1

        return converted if converted > 0 else 1

    @staticmethod
    def _execution_source(request: AIRequest) -> str:
        value = dict(request.metadata or {}).get(
            "execution_source",
            "AI_RUNTIME",
        )

        normalised = str(value or "AI_RUNTIME").strip().upper()

        return normalised[:100] or "AI_RUNTIME"

    @staticmethod
    def _serialisable_cost(value: Any) -> Any:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)