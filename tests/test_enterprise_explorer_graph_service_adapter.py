from sapientia.graph import BusinessNode, EnterpriseGraph
from sapientia.services.enterprise_explorer_service import EnterpriseExplorerService
from sapientia.services.enterprise_graph import EnterpriseGraphService


class Repository:
    def get_graph(self, project_id, business_domain, **kwargs):
        return EnterpriseGraph.create(
            project_id=project_id,
            business_domain=business_domain,
            nodes=[BusinessNode(1, project_id, "BUSINESS_ENTITY", "Invoice", "invoice", "ACTIVE", business_domain)],
            relationships=[],
        )

    def get_node(self, project_id, node_id):
        return None

    def get_node_evidence(self, project_id, node_id):
        return ()


def test_explorer_uses_enterprise_graph_contract():
    graph_service = EnterpriseGraphService(repository=Repository())
    result = EnterpriseExplorerService(graph_service).get_graph(1, "finance")
    assert result["summary"]["node_count"] == 1
    assert result["nodes"][0]["label"] == "Invoice"
