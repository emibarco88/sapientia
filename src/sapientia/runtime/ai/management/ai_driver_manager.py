"""
Driver lifecycle management for the Sapientia AI Runtime.
"""

from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from sapientia.runtime.ai.drivers import (
    AbstractAIDriver,
)
from sapientia.runtime.ai.exceptions import (
    AIConfigurationError,
    DriverAlreadyRegisteredError,
    DriverNotFoundError,
)


class AIDriverManager:
    """
    Registers, creates and manages AI driver implementations.

    Driver classes are registered rather than pre-created instances.
    This allows each execution environment to construct a driver with
    its own configuration.

    The manager contains no OpenAI, Anthropic or Gemini-specific logic.
    """

    def __init__(
        self,
        *,
        default_driver_name: str | None = None,
    ) -> None:
        self._driver_classes: dict[
            str,
            type[AbstractAIDriver],
        ] = {}

        self._default_driver_name: str | None = None
        self._lock = RLock()

        if default_driver_name is not None:
            self._default_driver_name = (
                self._normalise_driver_name(
                    default_driver_name
                )
            )

    @property
    def default_driver_name(self) -> str | None:
        """
        Return the configured default driver name.
        """

        return self._default_driver_name

    def register(
        self,
        driver_class: type[AbstractAIDriver],
        *,
        driver_name: str | None = None,
        replace: bool = False,
        make_default: bool = False,
    ) -> str:
        """
        Register an AI driver class.

        Args:
            driver_class:
                Concrete subclass of AbstractAIDriver.

            driver_name:
                Optional explicit registration name. When omitted, the
                manager attempts to resolve the driver's name by
                constructing it without configuration.

            replace:
                Permit replacing an existing registration.

            make_default:
                Make the registered driver the default.

        Returns:
            The normalised registered driver name.
        """

        self._validate_driver_class(
            driver_class
        )

        resolved_name = self._resolve_registration_name(
            driver_class=driver_class,
            driver_name=driver_name,
        )

        with self._lock:
            if (
                resolved_name in self._driver_classes
                and not replace
            ):
                raise DriverAlreadyRegisteredError(
                    f"AI driver '{resolved_name}' is already "
                    "registered.",
                    driver_name=resolved_name,
                    details={
                        "registered_class":
                            self._driver_classes[
                                resolved_name
                            ].__name__,
                    },
                )

            self._driver_classes[
                resolved_name
            ] = driver_class

            if (
                make_default
                or self._default_driver_name is None
            ):
                self._default_driver_name = resolved_name

        return resolved_name

    def unregister(
        self,
        driver_name: str,
    ) -> type[AbstractAIDriver]:
        """
        Remove and return a registered driver class.
        """

        normalised_name = self._normalise_driver_name(
            driver_name
        )

        with self._lock:
            if normalised_name not in self._driver_classes:
                raise DriverNotFoundError(
                    f"AI driver '{normalised_name}' is not "
                    "registered.",
                    driver_name=normalised_name,
                )

            removed_class = self._driver_classes.pop(
                normalised_name
            )

            if (
                self._default_driver_name
                == normalised_name
            ):
                self._default_driver_name = (
                    next(
                        iter(self._driver_classes),
                        None,
                    )
                )

        return removed_class

    def create(
        self,
        driver_name: str | None = None,
        *,
        configuration: Mapping[str, Any] | None = None,
    ) -> AbstractAIDriver:
        """
        Create an instance of a registered AI driver.

        Passing None or DEFAULT uses the configured default driver.
        """

        resolved_name = self.resolve_driver_name(
            driver_name
        )

        with self._lock:
            driver_class = self._driver_classes.get(
                resolved_name
            )

        if driver_class is None:
            raise DriverNotFoundError(
                f"AI driver '{resolved_name}' is not "
                "registered.",
                driver_name=resolved_name,
                details={
                    "available_drivers":
                        self.list_driver_names(),
                },
            )

        try:
            instance = driver_class(
                configuration=dict(
                    configuration or {}
                )
            )
        except Exception as exc:
            raise AIConfigurationError(
                f"Could not create AI driver "
                f"'{resolved_name}'.",
                driver_name=resolved_name,
                details={
                    "driver_class":
                        driver_class.__name__,
                    "cause":
                        str(exc),
                },
            ) from exc

        actual_name = instance.normalised_driver_name

        if actual_name != resolved_name:
            raise AIConfigurationError(
                "Created AI driver name does not match "
                "its registration name.",
                driver_name=resolved_name,
                details={
                    "registration_name":
                        resolved_name,
                    "instance_driver_name":
                        actual_name,
                    "driver_class":
                        driver_class.__name__,
                },
            )

        return instance

    def get_driver_class(
        self,
        driver_name: str,
    ) -> type[AbstractAIDriver]:
        """
        Return a registered driver class without creating it.
        """

        normalised_name = self._normalise_driver_name(
            driver_name
        )

        with self._lock:
            driver_class = self._driver_classes.get(
                normalised_name
            )

        if driver_class is None:
            raise DriverNotFoundError(
                f"AI driver '{normalised_name}' is not "
                "registered.",
                driver_name=normalised_name,
            )

        return driver_class

    def set_default(
        self,
        driver_name: str,
    ) -> None:
        """
        Set the default AI driver.
        """

        normalised_name = self._normalise_driver_name(
            driver_name
        )

        with self._lock:
            if normalised_name not in self._driver_classes:
                raise DriverNotFoundError(
                    f"AI driver '{normalised_name}' is not "
                    "registered.",
                    driver_name=normalised_name,
                )

            self._default_driver_name = normalised_name

    def resolve_driver_name(
        self,
        driver_name: str | None,
    ) -> str:
        """
        Resolve an explicit or default driver name.
        """

        if (
            driver_name is None
            or str(driver_name).strip().upper()
            == "DEFAULT"
        ):
            if self._default_driver_name is None:
                raise AIConfigurationError(
                    "No default AI driver is configured."
                )

            return self._default_driver_name

        return self._normalise_driver_name(
            driver_name
        )

    def is_registered(
        self,
        driver_name: str,
    ) -> bool:
        """
        Return whether a driver name is registered.
        """

        normalised_name = self._normalise_driver_name(
            driver_name
        )

        with self._lock:
            return (
                normalised_name
                in self._driver_classes
            )

    def list_driver_names(self) -> list[str]:
        """
        Return registered driver names in sorted order.
        """

        with self._lock:
            return sorted(
                self._driver_classes.keys()
            )

    def describe(self) -> dict[str, Any]:
        """
        Return manager registration metadata.
        """

        with self._lock:
            drivers = {
                name: driver_class.__name__
                for name, driver_class
                in sorted(
                    self._driver_classes.items()
                )
            }

            default_driver_name = (
                self._default_driver_name
            )

        return {
            "default_driver_name":
                default_driver_name,
            "registered_driver_count":
                len(drivers),
            "drivers":
                drivers,
        }

    @staticmethod
    def _validate_driver_class(
        driver_class: type[AbstractAIDriver],
    ) -> None:
        if not isinstance(driver_class, type):
            raise TypeError(
                "driver_class must be a class."
            )

        if not issubclass(
            driver_class,
            AbstractAIDriver,
        ):
            raise TypeError(
                "driver_class must inherit from "
                "AbstractAIDriver."
            )

        if getattr(
            driver_class,
            "__abstractmethods__",
            None,
        ):
            raise TypeError(
                "driver_class must be a concrete "
                "AbstractAIDriver implementation."
            )

    def _resolve_registration_name(
        self,
        *,
        driver_class: type[AbstractAIDriver],
        driver_name: str | None,
    ) -> str:
        if driver_name is not None:
            return self._normalise_driver_name(
                driver_name
            )

        try:
            instance = driver_class()
        except Exception as exc:
            raise AIConfigurationError(
                "driver_name must be supplied when the "
                "driver cannot be created without "
                "configuration.",
                details={
                    "driver_class":
                        driver_class.__name__,
                    "cause":
                        str(exc),
                },
            ) from exc

        return instance.normalised_driver_name

    @staticmethod
    def _normalise_driver_name(
        driver_name: str,
    ) -> str:
        normalised_name = str(
            driver_name or ""
        ).strip().upper()

        if not normalised_name:
            raise ValueError(
                "driver_name cannot be empty."
            )

        return normalised_name