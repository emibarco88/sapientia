"""
Exceptions raised by the Sapientia AI Runtime.
"""

from sapientia.runtime.ai.exceptions.ai_exceptions import (
    AIConfigurationError,
    AIException,
    AIRequestValidationError,
    AIResponseValidationError,
    AIRuntimeError,
    DriverAlreadyRegisteredError,
    DriverAuthenticationError,
    DriverException,
    DriverExecutionError,
    DriverNotFoundError,
    DriverRateLimitError,
    DriverTimeoutError,
)


__all__ = [
    "AIConfigurationError",
    "AIException",
    "AIRequestValidationError",
    "AIResponseValidationError",
    "AIRuntimeError",
    "DriverAlreadyRegisteredError",
    "DriverAuthenticationError",
    "DriverException",
    "DriverExecutionError",
    "DriverNotFoundError",
    "DriverRateLimitError",
    "DriverTimeoutError",
]