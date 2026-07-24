from sapientia.intelligence_experience.engines import BusinessHealthEngine, EnterpriseNarrativeEngine


def test_empty_health_is_insufficient_evidence():
    result = BusinessHealthEngine().calculate([])
    assert result["label"] == "INSUFFICIENT_EVIDENCE"
    assert result["score"] is None


def test_narrative_is_deterministic_and_grounded():
    assessment = {
        "assessment_id": 5,
        "assessment_version": 2,
        "assessment_status": "GENERATED",
        "assessment_title": "Finance assessment",
        "generated_at": "2026-07-24T00:00:00+00:00",
        "overall_confidence": 0.9,
    }
    objects = [{
        "intelligence_object_id": 10,
        "assessment_id": 5,
        "object_type": "RISK",
        "object_key": "risk-10",
        "title": "Margin pressure",
        "description": "Gross margin is under pressure.",
        "interpretation": "Cost growth is exceeding revenue growth.",
        "status": "ACTIVE",
        "severity": "HIGH",
        "priority": "HIGH",
        "confidence_score": 0.85,
        "impact_score": 0.8,
        "enterprise_object_id": 12,
    }]
    first = EnterpriseNarrativeEngine().build(1, "FINANCE", assessment, objects)
    second = EnterpriseNarrativeEngine().build(1, "FINANCE", assessment, objects)
    assert first["executive_summary"]["statement_id"] == second["executive_summary"]["statement_id"]
    assert first["sections"]["risks"][0]["title"] == "Margin pressure"
    assert first["provenance"]["generated_by"] == "DETERMINISTIC"
