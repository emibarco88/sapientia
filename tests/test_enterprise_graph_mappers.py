from sapientia.graph.mappers import map_node, map_relationship


def test_map_node_from_database_shape() -> None:
    node = map_node({
        "enterprise_object_id": 7, "project_id": 1, "object_type_code": "BUSINESS_ENTITY",
        "canonical_name": "Invoice", "canonical_key": "business:finance:invoice",
        "status": "ACTIVE", "average_confidence": 0.82, "incoming_count": 2,
        "outgoing_count": 3, "evidence_count": 4, "metadata_json": {"provider_id": "finance-core"},
    })
    assert node.node_id == 7
    assert node.degree == 5
    assert node.metadata["provider_id"] == "finance-core"


def test_map_relationship_from_database_shape() -> None:
    relationship = map_relationship({
        "operational_relationship_id": 9, "project_id": 1,
        "source_enterprise_object_id": 7, "target_enterprise_object_id": 8,
        "relationship_type_code": "DENOMINATED_IN", "confidence_score": 0.91,
        "status": "ACTIVE", "evidence_count": 2,
    })
    assert relationship.relationship_id == 9
    assert relationship.source_node_id == 7
    assert relationship.confidence == 0.91
