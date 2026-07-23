"""Enterprise Understanding orchestration for Sprint 4.5.1.

The customer-facing Build Understanding action executes the existing
semantic/knowledge/concept pipeline and then persists U1-U4 in dependency
order. The public result is deliberately restricted to JSON-safe primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, Sequence
from uuid import UUID

from sapientia.services.enterprise_behaviour_service import (
    EnterpriseBehaviourService,
)
from sapientia.services.enterprise_operational_context_service import (
    EnterpriseOperationalContextService,
)
from sapientia.services.enterprise_relationship_service import (
    EnterpriseRelationshipService,
)
from sapientia.services.enterprise_understanding_foundation_service import (
    EnterpriseUnderstandingFoundationService,
)
from sapientia.services.enterprise_understanding_service import (
    EnterpriseUnderstandingService,
)


class UnderstandingServiceProtocol(Protocol):
    def build_understanding(
        self,
        dataset_ids: Sequence[int],
        refresh_concepts: bool = True,
        run_semantic: bool = True,
        run_fusion: bool = True,
        run_concepts: bool = True,
        sample_limit: int = 10,
    ) -> dict[str, Any]: ...


class FoundationServiceProtocol(Protocol):
    def initialise_and_publish(
        self,
        project_id: int,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
        dataset_ids: list[int] | None = None,
        configuration: dict[str, Any] | None = None,
        model_version: str = "1.0",
    ) -> dict[str, Any]: ...


class RelationshipServiceProtocol(Protocol):
    def build_relationships(
        self,
        project_id: int,
        dataset_ids: list[int] | None = None,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
    ) -> dict[str, Any]: ...


class BehaviourServiceProtocol(Protocol):
    def build_behaviour(
        self,
        project_id: int,
        scope_type: str = "enterprise",
        scope_reference: str | None = None,
    ) -> dict[str, Any]: ...


class OperationalContextServiceProtocol(Protocol):
    def build_context(
        self,
        project_id: int,
        understanding_snapshot_id: int | None = None,
    ) -> dict[str, Any]: ...


def to_json_safe(value: Any) -> Any:
    """Recursively convert common database/domain values to JSON primitives."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (UUID, Path)):
        return str(value)
    if isinstance(value, Enum):
        return to_json_safe(value.value)
    if isinstance(value, dict):
        return {str(key): to_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_json_safe(value.to_dict())
    raise TypeError(
        "Enterprise Understanding returned a non-serialisable value: "
        f"{type(value).__name__}."
    )


@dataclass(slots=True)
class EnterpriseUnderstandingOrchestrator:
    """Coordinate the existing understanding pipeline and U1-U4 persistence."""

    understanding_service: UnderstandingServiceProtocol | None = None
    foundation_service: FoundationServiceProtocol | None = None
    relationship_service: RelationshipServiceProtocol | None = None
    behaviour_service: BehaviourServiceProtocol | None = None
    operational_context_service: OperationalContextServiceProtocol | None = None

    def __post_init__(self) -> None:
        self.understanding_service = (
            self.understanding_service or EnterpriseUnderstandingService()
        )
        self.foundation_service = (
            self.foundation_service or EnterpriseUnderstandingFoundationService()
        )
        self.relationship_service = (
            self.relationship_service or EnterpriseRelationshipService()
        )
        self.behaviour_service = (
            self.behaviour_service or EnterpriseBehaviourService()
        )
        self.operational_context_service = (
            self.operational_context_service
            or EnterpriseOperationalContextService()
        )

    def build_understanding(
        self,
        *,
        project_id: int,
        business_domain: str,
        dataset_ids: Sequence[int],
        refresh_concepts: bool = True,
        scope_type: str = "business_area",
        scope_reference: str | None = None,
    ) -> dict[str, Any]:
        """Execute Build Understanding through U4 and return a compact result."""

        normalized_dataset_ids = self._validate_inputs(
            project_id=project_id,
            business_domain=business_domain,
            dataset_ids=dataset_ids,
        )
        normalized_domain = business_domain.strip().upper()
        effective_scope_reference = scope_reference or normalized_domain

        base_result = self.understanding_service.build_understanding(
            dataset_ids=normalized_dataset_ids,
            refresh_concepts=refresh_concepts,
        )
        self._validate_base_result(
            base_result=base_result,
            project_id=project_id,
            business_domain=normalized_domain,
        )

        u1 = self.foundation_service.initialise_and_publish(
            project_id=project_id,
            scope_type=scope_type,
            scope_reference=effective_scope_reference,
            dataset_ids=normalized_dataset_ids,
            configuration={
                "increment": "U1",
                "business_domain": normalized_domain,
                "trigger": "BUILD_UNDERSTANDING",
            },
            model_version="1.0",
        )
        u1_run_id = self._nested_positive_int(
            u1, "run", "understanding_run_id", "U1"
        )
        u1_snapshot_id = self._nested_positive_int(
            u1, "snapshot", "understanding_snapshot_id", "U1"
        )

        u2 = self.relationship_service.build_relationships(
            project_id=project_id,
            dataset_ids=normalized_dataset_ids,
            scope_type=scope_type,
            scope_reference=effective_scope_reference,
        )
        u2_run_id = self._required_positive_int(
            u2, "understanding_run_id", "U2"
        )
        u2_snapshot_id = self._required_positive_int(
            u2, "understanding_snapshot_id", "U2"
        )

        u3 = self.behaviour_service.build_behaviour(
            project_id=project_id,
            scope_type=scope_type,
            scope_reference=effective_scope_reference,
        )
        u3_run_id = self._required_positive_int(
            u3, "understanding_run_id", "U3"
        )
        u3_snapshot_id = self._required_positive_int(
            u3, "understanding_snapshot_id", "U3"
        )

        u4 = self.operational_context_service.build_context(
            project_id=project_id,
            understanding_snapshot_id=u3_snapshot_id,
        )
        u4_snapshot_id = self._required_positive_int(
            u4, "understanding_snapshot_id", "U4"
        )

        # Keep existing fields consumed by the UI, but never expose raw stage
        # payloads. Stage payloads can contain Decimal or other DB-native types.
        result = dict(base_result)
        result.update(
            {
                "status": "COMPLETED",
                "project_id": project_id,
                "business_domain": normalized_domain,
                "dataset_ids": normalized_dataset_ids,
                "message": (
                    "Enterprise Understanding completed successfully for "
                    f"{len(normalized_dataset_ids)} dataset(s). Business concepts, "
                    "relationships, behaviour and operational context are ready."
                ),
                "orchestration": {
                    "pipeline": "BUILD_UNDERSTANDING_U1_U4",
                    "completed_increment": "U4",
                    "scope_type": scope_type,
                    "scope_reference": effective_scope_reference,
                    "stages": {
                        "base_understanding": {"status": "COMPLETED"},
                        "u1_foundation": {
                            "status": "COMPLETED",
                            "understanding_run_id": u1_run_id,
                            "understanding_snapshot_id": u1_snapshot_id,
                        },
                        "u2_relationships": {
                            "status": "COMPLETED",
                            "understanding_run_id": u2_run_id,
                            "understanding_snapshot_id": u2_snapshot_id,
                            "relationships_registered": int(
                                u2.get("relationships_registered") or 0
                            ),
                        },
                        "u3_behaviour": {
                            "status": "COMPLETED",
                            "understanding_run_id": u3_run_id,
                            "understanding_snapshot_id": u3_snapshot_id,
                            "processes_registered": int(
                                u3.get("processes_registered") or 0
                            ),
                        },
                        "u4_operational_context": {
                            "status": "COMPLETED",
                            "understanding_snapshot_id": u4_snapshot_id,
                            "contexts_registered": int(
                                u4.get("contexts_registered") or 0
                            ),
                            "facts_registered": int(
                                u4.get("facts_registered") or 0
                            ),
                        },
                    },
                },
                "u1_u4": {
                    "u1_understanding_run_id": u1_run_id,
                    "u1_snapshot_id": u1_snapshot_id,
                    "u2_understanding_run_id": u2_run_id,
                    "u2_snapshot_id": u2_snapshot_id,
                    "u3_understanding_run_id": u3_run_id,
                    "u3_snapshot_id": u3_snapshot_id,
                    "u4_snapshot_id": u4_snapshot_id,
                    "relationships_registered": int(
                        u2.get("relationships_registered") or 0
                    ),
                    "processes_registered": int(
                        u3.get("processes_registered") or 0
                    ),
                    "contexts_registered": int(
                        u4.get("contexts_registered") or 0
                    ),
                    "facts_registered": int(u4.get("facts_registered") or 0),
                },
            }
        )
        return to_json_safe(result)

    @staticmethod
    def _validate_inputs(
        *,
        project_id: int,
        business_domain: str,
        dataset_ids: Sequence[int],
    ) -> list[int]:
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError("project_id must be a positive integer.")
        if not str(business_domain or "").strip():
            raise ValueError("business_domain is required.")

        normalized = sorted({int(dataset_id) for dataset_id in dataset_ids})
        if not normalized or any(dataset_id <= 0 for dataset_id in normalized):
            raise ValueError("dataset_ids must contain positive integers.")
        return normalized

    @staticmethod
    def _validate_base_result(
        *,
        base_result: dict[str, Any],
        project_id: int,
        business_domain: str,
    ) -> None:
        if not isinstance(base_result, dict):
            raise RuntimeError("Base Enterprise Understanding returned no result.")
        status = str(base_result.get("status") or "").upper()
        if status != "COMPLETED":
            raise RuntimeError(
                "Base Enterprise Understanding returned status "
                f"{status or 'UNKNOWN'}."
            )
        if int(base_result.get("project_id") or 0) != project_id:
            raise RuntimeError("Base Enterprise Understanding project mismatch.")
        returned_domain = str(base_result.get("business_domain") or "").upper()
        if returned_domain != business_domain:
            raise RuntimeError("Base Enterprise Understanding domain mismatch.")

    @staticmethod
    def _required_positive_int(
        payload: dict[str, Any],
        key: str,
        stage: str,
    ) -> int:
        value = int(payload.get(key) or 0)
        if value <= 0:
            raise RuntimeError(f"{stage} did not return a valid {key}.")
        return value

    @classmethod
    def _nested_positive_int(
        cls,
        payload: dict[str, Any],
        parent: str,
        key: str,
        stage: str,
    ) -> int:
        nested = payload.get(parent)
        if not isinstance(nested, dict):
            raise RuntimeError(f"{stage} did not return {parent} details.")
        return cls._required_positive_int(nested, key, stage)