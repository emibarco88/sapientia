from sapientia.engines.enterprise_reasoning.enterprise_reasoning_engine import EnterpriseReasoningEngine
from sapientia.engines.enterprise_reasoning.models import DependencyEdge

def test_downstream_paths_are_cycle_safe():
    edges=[DependencyEdge(1,2,10,'FEEDS',.9),DependencyEdge(2,3,11,'FEEDS',.8),DependencyEdge(3,1,12,'FEEDS',.7)]
    paths=EnterpriseReasoningEngine._paths(1,edges,'DOWNSTREAM',6)
    assert [p.object_ids for p in paths] == [(1,2),(1,2,3)]
    assert paths[-1].confidence == .72

def test_critical_nodes_use_connectivity():
    edges=[DependencyEdge(1,2,1,'X',.9),DependencyEdge(1,3,2,'X',.9),DependencyEdge(4,1,3,'X',.9)]
    assert 1 in EnterpriseReasoningEngine._critical_nodes(edges)
