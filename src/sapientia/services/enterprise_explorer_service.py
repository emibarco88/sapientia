"""
Application service for the Enterprise Explorer graph projection.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from sapientia.db.connection import get_engine
from sapientia.repositories.explorer.enterprise_explorer_repository import (
    EnterpriseExplorerRepository,
)


class EnterpriseExplorerService:
    """Build a UI-ready graph for one project and business domain."""

    def get_graph(
        self,
        project_id: int,
        business_domain: str,
        limit: int = 250,
        minimum_confidence: float = 0.0,
    ) -> dict[str, Any]:
        if project_id <= 0:
            raise ValueError(
                "project_id must be greater than zero."
            )

        normalized_domain = str(
            business_domain or ""
        ).strip().upper()

        if not normalized_domain:
            raise ValueError(
                "A business domain is required."
            )

        bounded_limit = min(
            max(int(limit), 1),
            500,
        )

        bounded_confidence = min(
            max(float(minimum_confidence), 0.0),
            1.0,
        )

        engine = get_engine()

        with engine.begin() as connection:
            repository = EnterpriseExplorerRepository(
                connection
            )

            graph = repository.get_graph(
                project_id=project_id,
                business_domain=normalized_domain,
                limit=bounded_limit,
                minimum_confidence=bounded_confidence,
            )

        object_types = Counter(
            str(
                node.get(
                    "object_type_code"
                )
                or "UNKNOWN"
            )
            for node in graph["nodes"]
        )

        relationship_types = Counter(
            str(
                edge.get(
                    "relationship_type_code"
                )
                or "RELATED_TO"
            )
            for edge in graph["edges"]
        )

        return {
            "project_id": project_id,
            "business_domain": normalized_domain,
            "summary": {
                "node_count": len(
                    graph["nodes"]
                ),
                "edge_count": len(
                    graph["edges"]
                ),
                "finding_count": sum(
                    int(
                        node.get(
                            "finding_count"
                        )
                        or 0
                    )
                    for node in graph["nodes"]
                ),
                "recommendation_count": sum(
                    int(
                        node.get(
                            "recommendation_count"
                        )
                        or 0
                    )
                    for node in graph["nodes"]
                ),
                "object_types": dict(
                    object_types
                ),
                "relationship_types": dict(
                    relationship_types
                ),
            },
            "nodes": [
                {
                    "id": str(
                        node[
                            "enterprise_object_id"
                        ]
                    ),
                    "enterprise_object_id": int(
                        node[
                            "enterprise_object_id"
                        ]
                    ),
                    "label": node[
                        "canonical_name"
                    ],
                    "canonical_key": node[
                        "canonical_key"
                    ],
                    "object_type": node[
                        "object_type_code"
                    ],
                    "description": node.get(
                        "description"
                    ),
                    "business_domain": node.get(
                        "business_domain"
                    ),
                    "confidence": float(
                        node.get(
                            "average_confidence"
                        )
                        or 0
                    ),
                    "incoming_count": int(
                        node.get(
                            "incoming_count"
                        )
                        or 0
                    ),
                    "outgoing_count": int(
                        node.get(
                            "outgoing_count"
                        )
                        or 0
                    ),
                    "finding_count": int(
                        node.get(
                            "finding_count"
                        )
                        or 0
                    ),
                    "recommendation_count": int(
                        node.get(
                            "recommendation_count"
                        )
                        or 0
                    ),
                    "source": {
                        "schema": node.get(
                            "source_schema"
                        ),
                        "table": node.get(
                            "source_table"
                        ),
                        "object_id": node.get(
                            "source_object_id"
                        ),
                    },
                    "metadata": node.get(
                        "metadata_json"
                    )
                    or {},
                }
                for node in graph["nodes"]
            ],
            "edges": [
                {
                    "id": str(
                        edge[
                            "operational_relationship_id"
                        ]
                    ),
                    "operational_relationship_id": int(
                        edge[
                            "operational_relationship_id"
                        ]
                    ),
                    "source": str(
                        edge[
                            "source_enterprise_object_id"
                        ]
                    ),
                    "target": str(
                        edge[
                            "target_enterprise_object_id"
                        ]
                    ),
                    "relationship_type": edge[
                        "relationship_type_code"
                    ],
                    "label": str(
                        edge[
                            "relationship_type_code"
                        ]
                    ).replace(
                        "_",
                        " ",
                    ).title(),
                    "confidence": float(
                        edge.get(
                            "confidence_score"
                        )
                        or 0
                    ),
                    "evidence_count": int(
                        edge.get(
                            "evidence_count"
                        )
                        or 0
                    ),
                    "discovery_class": edge.get(
                        "discovery_class"
                    ),
                    "generation_method": edge.get(
                        "generation_method"
                    ),
                    "reasoning": edge.get(
                        "reasoning"
                    ),
                    "metadata": edge.get(
                        "metadata_json"
                    )
                    or {},
                }
                for edge in graph["edges"]
            ],
        }
