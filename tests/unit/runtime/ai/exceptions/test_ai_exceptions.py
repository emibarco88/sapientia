from sapientia.runtime.ai.exceptions import (
    AIException,
    DriverAuthenticationError,
    DriverRateLimitError,
    DriverTimeoutError,
)


def test_ai_exception_stores_context() -> None:
    error = AIException(
        "Execution failed.",
        execution_id="execution-123",
        driver_name="openai",
        details={
            "status_code": 500,
        },
    )

    assert str(error) == "Execution failed."
    assert error.execution_id == "execution-123"
    assert error.driver_name == "OPENAI"
    assert error.retryable is False
    assert error.details["status_code"] == 500


def test_ai_exception_serialisation() -> None:
    error = AIException(
        "Execution failed.",
        error_code="custom_error",
        driver_name="openai",
    )

    result = error.to_dict()

    assert result["error_type"] == "AIException"
    assert result["error_code"] == "CUSTOM_ERROR"
    assert result["driver_name"] == "OPENAI"
    assert result["message"] == "Execution failed."


def test_timeout_error_is_retryable() -> None:
    error = DriverTimeoutError(
        "The AI request timed out."
    )

    assert error.retryable is True
    assert error.error_code == "AI_DRIVER_TIMEOUT"


def test_rate_limit_error_is_retryable() -> None:
    error = DriverRateLimitError(
        "Rate limit reached."
    )

    assert error.retryable is True


def test_authentication_error_is_not_retryable() -> None:
    error = DriverAuthenticationError(
        "Invalid API key."
    )

    assert error.retryable is False