from sqlalchemy import text
from sapientia.engines.enterprise_understanding.relationship_models import ObjectReference,EvidenceCandidate,RelationshipCandidate
class KnowledgeRelationshipStrategy:
 name='KNOWLEDGE'
 def discover(self,c,project_id,dataset_ids=None):
  rows=c.execute(text('''SELECT kr.knowledge_relationship_id,kr.relationship_type,kr.confidence_score,kr.reasoning,s.knowledge_item_id source_id,s.name source_name,t.knowledge_item_id target_id,t.name target_name FROM ekr_knowledge.knowledge_relationship kr JOIN ekr_knowledge.knowledge_item s ON s.knowledge_item_id=kr.source_knowledge_item_id JOIN ekr_knowledge.knowledge_item t ON t.knowledge_item_id=kr.target_knowledge_item_id WHERE s.project_id=:p AND t.project_id=:p AND s.status='ACTIVE' AND t.status='ACTIVE' '''),{'p':project_id}).mappings().all()
  out=[]
  for r in rows:
   s=ObjectReference(project_id,'KNOWLEDGE_ITEM','ekr_knowledge','knowledge_item',int(r['source_id']),r['source_name'],f"knowledge_item:{r['source_id']}")
   t=ObjectReference(project_id,'KNOWLEDGE_ITEM','ekr_knowledge','knowledge_item',int(r['target_id']),r['target_name'],f"knowledge_item:{r['target_id']}")
   score=float(r['confidence_score'] or .75); rt=self._map(r['relationship_type'])
   e=EvidenceCandidate('KNOWLEDGE_RELATIONSHIP',f"knowledge_relationship:{r['knowledge_relationship_id']}",score,r['reasoning'] or 'Knowledge relationship','ekr_knowledge','knowledge_relationship',int(r['knowledge_relationship_id']),{'source_relationship_type':r['relationship_type']})
   out.append(RelationshipCandidate(s,t,rt,self.name,score,r['reasoning'] or 'Deterministic knowledge relationship',evidence=(e,)))
  return out
 @staticmethod
 def _map(v):
  u=(v or '').upper()
  for token,target in [('DEPEND','DEPENDS_ON'),('DERIV','DERIVED_FROM'),('PRODUC','PRODUCES'),('MEASUR','MEASURED_BY'),('REFER','REFERENCES'),('CONTAIN','CONTAINS')]:
   if token in u:return target
  return 'RELATED_TO'
