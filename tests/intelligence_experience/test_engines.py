from sapientia.intelligence_experience.engines import (
    BusinessHealthEngine,
    EnterpriseNarrativeEngine,
)


def sample_objects():
    return [
        {
            "intelligence_object_id": 1,
            "assessment_id": 10,
            "object_type": "RISK",
            "object_key": "risk-1",
            "title": "Control weakness",
            "description": "A grounded weakness was detected.",
            "confidence_score": 0.9,
            "impact_score": 0.8,
            "status": "active",
        },
        {
            "intelligence_object_id": 2,
            "assessment_id": 10,
            "object_type": "OPPORTUNITY",
            "object_key": "opportunity-1",
            "title": "Improvement opportunity",
            "description": "A grounded opportunity was detected.",
            "confidence_score": 0.8,
            "impact_score": 0.6,
            "status": "active",
        },
    ]


def test_health_is_deterministic():
    engine = BusinessHealthEngine()
    first = engine.calculate(sample_objects())
    second = engine.calculate(sample_objects())
    assert first == second
    assert first["label"] in {
        "HEALTHY",
        "STABLE",
        "NEEDS_ATTENTION",
        "CRITICAL",
    }


def test_narrative_contract():
    assessment = {
        "assessment_id": 10,
        "assessment_version": 1,
        "assessment_status": "completed",
        "assessment_title": "Test",
        "generated_at": "2026-07-24T00:00:00+00:00",
        "overall_confidence": 0.8,
    }
    result = EnterpriseNarrativeEngine().build(
        1,
        "ANY_DOMAIN",
        assessment,
        sample_objects(),
    )
    assert result["experience_version"] == "0.4"
    assert result["business_domain"] == "ANY_DOMAIN"
    assert result["executive_summary"]["evidence"]
    assert result["sections"]["risks"][0]["object_type"] == "RISK"


def test_no_evidence_is_explicit():
    health = BusinessHealthEngine().calculate([])
    assert health["label"] == "INSUFFICIENT_EVIDENCE"
    assert health["score"] is None
