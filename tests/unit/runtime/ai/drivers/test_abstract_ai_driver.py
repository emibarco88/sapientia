import pytest

from sapientia.runtime.ai import (
    AIRequest,
    AIResponse,
    AIRuntimeContext,
    AbstractAIDriver,
)


class TestDriver(AbstractAIDriver):
    @property
    def driver_name(self) -> str:
        return "TEST"

    def execute(
        self,
        request: AIRequest,
    ) -> AIResponse:
        self.validate_request(request)

        return AIResponse(
            execution_id=request.execution_id,
            driver=self.normalised_driver_name,
            model=request.model or "test-model",
            content="Test response",
        )


def build_request(
    driver_name: str = "TEST",
) -> AIRequest:
    context = AIRuntimeContext(
        project_id=1,
        business_domain="FINANCE",
        capability="ENTERPRISE_ASSESSMENT",
        operation="GENERATE_ASSESSMENT",
    )

    return AIRequest(
        prompt="Assess Finance.",
        runtime_context=context,
        driver_name=driver_name,
    )


def test_abstract_driver_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        AbstractAIDriver()  # type: ignore[abstract]


def test_concrete_driver_can_execute_request() -> None:
    driver = TestDriver()

    response = driver.execute(
        build_request()
    )

    assert response.driver == "TEST"
    assert response.content == "Test response"


def test_default_request_driver_is_accepted() -> None:
    driver = TestDriver()

    driver.validate_request(
        build_request("DEFAULT")
    )


def test_mismatched_driver_is_rejected() -> None:
    driver = TestDriver()

    with pytest.raises(
        ValueError,
        match="does not match",
    ):
        driver.validate_request(
            build_request("OTHER")
        )


def test_driver_configuration_is_copied() -> None:
    configuration = {
        "api_key": "secret",
    }

    driver = TestDriver(
        configuration=configuration
    )

    returned_configuration = (
        driver.configuration
    )

    returned_configuration["api_key"] = "changed"

    assert (
        driver.configuration["api_key"]
        == "secret"
    )


def test_driver_description() -> None:
    driver = TestDriver(
        configuration={
            "model": "test-model",
            "timeout": 30,
        }
    )

    result = driver.describe()

    assert result["driver_name"] == "TEST"
    assert result["driver_class"] == "TestDriver"
    assert result["configuration_keys"] == [
        "model",
        "timeout",
    ]


def test_default_health_check() -> None:
    driver = TestDriver()

    assert driver.health_check() is True