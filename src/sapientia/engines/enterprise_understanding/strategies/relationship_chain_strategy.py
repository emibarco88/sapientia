from __future__ import annotations
import hashlib
from collections import defaultdict
from sqlalchemy import text
from sapientia.engines.enterprise_understanding.behaviour_models import ProcessCandidate, ProcessStepCandidate, ProcessTransitionCandidate

class RelationshipChainStrategy:
    name = "relationship_chain"
    ALLOWED_TYPES = ("precedes", "triggers", "input_to", "output_of", "produces", "consumes", "depends_on", "derived_from")

    def __init__(self, max_depth: int = 6, minimum_steps: int = 3, minimum_confidence: float = 0.55) -> None:
        self.max_depth = max_depth
        self.minimum_steps = minimum_steps
        self.minimum_confidence = minimum_confidence

    def discover(self, connection, project_id: int) -> list[ProcessCandidate]:
        rows = connection.execute(text("""
            SELECT r.operational_relationship_id, r.source_enterprise_object_id, r.target_enterprise_object_id,
                   LOWER(r.relationship_type_code) relationship_type_code, r.confidence_score, r.reasoning,
                   s.canonical_name source_name, s.business_domain source_domain,
                   t.canonical_name target_name, t.business_domain target_domain
            FROM ekr_understanding.operational_relationship r
            JOIN ekr_understanding.enterprise_object s ON s.enterprise_object_id=r.source_enterprise_object_id
            JOIN ekr_understanding.enterprise_object t ON t.enterprise_object_id=r.target_enterprise_object_id
            WHERE r.project_id=:project_id AND r.status='ACTIVE'
              AND LOWER(r.relationship_type_code)=ANY(:types)
              AND r.confidence_score >= :minimum_confidence
            ORDER BY r.confidence_score DESC, r.operational_relationship_id
        """), {"project_id": project_id, "types": list(self.ALLOWED_TYPES), "minimum_confidence": self.minimum_confidence}).mappings().all()
        adjacency: dict[int, list[dict]] = defaultdict(list)
        incoming: dict[int, int] = defaultdict(int)
        names: dict[int, str] = {}
        domains: dict[int, str | None] = {}
        for row in rows:
            d=dict(row); adjacency[int(row["source_enterprise_object_id"])].append(d)
            incoming[int(row["target_enterprise_object_id"])]+=1
            names[int(row["source_enterprise_object_id"])]=str(row["source_name"])
            names[int(row["target_enterprise_object_id"])]=str(row["target_name"])
            domains[int(row["source_enterprise_object_id"])]=row["source_domain"]
            domains[int(row["target_enterprise_object_id"])]=row["target_domain"]
        starts=[node for node in adjacency if incoming[node]==0] or list(adjacency)
        discovered: list[ProcessCandidate]=[]; seen=set()
        def walk(node:int, path_nodes:list[int], path_edges:list[dict]) -> None:
            if len(path_nodes)>=self.max_depth or not adjacency.get(node):
                self._append(path_nodes,path_edges,names,domains,discovered,seen); return
            extended=False
            for edge in adjacency[node]:
                nxt=int(edge["target_enterprise_object_id"])
                if nxt in path_nodes: continue
                extended=True; walk(nxt,path_nodes+[nxt],path_edges+[edge])
            if not extended: self._append(path_nodes,path_edges,names,domains,discovered,seen)
        for start in starts: walk(start,[start],[])
        return discovered

    def _append(self,nodes,edges,names,domains,out,seen):
        if len(nodes)<self.minimum_steps or len(edges)!=len(nodes)-1: return
        signature="->".join(map(str,nodes))
        if signature in seen: return
        seen.add(signature)
        confidence=sum(float(e["confidence_score"]) for e in edges)/len(edges)
        process_key="relationship-chain:"+hashlib.sha256(signature.encode()).hexdigest()[:32]
        process_name=f"{names[nodes[0]]} to {names[nodes[-1]]}"
        domain=next((domains.get(n) for n in nodes if domains.get(n)),None)
        steps=tuple(ProcessStepCandidate(n,names[n],i+1,"TRIGGER" if i==0 else "OUTCOME" if i==len(nodes)-1 else "ACTIVITY",confidence) for i,n in enumerate(nodes))
        transitions=tuple(ProcessTransitionCandidate(int(e["source_enterprise_object_id"]),int(e["target_enterprise_object_id"]),int(e["operational_relationship_id"]),float(e["confidence_score"]),str(e["relationship_type_code"]),e["reasoning"]) for e in edges)
        out.append(ProcessCandidate(process_key,process_name,self.name,confidence,steps,transitions,domain,metadata={"node_ids":nodes,"relationship_ids":[int(e["operational_relationship_id"]) for e in edges]}))
