from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class ProcessStepCandidate:
    enterprise_object_id: int
    canonical_name: str
    step_number: int
    step_role: str = "ACTIVITY"
    confidence_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ProcessTransitionCandidate:
    source_enterprise_object_id: int
    target_enterprise_object_id: int
    operational_relationship_id: int | None
    confidence_score: float
    relationship_type_code: str
    reasoning: str | None = None

@dataclass(frozen=True)
class ProcessCandidate:
    process_key: str
    process_name: str
    generation_method: str
    confidence_score: float
    steps: tuple[ProcessStepCandidate, ...]
    transitions: tuple[ProcessTransitionCandidate, ...]
    business_domain: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class BehaviourBuildResult:
    understanding_run_id: int
    understanding_snapshot_id: int
    project_id: int
    processes_registered: int
    steps_registered: int
    transitions_registered: int
    warnings: tuple[str, ...] = ()
    def to_dict(self) -> dict[str, Any]:
        return {
            "understanding_run_id": self.understanding_run_id,
            "understanding_snapshot_id": self.understanding_snapshot_id,
            "project_id": self.project_id,
            "processes_registered": self.processes_registered,
            "steps_registered": self.steps_registered,
            "transitions_registered": self.transitions_registered,
            "warnings": list(self.warnings),
        }
