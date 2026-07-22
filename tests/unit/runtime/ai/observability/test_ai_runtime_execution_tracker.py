from sapientia.runtime.ai.contracts import (
    AIRequest,
    AIRuntimeContext,
)
from sapientia.runtime.ai.observability import (
    AIRuntimeExecutionTracker,
)


def build_request(metadata=None) -> AIRequest:
    return AIRequest(
        prompt="Sensitive business prompt.",
        runtime_context=AIRuntimeContext(
            project_id=1,
            business_domain="FINANCE",
            capability="AI_ADVISOR",
            operation="ANSWER_QUESTION",
            execution_id="execution-123",
            correlation_id="correlation-123",
        ),
        driver_name="OPENAI",
        model="test-model",
        metadata=metadata or {},
    )


def test_input_metadata_does_not_store_prompt_content():
    tracker = AIRuntimeExecutionTracker()
    request = build_request(
        metadata={
            "dataset_id": 10,
            "prompt_text": "Do not persist this.",
            "business_reference": "FIN-001",
        }
    )

    payload = tracker._build_input_json(request)

    assert payload["prompt_length"] > 0
    assert "prompt" not in payload
    assert "prompt_text" not in payload["metadata"]
    assert (
        payload["metadata"]["business_reference"]
        == "FIN-001"
    )


def test_optional_integer_metadata_returns_integer():
    value = AIRuntimeExecutionTracker._optional_integer_metadata(
        {"dataset_id": "25"},
        "dataset_id",
    )

    assert value == 25


def test_optional_integer_metadata_rejects_invalid_value():
    value = AIRuntimeExecutionTracker._optional_integer_metadata(
        {"dataset_id": "invalid"},
        "dataset_id",
    )

    assert value is None