from sapientia.services.intelligence.assessment_evolution_service import EnterpriseIntelligenceEvolutionService
def test_new_change():
 s=EnterpriseIntelligenceEvolutionService()
 c=s._change(None,{"intelligence_object_id":2,"object_type":"RISK","object_key":"r1","title":"Risk","confidence_score":.8})
 assert c["change_type"]=="NEW"
def test_changed():
 s=EnterpriseIntelligenceEvolutionService()
 a={"intelligence_object_id":1,"object_type":"RISK","object_key":"r1","title":"Risk","severity":"HIGH","confidence_score":.6}
 b={**a,"intelligence_object_id":2,"severity":"LOW","confidence_score":.9}
 c=s._change(a,b)
 assert c["change_type"]=="CHANGED" and "severity" in c["changed_fields"]
