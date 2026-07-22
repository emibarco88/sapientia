from unittest.mock import Mock

import pytest

from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIResponse,
    AIUsage,
    AIRuntimeContext,
)
from sapientia.runtime.ai.management import AIDriverManager
from sapientia.runtime.ai.runtime import AIRuntime


class FakeDriver:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def execute(self, request):
        if self.error is not None:
            raise self.error

        return self.response


def build_request() -> AIRequest:
    return AIRequest(
        prompt="Explain the revenue evidence.",
        runtime_context=AIRuntimeContext(
            project_id=1,
            business_domain="FINANCE",
            capability="AI_ADVISOR",
            operation="ANSWER_QUESTION",
            execution_id="execution-123",
            correlation_id="correlation-123",
        ),
        driver_name="OPENAI",
        model="test-model",
        metadata={
            "execution_source": "UNIT_TEST",
        },
    )


def build_response() -> AIResponse:
    return AIResponse(
        execution_id="execution-123",
        driver="OPENAI",
        model="test-model",
        content="Revenue evidence explanation.",
        usage=AIUsage(
            input_tokens=20,
            output_tokens=10,
            total_tokens=30,
        ),
        finish_reason="completed",
        latency_ms=100,
    )


def test_runtime_creates_driver_manager():
    runtime = AIRuntime(
        tracking_enabled=False,
    )

    assert isinstance(
        runtime.driver_manager,
        AIDriverManager,
    )


def test_runtime_registers_openai():
    runtime = AIRuntime(
        tracking_enabled=False,
    )

    assert (
        "OPENAI"
        in runtime.driver_manager.list_driver_names()
    )


def test_runtime_tracks_successful_execution():
    request = build_request()
    response = build_response()

    driver_manager = Mock()
    driver_manager.list_driver_names.return_value = [
        "OPENAI"
    ]
    driver_manager.create.return_value = FakeDriver(
        response=response
    )

    tracker = Mock()
    tracker.start.return_value = 1001

    runtime = AIRuntime(
        driver_manager=driver_manager,
        execution_tracker=tracker,
    )

    actual_response = runtime.execute(request)

    assert actual_response is response

    tracker.start.assert_called_once_with(request)

    tracker.complete.assert_called_once_with(
        runtime_execution_id=1001,
        request=request,
        response=response,
    )

    tracker.fail.assert_not_called()


def test_runtime_tracks_failed_execution_and_reraises():
    request = build_request()
    expected_error = RuntimeError(
        "AI execution failed."
    )

    driver_manager = Mock()
    driver_manager.list_driver_names.return_value = [
        "OPENAI"
    ]
    driver_manager.create.return_value = FakeDriver(
        error=expected_error
    )

    tracker = Mock()
    tracker.start.return_value = 1002

    runtime = AIRuntime(
        driver_manager=driver_manager,
        execution_tracker=tracker,
    )

    with pytest.raises(
        RuntimeError,
        match="AI execution failed",
    ):
        runtime.execute(request)

    tracker.start.assert_called_once_with(request)

    tracker.fail.assert_called_once_with(
        runtime_execution_id=1002,
        request=request,
        error=expected_error,
    )

    tracker.complete.assert_not_called()


def test_runtime_can_disable_tracking():
    request = build_request()
    response = build_response()

    driver_manager = Mock()
    driver_manager.list_driver_names.return_value = [
        "OPENAI"
    ]
    driver_manager.create.return_value = FakeDriver(
        response=response
    )

    tracker = Mock()

    runtime = AIRuntime(
        driver_manager=driver_manager,
        execution_tracker=tracker,
        tracking_enabled=False,
    )

    actual_response = runtime.execute(request)

    assert actual_response is response

    tracker.start.assert_not_called()
    tracker.complete.assert_not_called()
    tracker.fail.assert_not_called()