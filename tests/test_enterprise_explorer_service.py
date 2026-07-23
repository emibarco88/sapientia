from sapientia.services.enterprise_explorer_service import (
    EnterpriseExplorerService,
)


def test_enterprise_explorer_rejects_invalid_project_id():
    service = EnterpriseExplorerService()

    try:
        service.get_graph(
            project_id=0,
            business_domain="FINANCE",
        )
    except ValueError as exc:
        assert "project_id" in str(exc)
    else:
        raise AssertionError(
            "Expected invalid project_id to raise ValueError."
        )


def test_enterprise_explorer_rejects_empty_domain():
    service = EnterpriseExplorerService()

    try:
        service.get_graph(
            project_id=1,
            business_domain=" ",
        )
    except ValueError as exc:
        assert "business domain" in str(exc).lower()
    else:
        raise AssertionError(
            "Expected an empty domain to raise ValueError."
        )
