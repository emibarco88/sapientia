from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable, Mapping

JsonObject = dict[str, Any]


def _json(value: Mapping[str, Any] | None) -> JsonObject:
    return dict(value or {})


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    evidence_id: int
    evidence_type: str
    evidence_key: str
    score: float
    source_schema: str
    source_table: str
    source_record_id: int
    reasoning: str | None = None
    evidence_object_id: int | None = None
    metadata: JsonObject = field(default_factory=dict)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Evidence score must be between 0 and 1.")
        object.__setattr__(self, "metadata", _json(self.metadata))


@dataclass(frozen=True, slots=True)
class BusinessNode:
    node_id: int
    project_id: int
    object_type: str
    canonical_name: str
    canonical_key: str
    status: str
    business_domain: str | None = None
    description: str | None = None
    source_schema: str | None = None
    source_table: str | None = None
    source_object_id: int | None = None
    confidence: float | None = None
    incoming_count: int = 0
    outgoing_count: int = 0
    evidence_count: int = 0
    metadata: JsonObject = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.node_id <= 0 or self.project_id <= 0:
            raise ValueError("Node and project identifiers must be positive.")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Node confidence must be between 0 and 1.")
        for value in (self.incoming_count, self.outgoing_count, self.evidence_count):
            if value < 0:
                raise ValueError("Graph counts cannot be negative.")
        object.__setattr__(self, "metadata", _json(self.metadata))

    @property
    def degree(self) -> int:
        return self.incoming_count + self.outgoing_count


@dataclass(frozen=True, slots=True)
class BusinessRelationship:
    relationship_id: int
    project_id: int
    source_node_id: int
    target_node_id: int
    relationship_type: str
    confidence: float
    status: str
    discovery_class: str | None = None
    generation_method: str | None = None
    reasoning: str | None = None
    evidence_count: int = 0
    metadata: JsonObject = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if min(self.relationship_id, self.project_id, self.source_node_id, self.target_node_id) <= 0:
            raise ValueError("Relationship identifiers must be positive.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Relationship confidence must be between 0 and 1.")
        if self.evidence_count < 0:
            raise ValueError("Evidence count cannot be negative.")
        object.__setattr__(self, "metadata", _json(self.metadata))


@dataclass(frozen=True, slots=True)
class GraphStatistics:
    node_count: int
    relationship_count: int
    evidence_count: int
    isolated_node_count: int = 0
    average_relationship_confidence: float = 0.0
    nodes_by_type: JsonObject = field(default_factory=dict)
    relationships_by_type: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        if min(self.node_count, self.relationship_count, self.evidence_count, self.isolated_node_count) < 0:
            raise ValueError("Graph statistics cannot be negative.")
        if not 0.0 <= self.average_relationship_confidence <= 1.0:
            raise ValueError("Average confidence must be between 0 and 1.")
        object.__setattr__(self, "nodes_by_type", _json(self.nodes_by_type))
        object.__setattr__(self, "relationships_by_type", _json(self.relationships_by_type))


@dataclass(frozen=True, slots=True)
class EnterpriseGraph:
    project_id: int
    business_domain: str
    nodes: tuple[BusinessNode, ...]
    relationships: tuple[BusinessRelationship, ...]
    statistics: GraphStatistics
    metadata: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "relationships", tuple(self.relationships))
        object.__setattr__(self, "metadata", _json(self.metadata))
        node_ids = {node.node_id for node in self.nodes}
        invalid = [r.relationship_id for r in self.relationships if r.source_node_id not in node_ids or r.target_node_id not in node_ids]
        if invalid:
            raise ValueError(f"Relationships reference nodes outside the graph: {invalid}")

    def node(self, node_id: int) -> BusinessNode | None:
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def neighbours(self, node_id: int) -> tuple[BusinessNode, ...]:
        neighbour_ids: set[int] = set()
        for relationship in self.relationships:
            if relationship.source_node_id == node_id:
                neighbour_ids.add(relationship.target_node_id)
            if relationship.target_node_id == node_id:
                neighbour_ids.add(relationship.source_node_id)
        return tuple(node for node in self.nodes if node.node_id in neighbour_ids)

    @classmethod
    def create(
        cls,
        *,
        project_id: int,
        business_domain: str,
        nodes: Iterable[BusinessNode],
        relationships: Iterable[BusinessRelationship],
        evidence_count: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> "EnterpriseGraph":
        node_tuple = tuple(nodes)
        relationship_tuple = tuple(relationships)
        nodes_by_type: dict[str, int] = {}
        relationships_by_type: dict[str, int] = {}
        for node in node_tuple:
            nodes_by_type[node.object_type] = nodes_by_type.get(node.object_type, 0) + 1
        for relationship in relationship_tuple:
            relationships_by_type[relationship.relationship_type] = relationships_by_type.get(relationship.relationship_type, 0) + 1
        average = (
            sum(item.confidence for item in relationship_tuple) / len(relationship_tuple)
            if relationship_tuple else 0.0
        )
        connected_ids = {
            item for relationship in relationship_tuple
            for item in (relationship.source_node_id, relationship.target_node_id)
        }
        statistics = GraphStatistics(
            node_count=len(node_tuple),
            relationship_count=len(relationship_tuple),
            evidence_count=evidence_count,
            isolated_node_count=sum(node.node_id not in connected_ids for node in node_tuple),
            average_relationship_confidence=average,
            nodes_by_type=nodes_by_type,
            relationships_by_type=relationships_by_type,
        )
        return cls(project_id, business_domain, node_tuple, relationship_tuple, statistics, _json(metadata))
