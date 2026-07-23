from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class DependencyEdge:
    source_id: int
    target_id: int
    relationship_id: int | None
    dependency_type: str
    confidence: float
    evidence_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class DependencyPath:
    object_ids: tuple[int, ...]
    edge_ids: tuple[int, ...]
    confidence: float

    @property
    def depth(self) -> int:
        return max(0, len(self.object_ids) - 1)

@dataclass(frozen=True)
class ImpactResult:
    reasoning_run_id: int
    origin_object_id: int
    direction: str
    paths: tuple[DependencyPath, ...]
    impacted_object_ids: tuple[int, ...]
    critical_object_ids: tuple[int, ...]
    confidence: float
    root_causes: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "reasoning_run_id": self.reasoning_run_id,
            "origin_object_id": self.origin_object_id,
            "direction": self.direction,
            "paths": [
                {"object_ids": list(p.object_ids), "edge_ids": list(p.edge_ids), "depth": p.depth, "confidence": p.confidence}
                for p in self.paths
            ],
            "impacted_object_ids": list(self.impacted_object_ids),
            "critical_object_ids": list(self.critical_object_ids),
            "confidence": self.confidence,
            "root_causes": list(self.root_causes),
        }
