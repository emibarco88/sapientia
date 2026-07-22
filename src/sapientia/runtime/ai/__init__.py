"""
Sapientia AI Runtime.

This package contains provider-independent AI contracts, drivers,
management and execution infrastructure.
"""

from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIResponse,
    AIRuntimeContext,
    AIUsage,
)
from sapientia.runtime.ai.drivers import (
    AbstractAIDriver,
)
from sapientia.runtime.ai.exceptions import (
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
from sapientia.runtime.ai.management import (
    AIDriverManager,
)


__all__ = [
    "AIConfigurationError",
    "AIException",
    "AIRequest",
    "AIRequestValidationError",
    "AIResponse",
    "AIResponseValidationError",
    "AIRuntimeContext",
    "AIRuntimeError",
    "AIUsage",
    "AIDriverManager",
    "AbstractAIDriver",
    "DriverAlreadyRegisteredError",
    "DriverAuthenticationError",
    "DriverException",
    "DriverExecutionError",
    "DriverNotFoundError",
    "DriverRateLimitError",
    "DriverTimeoutError",
]