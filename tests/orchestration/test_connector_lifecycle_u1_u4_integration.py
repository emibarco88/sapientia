from __future__ import annotations

from sapientia.services.connector_lifecycle_service import (
    ConnectorLifecycleService,
)


class FakeLegacyUnderstandingService:
    pass


class FakeOrchestrator:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def build_understanding(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "COMPLETED",
            "project_id": 1,
            "business_domain": "FINANCE",
            "message": "Enterprise Understanding completed through U4.",
            "datasets_processed": 1,
            "evidence_after": {"semantic_columns": 4},
            "u1_u4": {"u4_snapshot_id": 203},
        }


class ConnectorLifecycleHarness(ConnectorLifecycleService):
    def __init__(self, orchestrator):
        super().__init__(
            enterprise_understanding_service=FakeLegacyUnderstandingService(),
            enterprise_understanding_orchestrator=orchestrator,
        )
        self.status_updates: list[tuple[str, str]] = []

    def _get_connector_context(self, connector_id):
        assert connector_id == 5
        return {
            "project_id": 1,
            "domain_code": "FINANCE",
            "dataset_ids": [9],
        }

    def _set_understanding_status(self, connector_id, status, message):
        assert connector_id == 5
        self.status_updates.append((status, message))


def test_build_understanding_delegates_to_orchestrator():
    orchestrator = FakeOrchestrator()
    service = ConnectorLifecycleHarness(orchestrator)

    result = service.build_understanding(connector_id=5)

    assert orchestrator.calls == [
        {
            "project_id": 1,
            "business_domain": "FINANCE",
            "dataset_ids": [9],
            "refresh_concepts": True,
            "scope_type": "business_area",
            "scope_reference": "FINANCE",
        }
    ]
    assert result["status"] == "COMPLETED"
    assert result["u1_u4"]["u4_snapshot_id"] == 203
    assert service.status_updates[0][0] == "RUNNING"
    assert service.status_updates[-1][0] == "COMPLETED"
