from sapientia.engines.enterprise_understanding.behaviour_models import ProcessStepCandidate, ProcessTransitionCandidate, ProcessCandidate
def test_process_candidate_is_constructible():
    steps=(ProcessStepCandidate(1,'Order',1,'TRIGGER',.9),ProcessStepCandidate(2,'Invoice',2,'OUTCOME',.9))
    transitions=(ProcessTransitionCandidate(1,2,10,.9,'produces'),)
    p=ProcessCandidate('k','Order to Invoice','test',.9,steps,transitions)
    assert p.steps[1].step_number==2
