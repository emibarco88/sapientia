"""
Exception hierarchy for the Sapientia AI Runtime.

These exceptions provide provider-independent error categories that can
be handled consistently by the AI Runtime and higher-level capabilities.
"""

from __future__ import annotations

from typing import Any


class AIException(Exception):
    """
    Base exception for all Sapientia AI Runtime errors.

    Attributes:
        message:
            Human-readable error description.

        error_code:
            Stable machine-readable error identifier.

        execution_id:
            Optional AI execution identifier.

        driver_name:
            Optional driver associated with the failure.

        retryable:
            Indicates whether the operation may succeed if attempted
            again.

        details:
            Additional structured diagnostic information.
    """

    default_error_code = "AI_ERROR"
    default_retryable = False

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        execution_id: str | None = None,
        driver_name: str | None = None,
        retryable: bool | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        normalised_message = str(message or "").strip()

        if not normalised_message:
            normalised_message = self.__class__.__name__

        self.message = normalised_message
        self.error_code = (
            str(error_code or self.default_error_code)
            .strip()
            .upper()
        )

        self.execution_id = (
            str(execution_id).strip()
            if execution_id is not None
            else None
        )

        self.driver_name = (
            str(driver_name).strip().upper()
            if driver_name is not None
            else None
        )

        self.retryable = (
            self.default_retryable
            if retryable is None
            else bool(retryable)
        )

        self.details = dict(details or {})

        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serialisable error representation.
        """

        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "execution_id": self.execution_id,
            "driver_name": self.driver_name,
            "retryable": self.retryable,
            "details": dict(self.details),
        }


class DriverException(AIException):
    """
    Base exception for failures involving an AI driver.
    """

    default_error_code = "AI_DRIVER_ERROR"


class DriverNotFoundError(DriverException):
    """
    Raised when the requested AI driver is not registered.
    """

    default_error_code = "AI_DRIVER_NOT_FOUND"


class DriverAlreadyRegisteredError(DriverException):
    """
    Raised when a driver name has already been registered.
    """

    default_error_code = "AI_DRIVER_ALREADY_REGISTERED"


class DriverAuthenticationError(DriverException):
    """
    Raised when an external AI service rejects authentication.
    """

    default_error_code = "AI_DRIVER_AUTHENTICATION_ERROR"


class DriverTimeoutError(DriverException):
    """
    Raised when an AI driver execution exceeds its timeout.
    """

    default_error_code = "AI_DRIVER_TIMEOUT"
    default_retryable = True


class DriverRateLimitError(DriverException):
    """
    Raised when an external AI service applies a rate limit.
    """

    default_error_code = "AI_DRIVER_RATE_LIMIT"
    default_retryable = True


class DriverExecutionError(DriverException):
    """
    Raised when an AI driver cannot complete a request.
    """

    default_error_code = "AI_DRIVER_EXECUTION_ERROR"


class AIRequestValidationError(AIException):
    """
    Raised when an AI request fails runtime validation.
    """

    default_error_code = "AI_REQUEST_VALIDATION_ERROR"


class AIResponseValidationError(AIException):
    """
    Raised when an AI response fails validation.
    """

    default_error_code = "AI_RESPONSE_VALIDATION_ERROR"


class AIRuntimeError(AIException):
    """
    Raised when AI Runtime orchestration fails.
    """

    default_error_code = "AI_RUNTIME_ERROR"


class AIConfigurationError(AIException):
    """
    Raised when the AI Runtime or a driver is incorrectly configured.
    """

    default_error_code = "AI_CONFIGURATION_ERROR"