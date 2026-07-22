import pytest

from sapientia.ai.runtime import (
    AIExecutionContext,
    AIRequest,
)


def build_context() -> AIExecutionContext:
    return AIExecutionContext(
        project_id=1,
        business_domain="FINANCE",
        capability="ENTERPRISE_ASSESSMENT",
        operation="GENERATE_ASSESSMENT",
    )


def test_ai_request_is_normalised() -> None:
    request = AIRequest(
        prompt="Assess the Finance domain.",
        execution_context=build_context(),
        provider="openai",
        model="gpt-test",
        response_format="json",
        temperature=0.2,
        max_output_tokens=2000,
        timeout_seconds=60,
    )

    assert request.provider == "OPENAI"
    assert request.response_format == "JSON"
    assert request.model == "gpt-test"


def test_request_can_exclude_prompt_from_dictionary() -> None:
    request = AIRequest(
        prompt="Sensitive enterprise context.",
        execution_context=build_context(),
    )

    result = request.to_dict(
        include_prompt=False
    )

    assert "prompt" not in result
    assert (
        result["execution_context"]
        ["business_domain"]
        == "FINANCE"
    )


def test_empty_prompt_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="prompt",
    ):
        AIRequest(
            prompt=" ",
            execution_context=build_context(),
        )


def test_invalid_response_format_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="response_format",
    ):
        AIRequest(
            prompt="Test",
            execution_context=build_context(),
            response_format="XML",
        )


def test_invalid_temperature_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="temperature",
    ):
        AIRequest(
            prompt="Test",
            execution_context=build_context(),
            temperature=3,
        )