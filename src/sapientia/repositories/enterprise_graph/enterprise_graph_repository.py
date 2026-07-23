"""Canonical read-only repository for the Enterprise Knowledge Graph."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import bindparam, text

from sapientia.graph.mappers import map_evidence, map_node, map_relationship
from sapientia.graph.models import BusinessNode, BusinessRelationship, EnterpriseGraph, EvidenceReference


class EnterpriseGraphRepository:
    """Storage boundary for graph reads over ekr_understanding."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def get_node(self, project_id: int, node_id: int) -> BusinessNode | None:
        row = self.connection.execute(
            text(self._NODE_SELECT + """
                WHERE eo.project_id = :project_id
                  AND eo.enterprise_object_id = :node_id
            """),
            {"project_id": project_id, "node_id": node_id},
        ).mappings().one_or_none()
        return map_node(row) if row else None

    def list_nodes(
        self,
        project_id: int,
        business_domain: str,
        *,
        limit: int = 500,
        offset: int = 0,
        object_types: Sequence[str] | None = None,
        active_only: bool = True,
    ) -> tuple[BusinessNode, ...]:
        if not 1 <= limit <= 5000:
            raise ValueError("limit must be between 1 and 5000")
        predicates = [
            "eo.project_id = :project_id",
            "UPPER(COALESCE(eo.business_domain, '')) = UPPER(:business_domain)",
        ]
        params: dict[str, object] = {
            "project_id": project_id,
            "business_domain": business_domain,
            "limit": limit,
            "offset": max(offset, 0),
        }
        if active_only:
            predicates.append("eo.status = 'ACTIVE'")
        statement = text(
            self._NODE_SELECT
            + " WHERE " + " AND ".join(predicates)
            + """
                AND (:filter_types = FALSE OR eo.object_type_code IN :object_types)
                ORDER BY eo.canonical_name, eo.enterprise_object_id
                LIMIT :limit OFFSET :offset
            """
        ).bindparams(bindparam("object_types", expanding=True))
        object_type_values = tuple(object_types or ("__NO_FILTER__",))
        params.update({"filter_types": bool(object_types), "object_types": object_type_values})
        rows = self.connection.execute(statement, params).mappings().all()
        return tuple(map_node(row) for row in rows)

    def list_relationships(
        self,
        project_id: int,
        *,
        node_ids: Sequence[int] | None = None,
        minimum_confidence: float = 0.0,
        active_only: bool = True,
    ) -> tuple[BusinessRelationship, ...]:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0 and 1")
        predicates = ["r.project_id = :project_id", "r.confidence_score >= :minimum_confidence"]
        params: dict[str, object] = {"project_id": project_id, "minimum_confidence": minimum_confidence}
        if active_only:
            predicates.append("r.status = 'ACTIVE'")
        statement_sql = self._RELATIONSHIP_SELECT + " WHERE " + " AND ".join(predicates)
        if node_ids is not None:
            ids = tuple(dict.fromkeys(int(node_id) for node_id in node_ids))
            if not ids:
                return ()
            statement_sql += " AND r.source_enterprise_object_id IN :node_ids AND r.target_enterprise_object_id IN :node_ids"
            params["node_ids"] = ids
            statement = text(statement_sql + " ORDER BY r.confidence_score DESC, r.operational_relationship_id").bindparams(
                bindparam("node_ids", expanding=True)
            )
        else:
            statement = text(statement_sql + " ORDER BY r.confidence_score DESC, r.operational_relationship_id")
        rows = self.connection.execute(statement, params).mappings().all()
        return tuple(map_relationship(row) for row in rows)

    def get_graph(
        self,
        project_id: int,
        business_domain: str,
        *,
        limit: int = 500,
        minimum_confidence: float = 0.0,
        business_objects_only: bool = False,
    ) -> EnterpriseGraph:
        object_types = None
        nodes = self.list_nodes(project_id, business_domain, limit=limit, object_types=object_types)
        if business_objects_only:
            nodes = tuple(node for node in nodes if node.object_type.startswith("BUSINESS_"))
        relationships = self.list_relationships(
            project_id,
            node_ids=[node.node_id for node in nodes],
            minimum_confidence=minimum_confidence,
        )
        evidence_count = sum(node.evidence_count for node in nodes) + sum(item.evidence_count for item in relationships)
        return EnterpriseGraph.create(
            project_id=project_id,
            business_domain=business_domain,
            nodes=nodes,
            relationships=relationships,
            evidence_count=evidence_count,
            metadata={"minimum_confidence": minimum_confidence, "limit": limit},
        )

    def get_node_evidence(self, project_id: int, node_id: int) -> tuple[EvidenceReference, ...]:
        rows = self.connection.execute(
            text("""
                SELECT
                    boe.business_object_evidence_id,
                    boe.evidence_enterprise_object_id,
                    boe.evidence_type,
                    boe.evidence_key,
                    boe.evidence_score,
                    boe.source_schema,
                    boe.source_table,
                    boe.source_record_id,
                    boe.reasoning,
                    boe.evidence_json,
                    boe.created_at
                FROM ekr_understanding.business_object_evidence boe
                JOIN ekr_understanding.enterprise_object eo
                  ON eo.enterprise_object_id = boe.business_enterprise_object_id
                WHERE eo.project_id = :project_id
                  AND boe.business_enterprise_object_id = :node_id
                ORDER BY boe.evidence_score DESC, boe.business_object_evidence_id
            """),
            {"project_id": project_id, "node_id": node_id},
        ).mappings().all()
        return tuple(map_evidence(row) for row in rows)

    _NODE_SELECT = """
        SELECT
            eo.enterprise_object_id,
            eo.project_id,
            eo.object_type_code,
            eo.source_schema,
            eo.source_table,
            eo.source_object_id,
            eo.canonical_name,
            eo.canonical_key,
            eo.description,
            eo.business_domain,
            eo.status,
            eo.metadata_json,
            eo.created_at,
            eo.updated_at,
            COALESCE(stats.incoming_count, 0) AS incoming_count,
            COALESCE(stats.outgoing_count, 0) AS outgoing_count,
            COALESCE(stats.average_confidence, 0) AS average_confidence,
            COALESCE(evidence.evidence_count, 0) AS evidence_count
        FROM ekr_understanding.enterprise_object eo
        LEFT JOIN (
            SELECT object_id,
                   SUM(incoming_count) AS incoming_count,
                   SUM(outgoing_count) AS outgoing_count,
                   AVG(confidence_score) AS average_confidence
            FROM (
                SELECT target_enterprise_object_id AS object_id, COUNT(*) AS incoming_count,
                       0 AS outgoing_count, AVG(confidence_score) AS confidence_score
                FROM ekr_understanding.operational_relationship
                WHERE status = 'ACTIVE' GROUP BY target_enterprise_object_id
                UNION ALL
                SELECT source_enterprise_object_id AS object_id, 0 AS incoming_count,
                       COUNT(*) AS outgoing_count, AVG(confidence_score) AS confidence_score
                FROM ekr_understanding.operational_relationship
                WHERE status = 'ACTIVE' GROUP BY source_enterprise_object_id
            ) relationship_counts GROUP BY object_id
        ) stats ON stats.object_id = eo.enterprise_object_id
        LEFT JOIN (
            SELECT business_enterprise_object_id AS object_id, COUNT(*) AS evidence_count
            FROM ekr_understanding.business_object_evidence
            GROUP BY business_enterprise_object_id
        ) evidence ON evidence.object_id = eo.enterprise_object_id
    """

    _RELATIONSHIP_SELECT = """
        SELECT
            r.operational_relationship_id,
            r.project_id,
            r.source_enterprise_object_id,
            r.target_enterprise_object_id,
            r.relationship_type_code,
            r.discovery_class,
            r.generation_method,
            r.confidence_score,
            r.reasoning,
            r.status,
            r.metadata_json,
            r.created_at,
            r.updated_at,
            COALESCE(evidence.evidence_count, 0) AS evidence_count
        FROM ekr_understanding.operational_relationship r
        LEFT JOIN (
            SELECT operational_relationship_id, COUNT(*) AS evidence_count
            FROM ekr_understanding.relationship_evidence
            GROUP BY operational_relationship_id
        ) evidence ON evidence.operational_relationship_id = r.operational_relationship_id
    """
