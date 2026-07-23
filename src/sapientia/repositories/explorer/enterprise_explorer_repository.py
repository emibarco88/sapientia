"""
Repository for projecting Enterprise Understanding into a bounded graph.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import bindparam, text


class EnterpriseExplorerRepository:
    """Read-only graph projection over Enterprise Understanding."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def get_graph(
        self,
        project_id: int,
        business_domain: str,
        limit: int,
        minimum_confidence: float,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Return enterprise objects and active relationships for one domain.

        Nodes are bounded before edges are loaded so the API never returns an
        unbounded enterprise graph.
        """

        node_rows = self.connection.execute(
            text(
                """
                WITH relationship_stats AS
                (
                    SELECT
                        object_id,
                        SUM(incoming_count) AS incoming_count,
                        SUM(outgoing_count) AS outgoing_count,
                        AVG(confidence_score) AS average_confidence
                    FROM
                    (
                        SELECT
                            target_enterprise_object_id AS object_id,
                            COUNT(*) AS incoming_count,
                            0 AS outgoing_count,
                            AVG(confidence_score) AS confidence_score
                        FROM ekr_understanding.operational_relationship
                        WHERE project_id = :project_id
                          AND status = 'ACTIVE'
                          AND confidence_score >= :minimum_confidence
                        GROUP BY target_enterprise_object_id

                        UNION ALL

                        SELECT
                            source_enterprise_object_id AS object_id,
                            0 AS incoming_count,
                            COUNT(*) AS outgoing_count,
                            AVG(confidence_score) AS confidence_score
                        FROM ekr_understanding.operational_relationship
                        WHERE project_id = :project_id
                          AND status = 'ACTIVE'
                          AND confidence_score >= :minimum_confidence
                        GROUP BY source_enterprise_object_id
                    ) raw_stats
                    GROUP BY object_id
                ),
                intelligence_stats AS
                (
                    SELECT
                        enterprise_object_id,
                        COUNT(*) FILTER
                        (
                            WHERE knowledge_type = 'INTELLIGENCE_FINDING'
                        ) AS finding_count,
                        COUNT(*) FILTER
                        (
                            WHERE knowledge_type = 'RECOMMENDATION'
                        ) AS recommendation_count
                    FROM ekr_ai.ai_knowledge_item
                    WHERE project_id = :project_id
                      AND UPPER(business_domain) = UPPER(:business_domain)
                      AND is_active = TRUE
                      AND enterprise_object_id IS NOT NULL
                    GROUP BY enterprise_object_id
                )
                SELECT
                    enterprise_object.enterprise_object_id,
                    enterprise_object.object_type_code,
                    enterprise_object.canonical_name,
                    enterprise_object.canonical_key,
                    enterprise_object.description,
                    enterprise_object.business_domain,
                    enterprise_object.source_schema,
                    enterprise_object.source_table,
                    enterprise_object.source_object_id,
                    enterprise_object.metadata_json,

                    COALESCE(
                        relationship_stats.incoming_count,
                        0
                    ) AS incoming_count,

                    COALESCE(
                        relationship_stats.outgoing_count,
                        0
                    ) AS outgoing_count,

                    COALESCE(
                        relationship_stats.average_confidence,
                        0
                    ) AS average_confidence,

                    COALESCE(
                        intelligence_stats.finding_count,
                        0
                    ) AS finding_count,

                    COALESCE(
                        intelligence_stats.recommendation_count,
                        0
                    ) AS recommendation_count

                FROM ekr_understanding.enterprise_object enterprise_object

                LEFT JOIN relationship_stats
                  ON relationship_stats.object_id =
                     enterprise_object.enterprise_object_id

                LEFT JOIN intelligence_stats
                  ON intelligence_stats.enterprise_object_id =
                     enterprise_object.enterprise_object_id

                WHERE enterprise_object.project_id = :project_id
                  AND enterprise_object.status = 'ACTIVE'
                  AND
                  (
                      NOT EXISTS
                      (
                          SELECT 1
                          FROM ekr_understanding.enterprise_object business_object
                          WHERE business_object.project_id = :project_id
                            AND business_object.status = 'ACTIVE'
                            AND UPPER(COALESCE(business_object.business_domain, '')) =
                                UPPER(:business_domain)
                            AND business_object.object_type_code LIKE 'BUSINESS_%'
                      )
                      OR enterprise_object.object_type_code LIKE 'BUSINESS_%'
                  )
                  AND UPPER(
                        COALESCE(
                            enterprise_object.business_domain,
                            ''
                        )
                      ) = UPPER(:business_domain)

                ORDER BY
                    (
                        COALESCE(
                            relationship_stats.incoming_count,
                            0
                        )
                        +
                        COALESCE(
                            relationship_stats.outgoing_count,
                            0
                        )
                    ) DESC,
                    enterprise_object.canonical_name

                LIMIT :limit
                """
            ),
            {
                "project_id": project_id,
                "business_domain": business_domain,
                "minimum_confidence": minimum_confidence,
                "limit": limit,
            },
        ).mappings().all()

        node_ids = [
            int(row["enterprise_object_id"])
            for row in node_rows
        ]

        if not node_ids:
            return {
                "nodes": [],
                "edges": [],
            }

        edge_statement = text(
            """
            SELECT
                relationship.operational_relationship_id,
                relationship.source_enterprise_object_id,
                relationship.target_enterprise_object_id,
                relationship.relationship_type_code,
                relationship.discovery_class,
                relationship.generation_method,
                relationship.confidence_score,
                relationship.reasoning,
                relationship.metadata_json,
                COALESCE(
                    evidence_stats.evidence_count,
                    0
                ) AS evidence_count

            FROM ekr_understanding.operational_relationship relationship

            LEFT JOIN
            (
                SELECT
                    operational_relationship_id,
                    COUNT(*) AS evidence_count
                FROM ekr_understanding.relationship_evidence
                GROUP BY operational_relationship_id
            ) evidence_stats
              ON evidence_stats.operational_relationship_id =
                 relationship.operational_relationship_id

            WHERE relationship.project_id = :project_id
              AND relationship.status = 'ACTIVE'
              AND relationship.confidence_score >= :minimum_confidence
              AND relationship.source_enterprise_object_id IN :node_ids
              AND relationship.target_enterprise_object_id IN :node_ids

            ORDER BY
                relationship.confidence_score DESC,
                relationship.operational_relationship_id
            """
        ).bindparams(
            bindparam(
                "node_ids",
                expanding=True,
            )
        )

        edge_rows = self.connection.execute(
            edge_statement,
            {
                "project_id": project_id,
                "minimum_confidence": minimum_confidence,
                "node_ids": node_ids,
            },
        ).mappings().all()

        return {
            "nodes": [
                dict(row)
                for row in node_rows
            ],
            "edges": [
                dict(row)
                for row in edge_rows
            ],
        }
