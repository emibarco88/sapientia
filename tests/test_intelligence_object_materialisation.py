from sapientia.services.intelligence.intelligence_object_service import (
    EnterpriseIntelligenceObjectService,
)


def test_extract_candidates_builds_first_class_objects():
    service = EnterpriseIntelligenceObjectService()
    result = service._extract_candidates({
        "intelligence": {
            "findings": [{"finding_type": "RISK", "title": "Supplier concentration risk"}],
            "recommendations": [{"title": "Diversify suppliers"}],
            "kpis": [{"kpi_name": "Supplier concentration"}],
        },
        "reasoning": {"root_causes": [{"title": "Single-source procurement"}]},
        "report": {},
    })
    assert {item["object_type"] for item in result} == {"RISK", "RECOMMENDATION", "KPI", "ROOT_CAUSE"}
    assert all(item["object_key"] for item in result)
