"""
Abstract contract implemented by all Sapientia AI drivers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIResponse,
)


class AbstractAIDriver(ABC):
    """
    Provider-independent interface for external AI services.

    Concrete drivers translate Sapientia AI contracts into an external
    service's request and response formats.

    Examples:
        OpenAIDriver
        AzureOpenAIDriver
        AnthropicDriver
        GeminiDriver
        LocalModelDriver
    """

    def __init__(
        self,
        *,
        configuration: dict[str, Any] | None = None,
    ) -> None:
        self._configuration = dict(configuration or {})

    @property
    @abstractmethod
    def driver_name(self) -> str:
        """
        Return the stable uppercase name of the driver.
        """

    @property
    def configuration(self) -> dict[str, Any]:
        """
        Return a copy of the driver's configuration.

        Returning a copy prevents external callers from accidentally
        mutating the driver's internal configuration.
        """

        return dict(self._configuration)

    @abstractmethod
    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        """
        Execute an AI request and return a normalised response.
        """

    def validate_request(
        self,
        request: AIRequest,
    ) -> None:
        """
        Perform common request validation before execution.

        Concrete drivers may extend this method and call super().
        """

        if not isinstance(request, AIRequest):
            raise TypeError(
                "request must be an AIRequest instance."
            )

        requested_driver = request.driver_name

        if (
            requested_driver != "DEFAULT"
            and requested_driver != self.normalised_driver_name
        ):
            raise ValueError(
                "AI request driver_name does not match "
                f"the {self.normalised_driver_name} driver."
            )

    def health_check(self) -> bool:
        """
        Return whether the driver appears operational.

        Concrete drivers may override this method with a real service
        health check. The default implementation only confirms that the
        driver has a valid name.
        """

        return bool(self.normalised_driver_name)

    @property
    def normalised_driver_name(self) -> str:
        """
        Return the validated uppercase driver name.
        """

        value = str(self.driver_name or "").strip().upper()

        if not value:
            raise ValueError(
                "driver_name cannot be empty."
            )

        return value

    def describe(self) -> dict[str, Any]:
        """
        Return metadata describing the driver.
        """

        return {
            "driver_name": self.normalised_driver_name,
            "driver_class": self.__class__.__name__,
            "configuration_keys": sorted(
                self._configuration.keys()
            ),
        }