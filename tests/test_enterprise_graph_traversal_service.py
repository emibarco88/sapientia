from sapientia.graph import BusinessNode, BusinessRelationship, EnterpriseGraph
from sapientia.services.enterprise_graph import EnterpriseGraphService, EnterpriseGraphTraversalService


class FakeRepository:
    def __init__(self):
        self.nodes = tuple(
            BusinessNode(i, 7, "BUSINESS_CONCEPT", name, f"finance:{name.lower()}", "ACTIVE", "FINANCE")
            for i, name in enumerate(("Revenue", "Invoice", "Order", "Customer", "Currency"), start=1)
        )
        self.relationships = (
            BusinessRelationship(11, 7, 1, 2, "CALCULATED_FROM", 0.95, "ACTIVE"),
            BusinessRelationship(12, 7, 2, 3, "DERIVED_FROM", 0.90, "ACTIVE"),
            BusinessRelationship(13, 7, 3, 4, "REFERENCES", 0.85, "ACTIVE"),
            BusinessRelationship(14, 7, 2, 5, "DENOMINATED_IN", 0.92, "ACTIVE"),
        )

    def get_graph(self, project_id, business_domain, **kwargs):
        return EnterpriseGraph.create(
            project_id=project_id,
            business_domain=business_domain,
            nodes=self.nodes,
            relationships=self.relationships,
        )

    def get_node(self, project_id, node_id):
        return next((node for node in self.nodes if node.node_id == node_id), None)

    def get_node_evidence(self, project_id, node_id):
        return ()


def service():
    graph_service = EnterpriseGraphService(repository=FakeRepository())
    return EnterpriseGraphTraversalService(graph_service)


def test_traversal_returns_nodes_by_hop_depth():
    result = service().traverse(7, "finance", 1, max_depth=2, direction="OUTGOING")
    assert result is not None
    assert [(item.node.node_id, item.depth) for item in result.nodes] == [(1, 0), (2, 1), (5, 2), (3, 2)]
    assert {item.relationship_id for item in result.relationships} == {11, 12, 14}


def test_traversal_filters_relationship_types():
    result = service().traverse(
        7, "FINANCE", 1, max_depth=3, direction="OUTGOING", relationship_types=["calculated_from"]
    )
    assert result is not None
    assert [item.node.node_id for item in result.nodes] == [1, 2]


def test_shortest_path_returns_ordered_path():
    result = service().shortest_path(7, "FINANCE", 1, 4, direction="OUTGOING")
    assert result.found is True
    assert [node.node_id for node in result.nodes] == [1, 2, 3, 4]
    assert result.hop_count == 3


def test_shortest_path_reports_no_path_for_direction():
    result = service().shortest_path(7, "FINANCE", 4, 1, direction="OUTGOING")
    assert result.found is False
    assert result.nodes == ()
