"""Reusable graph navigation for Explorer and future reasoning services."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from sapientia.graph import GraphDirection
from sapientia.models.graph import (
    EnterpriseGraphDTO,
    GraphPathDTO,
    GraphTraversalDTO,
    NodeDTO,
    RelationshipDTO,
    TraversalNodeDTO,
)
from sapientia.services.enterprise_graph.enterprise_graph_service import EnterpriseGraphService


class EnterpriseGraphTraversalService:
    """Perform deterministic in-memory traversals over the canonical graph contract."""

    def __init__(self, graph_service: EnterpriseGraphService | None = None) -> None:
        self._graph_service = graph_service or EnterpriseGraphService()

    def traverse(
        self,
        project_id: int,
        business_domain: str,
        centre_node_id: int,
        *,
        max_depth: int = 2,
        direction: GraphDirection | str = GraphDirection.BOTH,
        relationship_types: Iterable[str] | None = None,
        minimum_confidence: float = 0.0,
    ) -> GraphTraversalDTO | None:
        if centre_node_id <= 0:
            raise ValueError("centre_node_id must be greater than zero.")
        if not 1 <= max_depth <= 5:
            raise ValueError("max_depth must be between 1 and 5.")
        normalized_direction = GraphDirection(str(direction).upper())
        allowed_types = self._normalize_types(relationship_types)
        graph = self._graph_service.get_graph(
            project_id,
            business_domain,
            limit=5000,
            minimum_confidence=minimum_confidence,
        )
        node_by_id = {node.node_id: node for node in graph.nodes}
        if centre_node_id not in node_by_id:
            return None

        visited_depth: dict[int, int] = {centre_node_id: 0}
        queue: deque[int] = deque([centre_node_id])
        selected_relationships: dict[int, RelationshipDTO] = {}

        while queue:
            current = queue.popleft()
            depth = visited_depth[current]
            if depth >= max_depth:
                continue
            for relationship, neighbour_id in self._adjacent(
                graph.relationships,
                current,
                normalized_direction,
                allowed_types,
            ):
                selected_relationships[relationship.relationship_id] = relationship
                if neighbour_id not in node_by_id:
                    continue
                candidate_depth = depth + 1
                if neighbour_id not in visited_depth:
                    visited_depth[neighbour_id] = candidate_depth
                    queue.append(neighbour_id)

        traversal_nodes = tuple(
            TraversalNodeDTO(node=node_by_id[node_id], depth=depth)
            for node_id, depth in sorted(
                visited_depth.items(),
                key=lambda item: (item[1], node_by_id[item[0]].canonical_name.lower(), item[0]),
            )
        )
        relationships = tuple(
            sorted(
                (
                    relationship
                    for relationship in selected_relationships.values()
                    if relationship.source_node_id in visited_depth
                    and relationship.target_node_id in visited_depth
                ),
                key=lambda item: (item.relationship_type, item.relationship_id),
            )
        )
        return GraphTraversalDTO(
            project_id=project_id,
            business_domain=graph.business_domain,
            centre_node_id=centre_node_id,
            direction=normalized_direction.value,
            max_depth=max_depth,
            nodes=traversal_nodes,
            relationships=relationships,
        )

    def shortest_path(
        self,
        project_id: int,
        business_domain: str,
        source_node_id: int,
        target_node_id: int,
        *,
        direction: GraphDirection | str = GraphDirection.BOTH,
        max_depth: int = 5,
        relationship_types: Iterable[str] | None = None,
        minimum_confidence: float = 0.0,
    ) -> GraphPathDTO:
        if source_node_id <= 0 or target_node_id <= 0:
            raise ValueError("source_node_id and target_node_id must be greater than zero.")
        if not 1 <= max_depth <= 10:
            raise ValueError("max_depth must be between 1 and 10.")
        normalized_direction = GraphDirection(str(direction).upper())
        allowed_types = self._normalize_types(relationship_types)
        graph = self._graph_service.get_graph(
            project_id,
            business_domain,
            limit=5000,
            minimum_confidence=minimum_confidence,
        )
        node_by_id = {node.node_id: node for node in graph.nodes}
        if source_node_id not in node_by_id or target_node_id not in node_by_id:
            return self._empty_path(graph, source_node_id, target_node_id, normalized_direction)
        if source_node_id == target_node_id:
            return GraphPathDTO(
                project_id=project_id,
                business_domain=graph.business_domain,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                direction=normalized_direction.value,
                found=True,
                nodes=(node_by_id[source_node_id],),
                relationships=(),
                hop_count=0,
            )

        queue: deque[tuple[int, int]] = deque([(source_node_id, 0)])
        visited = {source_node_id}
        parent: dict[int, tuple[int, RelationshipDTO]] = {}

        found = False
        while queue and not found:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for relationship, neighbour_id in self._adjacent(
                graph.relationships,
                current,
                normalized_direction,
                allowed_types,
            ):
                if neighbour_id in visited or neighbour_id not in node_by_id:
                    continue
                visited.add(neighbour_id)
                parent[neighbour_id] = (current, relationship)
                if neighbour_id == target_node_id:
                    found = True
                    break
                queue.append((neighbour_id, depth + 1))

        if not found:
            return self._empty_path(graph, source_node_id, target_node_id, normalized_direction)

        node_ids = [target_node_id]
        relationships: list[RelationshipDTO] = []
        cursor = target_node_id
        while cursor != source_node_id:
            previous, relationship = parent[cursor]
            relationships.append(relationship)
            node_ids.append(previous)
            cursor = previous
        node_ids.reverse()
        relationships.reverse()
        return GraphPathDTO(
            project_id=project_id,
            business_domain=graph.business_domain,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            direction=normalized_direction.value,
            found=True,
            nodes=tuple(node_by_id[node_id] for node_id in node_ids),
            relationships=tuple(relationships),
            hop_count=len(relationships),
        )

    @staticmethod
    def _normalize_types(values: Iterable[str] | None) -> set[str] | None:
        if values is None:
            return None
        normalized = {str(value).strip().upper() for value in values if str(value).strip()}
        return normalized or None

    @staticmethod
    def _adjacent(
        relationships: tuple[RelationshipDTO, ...],
        node_id: int,
        direction: GraphDirection,
        allowed_types: set[str] | None,
    ) -> tuple[tuple[RelationshipDTO, int], ...]:
        results: list[tuple[RelationshipDTO, int]] = []
        for relationship in relationships:
            if allowed_types and relationship.relationship_type.upper() not in allowed_types:
                continue
            if direction in (GraphDirection.OUTGOING, GraphDirection.BOTH) and relationship.source_node_id == node_id:
                results.append((relationship, relationship.target_node_id))
            if direction in (GraphDirection.INCOMING, GraphDirection.BOTH) and relationship.target_node_id == node_id:
                results.append((relationship, relationship.source_node_id))
        return tuple(results)

    @staticmethod
    def _empty_path(
        graph: EnterpriseGraphDTO,
        source_node_id: int,
        target_node_id: int,
        direction: GraphDirection,
    ) -> GraphPathDTO:
        return GraphPathDTO(
            project_id=graph.project_id,
            business_domain=graph.business_domain,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            direction=direction.value,
            found=False,
        )
