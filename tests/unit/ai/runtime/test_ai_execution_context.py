from datetime import timezone

import pytest

from sapientia.ai.runtime import (
    AIExecutionContext,
)


def test_execution_context_is_normalised() -> None:
    context = AIExecutionContext(
        project_id=1,
        business_domain="finance",
        capability="enterprise assessment",
        operation="generate assessment",
        initiated_by="user@example.com",
    )

    assert context.project_id == 1
    assert context.business_domain == "FINANCE"
    assert context.capability == "ENTERPRISE ASSESSMENT"
    assert context.operation == "GENERATE ASSESSMENT"

    assert context.execution_id
    assert context.correlation_id

    assert context.created_at.tzinfo == timezone.utc


def test_execution_context_serialisation() -> None:
    context = AIExecutionContext(
        project_id=1,
        business_domain="FINANCE",
        capability="AI_ADVISOR",
        operation="ANSWER_QUESTION",
        metadata={
            "question_id": 20,
        },
    )

    result = context.to_dict()

    assert result["project_id"] == 1
    assert result["business_domain"] == "FINANCE"
    assert result["metadata"]["question_id"] == 20
    assert isinstance(result["created_at"], str)


def test_invalid_project_id_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="project_id",
    ):
        AIExecutionContext(
            project_id=0,
            business_domain="FINANCE",
            capability="AI_ADVISOR",
            operation="ANSWER_QUESTION",
        )


def test_empty_business_domain_is_rejected() -> None:
    with pytest.raises(ValueError):
        AIExecutionContext(
            project_id=1,
            business_domain=" ",
            capability="AI_ADVISOR",
            operation="ANSWER_QUESTION",
        )