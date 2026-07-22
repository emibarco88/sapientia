"""
Module: ai_runtime.py

Purpose:
Coordinates provider-independent AI execution through registered
AI drivers and records execution metadata through Sapientia's existing
runtime framework.
"""

from __future__ import annotations

from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIResponse,
)
from sapientia.runtime.ai.drivers import OpenAIDriver
from sapientia.runtime.ai.management import AIDriverManager
from sapientia.runtime.ai.observability import (
    AIRuntimeExecutionTracker,
)


class AIRuntime:
    """
    Provider-independent AI execution runtime.
    """

    def __init__(
        self,
        driver_manager: AIDriverManager | None = None,
        execution_tracker: AIRuntimeExecutionTracker | None = None,
        tracking_enabled: bool = True,
    ) -> None:
        self.driver_manager = (
            driver_manager
            if driver_manager is not None
            else AIDriverManager()
        )

        self.tracking_enabled = bool(tracking_enabled)

        self.execution_tracker = (
            execution_tracker
            if execution_tracker is not None
            else AIRuntimeExecutionTracker()
        )

        self._register_default_drivers()

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Execute an AI request using its selected driver.

        Runtime execution tracking is best-effort and does not change
        the AI response or exception behaviour.
        """

        runtime_execution_id: int | None = None

        if self.tracking_enabled:
            runtime_execution_id = self.execution_tracker.start(
                request
            )

        try:
            driver = self.driver_manager.create(
                request.driver_name
            )

            response = driver.execute(request)

            if self.tracking_enabled:
                self.execution_tracker.complete(
                    runtime_execution_id=runtime_execution_id,
                    request=request,
                    response=response,
                )

            return response

        except Exception as error:
            if self.tracking_enabled:
                self.execution_tracker.fail(
                    runtime_execution_id=runtime_execution_id,
                    request=request,
                    error=error,
                )

            raise

    def _register_default_drivers(self) -> None:
        """
        Register the built-in OpenAI driver when it is not already
        registered.
        """

        registered_names = set(
            self.driver_manager.list_driver_names()
        )

        if "OPENAI" not in registered_names:
            self.driver_manager.register(
                OpenAIDriver,
                driver_name="OPENAI",
                make_default=True,
            )