from sapientia.engines.enterprise_intelligence_v2.enterprise_intelligence_engine import EnterpriseIntelligenceEngine
from sapientia.engines.enterprise_intelligence_v2.question_answering_engine import EnterpriseQuestionAnsweringEngine

def test_findings_include_critical_dependency_and_evidence_gap():
    context={"objects":[{"enterprise_object_id":1,"canonical_name":"Revenue"},{"enterprise_object_id":2,"canonical_name":"Invoice"},{"enterprise_object_id":3,"canonical_name":"Order"},{"enterprise_object_id":4,"canonical_name":"Payment"}],
             "edges":[{"source_enterprise_object_id":2,"target_enterprise_object_id":1,"evidence_count":0},{"source_enterprise_object_id":3,"target_enterprise_object_id":1,"evidence_count":0},{"source_enterprise_object_id":4,"target_enterprise_object_id":1,"evidence_count":0}],"impacts":[],"root_causes":[]}
    findings,recommendations=EnterpriseIntelligenceEngine._derive(context)
    assert any(f["finding_type"]=="CRITICAL_DEPENDENCY" for f in findings)
    assert any(f["finding_type"]=="EVIDENCE_GAP" for f in findings)
    assert recommendations

def test_question_classifier():
    assert EnterpriseQuestionAnsweringEngine.classify('What would be impacted?') == 'IMPACT'
    assert EnterpriseQuestionAnsweringEngine.classify('Why did margin decrease?') == 'ROOT_CAUSE'
