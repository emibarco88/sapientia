from collections import defaultdict
from sqlalchemy import text
from sapientia.engines.enterprise_understanding.relationship_models import ObjectReference,EvidenceCandidate,RelationshipCandidate
class SharedIdentifierRelationshipStrategy:
 name='SHARED_IDENTIFIER'
 def discover(self,c,project_id,dataset_ids=None):
  rows=c.execute(text('''SELECT c.column_id,c.dataset_id,c.name column_name,d.name dataset_name,cs.confidence_score FROM ekr_core."column" c JOIN ekr_core.dataset d ON d.dataset_id=c.dataset_id JOIN ekr_core.source_system ss ON ss.source_system_id=d.source_system_id LEFT JOIN ekr_semantic.column_semantic cs ON cs.column_id=c.column_id WHERE ss.project_id=:p AND (lower(c.name) LIKE '%_id' OR COALESCE(cs.is_key_candidate,FALSE)=TRUE) AND (:f=FALSE OR d.dataset_id=ANY(:ids))'''),{'p':project_id,'f':bool(dataset_ids),'ids':dataset_ids or [0]}).mappings().all()
  groups=defaultdict(list)
  for r in rows:groups[r['column_name'].lower()].append(r)
  out=[]
  for key,items in groups.items():
   for i in range(len(items)):
    for j in range(i+1,len(items)):
     a,b=items[i],items[j]
     if a['dataset_id']==b['dataset_id']:continue
     s=ObjectReference(project_id,'DATASET','ekr_core','dataset',int(a['dataset_id']),a['dataset_name'],f"dataset:{a['dataset_id']}")
     t=ObjectReference(project_id,'DATASET','ekr_core','dataset',int(b['dataset_id']),b['dataset_name'],f"dataset:{b['dataset_id']}")
     score=min(float(a['confidence_score'] or .7),float(b['confidence_score'] or .7),.85)
     e=EvidenceCandidate('SHARED_IDENTIFIER',f"shared_identifier:{key}:{min(a['column_id'],b['column_id'])}:{max(a['column_id'],b['column_id'])}",score,f'Datasets share identifier {key}',evidence={'identifier':key,'column_ids':[int(a['column_id']),int(b['column_id'])]})
     out.append(RelationshipCandidate(s,t,'RELATED_TO',self.name,score,f'Datasets share identifier {key}','INFERRED',evidence=(e,)))
  return out
