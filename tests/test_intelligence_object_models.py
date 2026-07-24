from sapientia.models.intelligence.objects import (
    EnterpriseIntelligenceObject,
    IntelligenceEvidenceReference,
    IntelligenceObjectType,
)


def test_structured_intelligence_object_supports_evidence():
    item = EnterpriseIntelligenceObject(
        object_type=IntelligenceObjectType.RISK,
        object_key="RISK:margin",
        title="Margin risk",
        confidence_score=0.91,
        evidence=(IntelligenceEvidenceReference(evidence_type="DATASET"),),
    )
    assert item.object_type is IntelligenceObjectType.RISK
    assert item.evidence[0].evidence_type == "DATASET"
