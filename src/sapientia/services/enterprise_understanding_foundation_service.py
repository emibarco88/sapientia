"""Application facade for U1 Enterprise Understanding foundation."""

from __future__ import annotations

from typing import Any

from sapientia.engines.enterprise_understanding.understanding_foundation_engine import (
    UnderstandingFoundationEngine,
)


class EnterpriseUnderstandingFoundationService:
    def __init__(
        self,
        engine: UnderstandingFoundationEngine | None = None,
    ) -> None:
        self.engine = engine or UnderstandingFoundationEngine()

    def initialise_and_publish(
        self,
        project_id: int,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
        dataset_ids: list[int] | None = None,
        configuration: dict[str, Any] | None = None,
        model_version: str = "1.0",
    ) -> dict[str, Any]:
        return self.engine.initialise_and_publish(
            project_id=project_id,
            scope_type=scope_type,
            scope_reference=scope_reference,
            dataset_ids=dataset_ids,
            configuration=configuration,
            model_version=model_version,
        ).to_dict()

    def get_run(self, understanding_run_id: int) -> dict[str, Any]:
        return self.engine.get_run(understanding_run_id).to_dict()

    def get_snapshot(
        self,
        understanding_snapshot_id: int,
    ) -> dict[str, Any]:
        return self.engine.get_snapshot(
            understanding_snapshot_id
        ).to_dict()

    def get_latest_published_snapshot(
        self,
        project_id: int,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
    ) -> dict[str, Any] | None:
        snapshot = self.engine.get_latest_published_snapshot(
            project_id=project_id,
            scope_type=scope_type,
            scope_reference=scope_reference,
        )
        return snapshot.to_dict() if snapshot else None
