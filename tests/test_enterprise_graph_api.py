from api.routers.enterprise_graph import router


def test_enterprise_graph_router_exposes_versioned_routes():
    paths = {route.path for route in router.routes}
    assert "/enterprise-graph/v1/{project_id}/{business_domain}" in paths
    assert "/enterprise-graph/v1/{project_id}/nodes/{node_id}" in paths
    assert "/enterprise-graph/v1/{project_id}/{business_domain}/nodes/{node_id}/neighbours" in paths
    assert "/enterprise-graph/v1/{project_id}/nodes/{node_id}/evidence" in paths
    assert "/enterprise-graph/v1/{project_id}/{business_domain}/statistics" in paths
