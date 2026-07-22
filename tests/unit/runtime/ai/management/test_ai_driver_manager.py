import pytest

from sapientia.runtime.ai import (
    AIRequest,
    AIResponse,
    AbstractAIDriver,
    AIDriverManager,
)
from sapientia.runtime.ai.exceptions import (
    AIConfigurationError,
    DriverAlreadyRegisteredError,
    DriverNotFoundError,
)


class TestDriver(AbstractAIDriver):
    @property
    def driver_name(self) -> str:
        return "TEST"

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        return AIResponse(
            execution_id=request.execution_id,
            driver=self.normalised_driver_name,
            model=request.model or "test-model",
            content="Test response",
        )


class OtherDriver(AbstractAIDriver):
    @property
    def driver_name(self) -> str:
        return "OTHER"

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        return AIResponse(
            execution_id=request.execution_id,
            driver=self.normalised_driver_name,
            model=request.model or "other-model",
            content="Other response",
        )


class IncorrectNameDriver(AbstractAIDriver):
    @property
    def driver_name(self) -> str:
        return "ACTUAL"

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        raise NotImplementedError


def test_driver_can_be_registered() -> None:
    manager = AIDriverManager()

    registered_name = manager.register(
        TestDriver
    )

    assert registered_name == "TEST"
    assert manager.is_registered("test")
    assert manager.list_driver_names() == [
        "TEST",
    ]


def test_first_registered_driver_becomes_default() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    assert manager.default_driver_name == "TEST"


def test_driver_can_be_registered_as_default() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)
    manager.register(
        OtherDriver,
        make_default=True,
    )

    assert manager.default_driver_name == "OTHER"


def test_duplicate_registration_is_rejected() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    with pytest.raises(
        DriverAlreadyRegisteredError
    ):
        manager.register(TestDriver)


def test_registration_can_be_replaced() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    manager.register(
        TestDriver,
        replace=True,
    )

    assert manager.get_driver_class(
        "TEST"
    ) is TestDriver


def test_registered_driver_can_be_created() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    driver = manager.create(
        "test",
        configuration={
            "model": "test-model",
        },
    )

    assert isinstance(driver, TestDriver)
    assert driver.driver_name == "TEST"
    assert (
        driver.configuration["model"]
        == "test-model"
    )


def test_default_driver_can_be_created() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    driver = manager.create("DEFAULT")

    assert isinstance(driver, TestDriver)


def test_none_uses_default_driver() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    driver = manager.create()

    assert isinstance(driver, TestDriver)


def test_unknown_driver_is_rejected() -> None:
    manager = AIDriverManager()

    with pytest.raises(
        DriverNotFoundError
    ):
        manager.create("UNKNOWN")


def test_missing_default_driver_is_rejected() -> None:
    manager = AIDriverManager()

    with pytest.raises(
        AIConfigurationError,
        match="default",
    ):
        manager.create()


def test_driver_can_be_unregistered() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)

    removed_class = manager.unregister(
        "TEST"
    )

    assert removed_class is TestDriver
    assert not manager.is_registered("TEST")


def test_default_moves_after_unregister() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)
    manager.register(OtherDriver)

    manager.unregister("TEST")

    assert manager.default_driver_name == "OTHER"


def test_default_driver_can_be_changed() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)
    manager.register(OtherDriver)

    manager.set_default("OTHER")

    assert manager.default_driver_name == "OTHER"


def test_non_driver_class_is_rejected() -> None:
    manager = AIDriverManager()

    with pytest.raises(
        TypeError,
        match="AbstractAIDriver",
    ):
        manager.register(
            object  # type: ignore[arg-type]
        )


def test_registration_name_must_match_instance_name() -> None:
    manager = AIDriverManager()

    manager.register(
        IncorrectNameDriver,
        driver_name="REGISTERED",
    )

    with pytest.raises(
        AIConfigurationError,
        match="does not match",
    ):
        manager.create("REGISTERED")


def test_manager_description() -> None:
    manager = AIDriverManager()

    manager.register(TestDriver)
    manager.register(OtherDriver)

    result = manager.describe()

    assert result["registered_driver_count"] == 2
    assert result["default_driver_name"] == "TEST"

    assert result["drivers"] == {
        "OTHER": "OtherDriver",
        "TEST": "TestDriver",
    }