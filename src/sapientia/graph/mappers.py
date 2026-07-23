from __future__ import annotations

from typing import Any, Mapping

from sapientia.graph.models import BusinessNode, BusinessRelationship, EvidenceReference


def _value(row: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return default


def map_node(row: Mapping[str, Any]) -> BusinessNode:
    return BusinessNode(
        node_id=int(_value(row, "enterprise_object_id", "node_id")),
        project_id=int(row["project_id"]),
        object_type=str(_value(row, "object_type_code", "object_type")),
        canonical_name=str(row["canonical_name"]),
        canonical_key=str(row["canonical_key"]),
        status=str(row["status"]),
        business_domain=_value(row, "business_domain"),
        description=_value(row, "description"),
        source_schema=_value(row, "source_schema"),
        source_table=_value(row, "source_table"),
        source_object_id=_value(row, "source_object_id"),
        confidence=_value(row, "confidence", "average_confidence"),
        incoming_count=int(_value(row, "incoming_count", default=0)),
        outgoing_count=int(_value(row, "outgoing_count", default=0)),
        evidence_count=int(_value(row, "evidence_count", default=0)),
        metadata=_value(row, "metadata_json", "metadata", default={}),
        created_at=_value(row, "created_at"),
        updated_at=_value(row, "updated_at"),
    )


def map_relationship(row: Mapping[str, Any]) -> BusinessRelationship:
    return BusinessRelationship(
        relationship_id=int(_value(row, "operational_relationship_id", "relationship_id")),
        project_id=int(row["project_id"]),
        source_node_id=int(_value(row, "source_enterprise_object_id", "source_node_id")),
        target_node_id=int(_value(row, "target_enterprise_object_id", "target_node_id")),
        relationship_type=str(_value(row, "relationship_type_code", "relationship_type")),
        confidence=float(_value(row, "confidence_score", "confidence")),
        status=str(row["status"]),
        discovery_class=_value(row, "discovery_class"),
        generation_method=_value(row, "generation_method"),
        reasoning=_value(row, "reasoning"),
        evidence_count=int(_value(row, "evidence_count", default=0)),
        metadata=_value(row, "metadata_json", "metadata", default={}),
        created_at=_value(row, "created_at"),
        updated_at=_value(row, "updated_at"),
    )


def map_evidence(row: Mapping[str, Any]) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=int(_value(row, "business_object_evidence_id", "relationship_evidence_id", "evidence_id")),
        evidence_type=str(row["evidence_type"]),
        evidence_key=str(row["evidence_key"]),
        score=float(_value(row, "evidence_score", "score")),
        source_schema=str(row["source_schema"]),
        source_table=str(row["source_table"]),
        source_record_id=int(row["source_record_id"]),
        reasoning=_value(row, "reasoning"),
        evidence_object_id=_value(row, "evidence_enterprise_object_id"),
        metadata=_value(row, "evidence_json", "metadata_json", "metadata", default={}),
        created_at=_value(row, "created_at"),
    )
