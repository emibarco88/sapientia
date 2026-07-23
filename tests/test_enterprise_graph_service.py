from sapientia.graph import BusinessNode, BusinessRelationship, EnterpriseGraph, EvidenceReference
from sapientia.services.enterprise_graph import EnterpriseGraphService


class FakeRepository:
    def __init__(self):
        self.nodes = (
            BusinessNode(1, 7, "BUSINESS_ENTITY", "Invoice", "finance:invoice", "ACTIVE", "FINANCE"),
            BusinessNode(2, 7, "BUSINESS_CONCEPT", "Currency", "finance:currency", "ACTIVE", "FINANCE"),
            BusinessNode(3, 7, "BUSINESS_CONCEPT", "Supplier", "finance:supplier", "ACTIVE", "FINANCE"),
        )
        self.relationships = (
            BusinessRelationship(11, 7, 1, 2, "DENOMINATED_IN", 0.91, "ACTIVE"),
            BusinessRelationship(12, 7, 3, 1, "ISSUED_BY", 0.88, "ACTIVE"),
        )

    def get_graph(self, project_id, business_domain, **kwargs):
        return EnterpriseGraph.create(
            project_id=project_id,
            business_domain=business_domain,
            nodes=self.nodes,
            relationships=self.relationships,
            evidence_count=2,
        )

    def get_node(self, project_id, node_id):
        return next((item for item in self.nodes if item.node_id == node_id), None)

    def get_node_evidence(self, project_id, node_id):
        return (
            EvidenceReference(1, "COLUMN", "invoice_id", 0.95, "ekr_core", "column", 44),
        )


def test_service_returns_stable_graph_dto():
    result = EnterpriseGraphService(repository=FakeRepository()).get_graph(7, "finance")
    assert result.contract_version == "1.0"
    assert result.business_domain == "FINANCE"
    assert result.statistics.node_count == 3
    assert result.nodes[0].canonical_name == "Invoice"


def test_service_filters_neighbours_by_direction():
    service = EnterpriseGraphService(repository=FakeRepository())
    outgoing = service.get_neighbours(7, "FINANCE", 1, direction="OUTGOING")
    incoming = service.get_neighbours(7, "FINANCE", 1, direction="INCOMING")
    assert [node.node_id for node in outgoing.neighbours] == [2]
    assert [node.node_id for node in incoming.neighbours] == [3]


def test_service_maps_evidence():
    evidence = EnterpriseGraphService(repository=FakeRepository()).get_node_evidence(7, 1)
    assert evidence[0].source.schema_name == "ekr_core"
    assert evidence[0].score == 0.95
