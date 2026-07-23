"""Enterprise Explorer projection backed by EnterpriseGraphService."""

from __future__ import annotations

from typing import Any

from sapientia.models.graph import EnterpriseGraphDTO
from sapientia.services.enterprise_graph import EnterpriseGraphService


class EnterpriseExplorerService:
    """Preserves the Explorer API contract while removing storage coupling."""

    def __init__(self, graph_service: EnterpriseGraphService | None = None) -> None:
        self.graph_service = graph_service or EnterpriseGraphService()

    def get_graph(
        self,
        project_id: int,
        business_domain: str,
        limit: int = 250,
        minimum_confidence: float = 0.0,
    ) -> dict[str, Any]:
        graph = self.graph_service.get_graph(
            project_id,
            business_domain,
            limit=limit,
            minimum_confidence=minimum_confidence,
        )
        return self._to_explorer_contract(graph)

    @staticmethod
    def _to_explorer_contract(graph: EnterpriseGraphDTO) -> dict[str, Any]:
        finding_count = sum(int(node.metadata.get("finding_count", 0) or 0) for node in graph.nodes)
        recommendation_count = sum(
            int(node.metadata.get("recommendation_count", 0) or 0) for node in graph.nodes
        )
        return {
            "project_id": graph.project_id,
            "business_domain": graph.business_domain,
            "summary": {
                "node_count": graph.statistics.node_count,
                "edge_count": graph.statistics.relationship_count,
                "finding_count": finding_count,
                "recommendation_count": recommendation_count,
                "object_types": graph.statistics.nodes_by_type,
                "relationship_types": graph.statistics.relationships_by_type,
            },
            "nodes": [
                {
                    "id": str(node.node_id),
                    "enterprise_object_id": node.node_id,
                    "label": node.canonical_name,
                    "canonical_key": node.canonical_key,
                    "object_type": node.object_type,
                    "description": node.description,
                    "business_domain": node.business_domain,
                    "confidence": float(node.confidence or 0.0),
                    "incoming_count": node.incoming_count,
                    "outgoing_count": node.outgoing_count,
                    "finding_count": int(node.metadata.get("finding_count", 0) or 0),
                    "recommendation_count": int(node.metadata.get("recommendation_count", 0) or 0),
                    "source": {
                        "schema": node.source.schema_name,
                        "table": node.source.table_name,
                        "object_id": node.source.object_id,
                    },
                    "metadata": node.metadata,
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "id": str(edge.relationship_id),
                    "operational_relationship_id": edge.relationship_id,
                    "source": str(edge.source_node_id),
                    "target": str(edge.target_node_id),
                    "relationship_type": edge.relationship_type,
                    "label": edge.relationship_type.replace("_", " ").title(),
                    "confidence": edge.confidence,
                    "evidence_count": edge.evidence_count,
                    "discovery_class": edge.discovery_class,
                    "generation_method": edge.generation_method,
                    "reasoning": edge.reasoning,
                    "metadata": edge.metadata,
                }
                for edge in graph.relationships
            ],
        }
