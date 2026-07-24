from datetime import datetime

from sapientia.models.intelligence import AssessmentStatus, EnterpriseIntelligenceAssessment


def test_assessment_model_supports_versioned_lifecycle():
    assessment = EnterpriseIntelligenceAssessment(
        assessment_id=1,
        project_id=1,
        business_domain_id=2,
        business_domain="FINANCE",
        assessment_version=3,
        assessment_status=AssessmentStatus.GENERATED,
        assessment_title="Finance assessment",
        executive_summary="Margin pressure detected.",
        overall_confidence=0.91,
        assessment_scope="DOMAIN",
        generated_at=datetime(2026, 7, 24),
    )
    assert assessment.assessment_version == 3
    assert assessment.assessment_status is AssessmentStatus.GENERATED
    assert assessment.overall_confidence == 0.91
