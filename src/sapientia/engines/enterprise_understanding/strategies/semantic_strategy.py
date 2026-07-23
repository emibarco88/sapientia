from sqlalchemy import text
from sapientia.engines.enterprise_understanding.relationship_models import ObjectReference,EvidenceCandidate,RelationshipCandidate
class SemanticRelationshipStrategy:
 name='SEMANTIC'
 def discover(self,c,project_id,dataset_ids=None):
  rows=c.execute(text('''SELECT cs.column_semantic_id,c.column_id,c.name column_name,c.dataset_id,d.name dataset_name,cs.semantic_type,cs.business_meaning,cs.business_domain,cs.confidence_score FROM ekr_semantic.column_semantic cs JOIN ekr_core."column" c ON c.column_id=cs.column_id JOIN ekr_core.dataset d ON d.dataset_id=c.dataset_id JOIN ekr_core.source_system ss ON ss.source_system_id=d.source_system_id WHERE ss.project_id=:p AND cs.semantic_type IS NOT NULL AND (:f=FALSE OR d.dataset_id=ANY(:ids))'''),{'p':project_id,'f':bool(dataset_ids),'ids':dataset_ids or [0]}).mappings().all()
  out=[]
  for r in rows:
   s=ObjectReference(project_id,'DATASET','ekr_core','dataset',int(r['dataset_id']),r['dataset_name'],f"dataset:{r['dataset_id']}")
   t=ObjectReference(project_id,'COLUMN','ekr_core','column',int(r['column_id']),r['column_name'],f"column:{r['column_id']}",r['business_meaning'],r['business_domain'],{'dataset_id':int(r['dataset_id'])})
   score=float(r['confidence_score'] or .75)
   e=EvidenceCandidate('SEMANTIC_CLASSIFICATION',f"column_semantic:{r['column_semantic_id']}",score,'Column semantic classification','ekr_semantic','column_semantic',int(r['column_semantic_id']),{'semantic_type':r['semantic_type']})
   out.append(RelationshipCandidate(s,t,'CONTAINS',self.name,score,'Dataset contains a semantically classified column',evidence=(e,)))
  return out
