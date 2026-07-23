"""Application boundary for all Enterprise Graph reads."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from typing import Any, Protocol

from sapientia.db.connection import get_engine
from sapientia.graph import GraphDirection
from sapientia.graph.models import (
    BusinessNode,
    BusinessRelationship,
    EnterpriseGraph,
    EvidenceReference,
    GraphStatistics,
)
from sapientia.models.graph import (
    EnterpriseGraphDTO,
    EvidenceDTO,
    GraphStatisticsDTO,
    NeighbourhoodDTO,
    NodeDTO,
    RelationshipDTO,
    SourceReferenceDTO,
)
from sapientia.repositories.enterprise_graph import EnterpriseGraphRepository


class GraphRepositoryProtocol(Protocol):
    def get_node(self, project_id: int, node_id: int) -> BusinessNode | None: ...
    def get_graph(self, project_id: int, business_domain: str, *, limit: int = 500,
                  minimum_confidence: float = 0.0, business_objects_only: bool = False) -> EnterpriseGraph: ...
    def get_node_evidence(self, project_id: int, node_id: int) -> tuple[EvidenceReference, ...]: ...


class EnterpriseGraphService:
    """Stable graph contract used by Explorer and future reasoning capabilities."""

    def __init__(
        self,
        repository: GraphRepositoryProtocol | None = None,
        connection_factory: Callable[[], AbstractContextManager[Any]] | None = None,
    ) -> None:
        self._repository = repository
        self._connection_factory = connection_factory

    def get_graph(
        self,
        project_id: int,
        business_domain: str,
        *,
        limit: int = 500,
        minimum_confidence: float = 0.0,
        business_objects_only: bool = False,
    ) -> EnterpriseGraphDTO:
        domain = self._validate(project_id, business_domain, limit, minimum_confidence)
        return self._with_repository(
            lambda repository: self._graph_to_dto(
                repository.get_graph(
                    project_id,
                    domain,
                    limit=limit,
                    minimum_confidence=minimum_confidence,
                    business_objects_only=business_objects_only,
                )
            )
        )

    def get_node(self, project_id: int, node_id: int) -> NodeDTO | None:
        if project_id <= 0 or node_id <= 0:
            raise ValueError("project_id and node_id must be greater than zero.")
        return self._with_repository(
            lambda repository: (
                self._node_to_dto(node)
                if (node := repository.get_node(project_id, node_id)) is not None
                else None
            )
        )

    def get_node_evidence(self, project_id: int, node_id: int) -> tuple[EvidenceDTO, ...]:
        if project_id <= 0 or node_id <= 0:
            raise ValueError("project_id and node_id must be greater than zero.")
        return self._with_repository(
            lambda repository: tuple(
                self._evidence_to_dto(item)
                for item in repository.get_node_evidence(project_id, node_id)
            )
        )

    def get_statistics(
        self,
        project_id: int,
        business_domain: str,
        *,
        minimum_confidence: float = 0.0,
    ) -> GraphStatisticsDTO:
        graph = self.get_graph(
            project_id,
            business_domain,
            limit=5000,
            minimum_confidence=minimum_confidence,
        )
        return graph.statistics

    def get_neighbours(
        self,
        project_id: int,
        business_domain: str,
        node_id: int,
        *,
        direction: GraphDirection | str = GraphDirection.BOTH,
        limit: int = 5000,
        minimum_confidence: float = 0.0,
    ) -> NeighbourhoodDTO | None:
        domain = self._validate(project_id, business_domain, limit, minimum_confidence)
        if node_id <= 0:
            raise ValueError("node_id must be greater than zero.")
        normalized_direction = GraphDirection(str(direction).upper())
        graph = self.get_graph(
            project_id,
            domain,
            limit=limit,
            minimum_confidence=minimum_confidence,
        )
        centre = next((item for item in graph.nodes if item.node_id == node_id), None)
        if centre is None:
            return None
        relationships = tuple(
            item for item in graph.relationships
            if self._matches_direction(item, node_id, normalized_direction)
        )
        neighbour_ids = {
            item.target_node_id if item.source_node_id == node_id else item.source_node_id
            for item in relationships
        }
        neighbours = tuple(item for item in graph.nodes if item.node_id in neighbour_ids)
        return NeighbourhoodDTO(
            project_id=project_id,
            business_domain=domain,
            centre_node=centre,
            neighbours=neighbours,
            relationships=relationships,
            direction=normalized_direction.value,
        )

    def _with_repository(self, operation: Callable[[GraphRepositoryProtocol], Any]) -> Any:
        if self._repository is not None:
            return operation(self._repository)
        context = self._connection_factory() if self._connection_factory else get_engine().begin()
        with context as connection:
            return operation(EnterpriseGraphRepository(connection))

    @staticmethod
    def _validate(project_id: int, business_domain: str, limit: int, confidence: float) -> str:
        if project_id <= 0:
            raise ValueError("project_id must be greater than zero.")
        domain = str(business_domain or "").strip().upper()
        if not domain:
            raise ValueError("A business domain is required.")
        if not 1 <= limit <= 5000:
            raise ValueError("limit must be between 1 and 5000.")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1.")
        return domain

    @staticmethod
    def _matches_direction(
        relationship: RelationshipDTO,
        node_id: int,
        direction: GraphDirection,
    ) -> bool:
        if direction is GraphDirection.OUTGOING:
            return relationship.source_node_id == node_id
        if direction is GraphDirection.INCOMING:
            return relationship.target_node_id == node_id
        return relationship.source_node_id == node_id or relationship.target_node_id == node_id

    @classmethod
    def _graph_to_dto(cls, graph: EnterpriseGraph) -> EnterpriseGraphDTO:
        return EnterpriseGraphDTO(
            project_id=graph.project_id,
            business_domain=graph.business_domain.upper(),
            nodes=tuple(cls._node_to_dto(item) for item in graph.nodes),
            relationships=tuple(cls._relationship_to_dto(item) for item in graph.relationships),
            statistics=cls._statistics_to_dto(graph.statistics),
            metadata=dict(graph.metadata),
        )

    @staticmethod
    def _node_to_dto(node: BusinessNode) -> NodeDTO:
        return NodeDTO(
            node_id=node.node_id,
            project_id=node.project_id,
            object_type=node.object_type,
            canonical_name=node.canonical_name,
            canonical_key=node.canonical_key,
            status=node.status,
            business_domain=node.business_domain,
            description=node.description,
            confidence=node.confidence,
            incoming_count=node.incoming_count,
            outgoing_count=node.outgoing_count,
            evidence_count=node.evidence_count,
            source=SourceReferenceDTO(
                schema_name=node.source_schema,
                table_name=node.source_table,
                object_id=node.source_object_id,
            ),
            metadata=dict(node.metadata),
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    @staticmethod
    def _relationship_to_dto(item: BusinessRelationship) -> RelationshipDTO:
        return RelationshipDTO(
            relationship_id=item.relationship_id,
            project_id=item.project_id,
            source_node_id=item.source_node_id,
            target_node_id=item.target_node_id,
            relationship_type=item.relationship_type,
            confidence=item.confidence,
            status=item.status,
            discovery_class=item.discovery_class,
            generation_method=item.generation_method,
            reasoning=item.reasoning,
            evidence_count=item.evidence_count,
            metadata=dict(item.metadata),
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def _evidence_to_dto(item: EvidenceReference) -> EvidenceDTO:
        return EvidenceDTO(
            evidence_id=item.evidence_id,
            evidence_type=item.evidence_type,
            evidence_key=item.evidence_key,
            score=item.score,
            source=SourceReferenceDTO(
                schema_name=item.source_schema,
                table_name=item.source_table,
                object_id=item.evidence_object_id,
            ),
            source_record_id=item.source_record_id,
            reasoning=item.reasoning,
            evidence_object_id=item.evidence_object_id,
            metadata=dict(item.metadata),
            created_at=item.created_at,
        )

    @staticmethod
    def _statistics_to_dto(item: GraphStatistics) -> GraphStatisticsDTO:
        return GraphStatisticsDTO(
            node_count=item.node_count,
            relationship_count=item.relationship_count,
            evidence_count=item.evidence_count,
            isolated_node_count=item.isolated_node_count,
            average_relationship_confidence=item.average_relationship_confidence,
            nodes_by_type=dict(item.nodes_by_type),
            relationships_by_type=dict(item.relationships_by_type),
        )
