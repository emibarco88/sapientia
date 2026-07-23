"""Stable DTO contract for the Enterprise Graph Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GraphDTOBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceReferenceDTO(GraphDTOBase):
    schema_name: str | None = None
    table_name: str | None = None
    object_id: int | None = None


class EvidenceDTO(GraphDTOBase):
    evidence_id: int
    evidence_type: str
    evidence_key: str
    score: float = Field(ge=0.0, le=1.0)
    source: SourceReferenceDTO
    source_record_id: int
    reasoning: str | None = None
    evidence_object_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class NodeDTO(GraphDTOBase):
    node_id: int
    project_id: int
    object_type: str
    canonical_name: str
    canonical_key: str
    status: str
    business_domain: str | None = None
    description: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    incoming_count: int = Field(default=0, ge=0)
    outgoing_count: int = Field(default=0, ge=0)
    evidence_count: int = Field(default=0, ge=0)
    source: SourceReferenceDTO
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def degree(self) -> int:
        return self.incoming_count + self.outgoing_count


class RelationshipDTO(GraphDTOBase):
    relationship_id: int
    project_id: int
    source_node_id: int
    target_node_id: int
    relationship_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: str
    discovery_class: str | None = None
    generation_method: str | None = None
    reasoning: str | None = None
    evidence_count: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GraphStatisticsDTO(GraphDTOBase):
    node_count: int = Field(ge=0)
    relationship_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    isolated_node_count: int = Field(default=0, ge=0)
    average_relationship_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    nodes_by_type: dict[str, int] = Field(default_factory=dict)
    relationships_by_type: dict[str, int] = Field(default_factory=dict)


class EnterpriseGraphDTO(GraphDTOBase):
    contract_version: str = "1.0"
    project_id: int
    business_domain: str
    nodes: tuple[NodeDTO, ...]
    relationships: tuple[RelationshipDTO, ...]
    statistics: GraphStatisticsDTO
    metadata: dict[str, Any] = Field(default_factory=dict)


class NeighbourhoodDTO(GraphDTOBase):
    contract_version: str = "1.0"
    project_id: int
    business_domain: str
    centre_node: NodeDTO
    neighbours: tuple[NodeDTO, ...]
    relationships: tuple[RelationshipDTO, ...]
    direction: str


class TraversalNodeDTO(GraphDTOBase):
    node: NodeDTO
    depth: int = Field(ge=0)


class GraphTraversalDTO(GraphDTOBase):
    contract_version: str = "1.1"
    project_id: int
    business_domain: str
    centre_node_id: int
    direction: str
    max_depth: int = Field(ge=1, le=5)
    nodes: tuple[TraversalNodeDTO, ...]
    relationships: tuple[RelationshipDTO, ...]


class GraphPathDTO(GraphDTOBase):
    contract_version: str = "1.1"
    project_id: int
    business_domain: str
    source_node_id: int
    target_node_id: int
    direction: str
    found: bool
    nodes: tuple[NodeDTO, ...] = ()
    relationships: tuple[RelationshipDTO, ...] = ()
    hop_count: int = Field(default=0, ge=0)
