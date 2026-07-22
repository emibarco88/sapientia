import pytest

from sapientia.ai.runtime import (
    AIResponse,
    AIUsage,
)


def test_ai_response_is_created() -> None:
    response = AIResponse(
        execution_id="execution-123",
        provider="openai",
        model="gpt-test",
        content='{"summary": "Finance assessment"}',
        parsed_content={
            "summary":
                "Finance assessment",
        },
        usage=AIUsage(
            input_tokens=100,
            output_tokens=20,
        ),
        latency_ms=500,
    )

    assert response.provider == "OPENAI"
    assert response.has_parsed_content is True
    assert response.usage.total_tokens == 120


def test_response_serialisation() -> None:
    response = AIResponse(
        execution_id="execution-123",
        provider="OPENAI",
        model="gpt-test",
        content="Finance assessment",
        usage=AIUsage(
            input_tokens=50,
            output_tokens=10,
        ),
    )

    result = response.to_dict()

    assert result["execution_id"] == "execution-123"
    assert result["provider"] == "OPENAI"
    assert result["usage"]["total_tokens"] == 60
    assert result["has_parsed_content"] is False


def test_empty_response_content_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="content",
    ):
        AIResponse(
            execution_id="execution-123",
            provider="OPENAI",
            model="gpt-test",
            content=" ",
        )


def test_negative_latency_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="latency_ms",
    ):
        AIResponse(
            execution_id="execution-123",
            provider="OPENAI",
            model="gpt-test",
            content="Response",
            latency_ms=-1,
        )