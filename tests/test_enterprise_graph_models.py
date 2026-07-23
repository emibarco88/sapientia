import pytest

from sapientia.graph import BusinessNode, BusinessRelationship, EnterpriseGraph, EvidenceReference


def node(node_id: int, name: str) -> BusinessNode:
    return BusinessNode(
        node_id=node_id,
        project_id=1,
        object_type="BUSINESS_CONCEPT",
        canonical_name=name,
        canonical_key=f"business:finance:{name.lower()}",
        status="ACTIVE",
        business_domain="FINANCE",
    )


def test_graph_builds_statistics_and_neighbours() -> None:
    relationship = BusinessRelationship(
        relationship_id=10,
        project_id=1,
        source_node_id=1,
        target_node_id=2,
        relationship_type="DENOMINATED_IN",
        confidence=0.9,
        status="ACTIVE",
    )
    graph = EnterpriseGraph.create(
        project_id=1,
        business_domain="FINANCE",
        nodes=[node(1, "Invoice"), node(2, "Currency")],
        relationships=[relationship],
        evidence_count=4,
    )
    assert graph.statistics.node_count == 2
    assert graph.statistics.relationship_count == 1
    assert graph.statistics.evidence_count == 4
    assert graph.statistics.average_relationship_confidence == pytest.approx(0.9)
    assert [item.canonical_name for item in graph.neighbours(1)] == ["Currency"]


def test_graph_rejects_relationship_to_missing_node() -> None:
    relationship = BusinessRelationship(
        relationship_id=10, project_id=1, source_node_id=1, target_node_id=99,
        relationship_type="RELATES_TO", confidence=0.7, status="ACTIVE"
    )
    with pytest.raises(ValueError, match="outside the graph"):
        EnterpriseGraph.create(project_id=1, business_domain="FINANCE", nodes=[node(1, "Invoice")], relationships=[relationship])


def test_confidence_validation() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        EvidenceReference(
            evidence_id=1, evidence_type="COLUMN", evidence_key="x", score=1.1,
            source_schema="ekr_core", source_table="column", source_record_id=1,
        )
