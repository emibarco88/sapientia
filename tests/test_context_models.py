from sapientia.engines.enterprise_understanding.context_models import ContextBuildResult
def test_context_result_serialises():
    assert ContextBuildResult(1,2,3,4).to_dict()['facts_registered']==4
