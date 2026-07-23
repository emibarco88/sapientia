from __future__ import annotations

import json
from decimal import Decimal

import pytest

from sapientia.orchestration.enterprise_understanding_orchestrator import (
    EnterpriseUnderstandingOrchestrator,
)


class FakeBaseUnderstanding:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def build_understanding(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "COMPLETED",
            "project_id": 1,
            "business_domain": "FINANCE",
            "message": "Base completed",
            "evidence_after": {
                "semantic_columns": 12,
                "average_confidence": Decimal("0.875"),
            },
        }


class FakeFoundation:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def initialise_and_publish(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "COMPLETED",
            "run": {"understanding_run_id": 101},
            "snapshot": {"understanding_snapshot_id": 201},
        }


class FakeRelationships:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def build_relationships(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "understanding_run_id": 102,
            "understanding_snapshot_id": 202,
            "relationships_registered": Decimal("7"),
        }


class FakeBehaviour:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def build_behaviour(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "understanding_run_id": 103,
            "understanding_snapshot_id": 203,
            "processes_registered": 2,
        }


class FakeContext:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def build_context(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "project_id": 1,
            "understanding_snapshot_id": 203,
            "contexts_registered": 5,
            "facts_registered": Decimal("11"),
        }


def build_subject():
    base = FakeBaseUnderstanding()
    u1 = FakeFoundation()
    u2 = FakeRelationships()
    u3 = FakeBehaviour()
    u4 = FakeContext()
    subject = EnterpriseUnderstandingOrchestrator(
        understanding_service=base,
        foundation_service=u1,
        relationship_service=u2,
        behaviour_service=u3,
        operational_context_service=u4,
    )
    return subject, base, u1, u2, u3, u4


def test_executes_base_then_u1_to_u4_and_returns_json_safe_result():
    subject, base, u1, u2, u3, u4 = build_subject()

    result = subject.build_understanding(
        project_id=1,
        business_domain="finance",
        dataset_ids=[8, 7, 8],
    )

    assert result["status"] == "COMPLETED"
    assert result["business_domain"] == "FINANCE"
    assert result["dataset_ids"] == [7, 8]
    assert result["orchestration"]["completed_increment"] == "U4"
    assert result["evidence_after"]["average_confidence"] == 0.875
    assert result["u1_u4"]["relationships_registered"] == 7
    assert result["u1_u4"]["facts_registered"] == 11

    # Regression check for the original API failure.
    json.dumps(result)

    assert base.calls[0]["dataset_ids"] == [7, 8]
    assert u1.calls[0]["scope_reference"] == "FINANCE"
    assert u2.calls[0]["dataset_ids"] == [7, 8]
    assert u3.calls[0]["scope_reference"] == "FINANCE"
    assert u4.calls[0]["understanding_snapshot_id"] == 203


def test_public_stage_summary_does_not_expose_raw_stage_payloads():
    subject, *_ = build_subject()
    result = subject.build_understanding(
        project_id=1,
        business_domain="FINANCE",
        dataset_ids=[7],
    )

    stages = result["orchestration"]["stages"]
    assert set(stages["u2_relationships"]) == {
        "status",
        "understanding_run_id",
        "understanding_snapshot_id",
        "relationships_registered",
    }


def test_stops_before_u1_when_base_understanding_fails():
    subject, base, u1, u2, u3, u4 = build_subject()
    base.build_understanding = lambda **_: {
        "status": "FAILED",
        "project_id": 1,
        "business_domain": "FINANCE",
    }

    with pytest.raises(RuntimeError, match="Base Enterprise Understanding"):
        subject.build_understanding(
            project_id=1,
            business_domain="FINANCE",
            dataset_ids=[7],
        )

    assert not u1.calls
    assert not u2.calls
    assert not u3.calls
    assert not u4.calls


@pytest.mark.parametrize(
    "project_id,business_domain,dataset_ids",
    [
        (0, "FINANCE", [1]),
        (1, "", [1]),
        (1, "FINANCE", []),
        (1, "FINANCE", [0]),
    ],
)
def test_rejects_invalid_scope(project_id, business_domain, dataset_ids):
    subject, *_ = build_subject()

    with pytest.raises(ValueError):
        subject.build_understanding(
            project_id=project_id,
            business_domain=business_domain,
            dataset_ids=dataset_ids,
        )
