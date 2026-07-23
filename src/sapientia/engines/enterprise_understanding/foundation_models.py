"""
Strongly typed contracts for the Enterprise Understanding foundation.

U1 intentionally contains no relationship or process inference. It
provides the run and immutable snapshot lifecycle consumed by later
Understanding sub-engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class UnderstandingScope:
    project_id: int
    scope_type: str = "enterprise"
    scope_reference: str | None = None
    dataset_ids: tuple[int, ...] = ()

    @property
    def scope_key(self) -> str:
        if self.scope_reference:
            return f"{self.scope_type}:{self.scope_reference}"
        return self.scope_type

    def validate(self) -> None:
        valid_scope_types = {
            "enterprise",
            "capability",
            "process",
            "business_area",
            "dataset",
            "document",
        }

        if not isinstance(self.project_id, int) or self.project_id <= 0:
            raise ValueError("project_id must be a positive integer.")

        if self.scope_type not in valid_scope_types:
            raise ValueError(
                "scope_type must be one of: "
                + ", ".join(sorted(valid_scope_types))
            )

        if self.scope_type != "enterprise" and not self.scope_reference:
            raise ValueError(
                "scope_reference is required unless scope_type is enterprise."
            )

        if any(
            not isinstance(dataset_id, int) or dataset_id <= 0
            for dataset_id in self.dataset_ids
        ):
            raise ValueError("dataset_ids must contain positive integers only.")


@dataclass(slots=True)
class UnderstandingRunRecord:
    understanding_run_id: int
    project_id: int
    scope_type: str
    scope_reference: str | None
    scope_key: str
    run_status: str
    current_stage: str
    model_version: str
    requested_dataset_ids: list[int] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    objects_generated: int = 0
    relationships_generated: int = 0
    warnings_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "understanding_run_id": self.understanding_run_id,
            "project_id": self.project_id,
            "scope_type": self.scope_type,
            "scope_reference": self.scope_reference,
            "scope_key": self.scope_key,
            "run_status": self.run_status,
            "current_stage": self.current_stage,
            "model_version": self.model_version,
            "requested_dataset_ids": list(self.requested_dataset_ids),
            "configuration": dict(self.configuration),
            "result": dict(self.result),
            "objects_generated": self.objects_generated,
            "relationships_generated": self.relationships_generated,
            "warnings_count": self.warnings_count,
            "started_at": (
                self.started_at.isoformat() if self.started_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
        }


@dataclass(slots=True)
class UnderstandingSnapshotRecord:
    understanding_snapshot_id: int
    project_id: int
    source_run_id: int
    scope_type: str
    scope_reference: str | None
    scope_key: str
    snapshot_version: int
    snapshot_status: str
    model_version: str
    object_count: int = 0
    relationship_count: int = 0
    summary: dict[str, Any] = field(default_factory=dict)
    effective_at: datetime | None = None
    published_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "understanding_snapshot_id": self.understanding_snapshot_id,
            "project_id": self.project_id,
            "source_run_id": self.source_run_id,
            "scope_type": self.scope_type,
            "scope_reference": self.scope_reference,
            "scope_key": self.scope_key,
            "snapshot_version": self.snapshot_version,
            "snapshot_status": self.snapshot_status,
            "model_version": self.model_version,
            "object_count": self.object_count,
            "relationship_count": self.relationship_count,
            "summary": dict(self.summary),
            "effective_at": (
                self.effective_at.isoformat() if self.effective_at else None
            ),
            "published_at": (
                self.published_at.isoformat() if self.published_at else None
            ),
        }


@dataclass(slots=True)
class UnderstandingFoundationResult:
    run: UnderstandingRunRecord
    snapshot: UnderstandingSnapshotRecord

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "COMPLETED",
            "message": (
                "Enterprise Understanding foundation run completed and "
                "an immutable empty snapshot was published."
            ),
            "run": self.run.to_dict(),
            "snapshot": self.snapshot.to_dict(),
        }
