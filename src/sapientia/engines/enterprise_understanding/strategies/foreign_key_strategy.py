from sqlalchemy import text
from sapientia.engines.enterprise_understanding.relationship_models import ObjectReference,EvidenceCandidate,RelationshipCandidate
class ForeignKeyRelationshipStrategy:
 name='FOREIGN_KEY'
 def discover(self,c,project_id,dataset_ids=None):
  rows=c.execute(text('''SELECT dr.dataset_relationship_id,dr.parent_dataset_id,dr.child_dataset_id,dr.relationship_type,dr.parent_key,dr.child_key,pd.name parent_name,cd.name child_name FROM ekr_core.dataset_relationship dr JOIN ekr_core.dataset pd ON pd.dataset_id=dr.parent_dataset_id JOIN ekr_core.dataset cd ON cd.dataset_id=dr.child_dataset_id JOIN ekr_core.source_system ss ON ss.source_system_id=pd.source_system_id WHERE ss.project_id=:p AND (:f=FALSE OR dr.parent_dataset_id=ANY(:ids) OR dr.child_dataset_id=ANY(:ids))'''),{'p':project_id,'f':bool(dataset_ids),'ids':dataset_ids or [0]}).mappings().all()
  out=[]
  for r in rows:
   s=ObjectReference(project_id,'DATASET','ekr_core','dataset',int(r['child_dataset_id']),r['child_name'],f"dataset:{r['child_dataset_id']}")
   t=ObjectReference(project_id,'DATASET','ekr_core','dataset',int(r['parent_dataset_id']),r['parent_name'],f"dataset:{r['parent_dataset_id']}")
   e=EvidenceCandidate('FOREIGN_KEY',f"dataset_relationship:{r['dataset_relationship_id']}",1.0,'Persisted dataset relationship','ekr_core','dataset_relationship',int(r['dataset_relationship_id']),{'parent_key':r['parent_key'],'child_key':r['child_key'],'source_type':r['relationship_type']})
   out.append(RelationshipCandidate(s,t,'REFERENCES',self.name,1.0,'Child dataset references parent dataset',evidence=(e,)))
  return out
