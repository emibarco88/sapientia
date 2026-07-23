from api.routers.enterprise_graph import router


def test_navigation_routes_are_versioned():
    paths = {route.path for route in router.routes}
    assert "/enterprise-graph/v1/{project_id}/{business_domain}/nodes/{node_id}/traversal" in paths
    assert "/enterprise-graph/v1/{project_id}/{business_domain}/path" in paths
