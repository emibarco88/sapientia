import json
from sqlalchemy import text
from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_understanding.foundation_models import UnderstandingScope
from sapientia.engines.enterprise_understanding.relationship_models import RelationshipBuildResult
from sapientia.engines.enterprise_understanding.strategies import ForeignKeyRelationshipStrategy,SemanticRelationshipStrategy,KnowledgeRelationshipStrategy,SharedIdentifierRelationshipStrategy
from sapientia.repositories.understanding.understanding_run_repository import UnderstandingRunRepository
from sapientia.repositories.understanding.snapshot_repository import UnderstandingSnapshotRepository
from sapientia.repositories.understanding.enterprise_object_repository import EnterpriseObjectRepository
from sapientia.repositories.understanding.relationship_repository import RelationshipRepository
from sapientia.repositories.understanding.relationship_evidence_repository import RelationshipEvidenceRepository
class RelationshipEngine:
 def __init__(self,database_engine=None,strategies=None):
  self.database_engine=database_engine or get_engine(); self.strategies=list(strategies or [ForeignKeyRelationshipStrategy(),SemanticRelationshipStrategy(),KnowledgeRelationshipStrategy(),SharedIdentifierRelationshipStrategy()])
 def build(self,project_id,dataset_ids=None,scope_type='enterprise',scope_reference=None,model_version='2.0'):
  scope=UnderstandingScope(project_id,scope_type,scope_reference,tuple(dataset_ids or ())); scope.validate()
  with self.database_engine.begin() as c: run=UnderstandingRunRepository(c).create_run(scope,model_version,{'increment':'U2','strategies':[s.name for s in self.strategies]})
  try:
   with self.database_engine.begin() as c:
    rr=UnderstandingRunRepository(c); sr=UnderstandingSnapshotRepository(c); rr.update_stage(run.understanding_run_id,'DISCOVERING_RELATIONSHIPS')
    candidates=[]; counts={}; warnings=[]
    for s in self.strategies:
     try: found=s.discover(c,project_id,dataset_ids); candidates.extend(found); counts[s.name]=len(found)
     except Exception as exc: warnings.append(f'{s.name}: {exc}'); counts[s.name]=0
    rr.update_stage(run.understanding_run_id,'PERSISTING_RELATIONSHIPS'); draft=sr.create_draft(run.understanding_run_id,{'increment':'U2','strategy_counts':counts})
    orepo=EnterpriseObjectRepository(c); rrepo=RelationshipRepository(c); erepo=RelationshipEvidenceRepository(c); object_ids=set(); relationship_ids=set(); evidence_count=0
    for candidate in candidates:
     sid=orepo.upsert(candidate.source); tid=orepo.upsert(candidate.target); object_ids.update((sid,tid)); orepo.add_to_snapshot(draft.understanding_snapshot_id,sid); orepo.add_to_snapshot(draft.understanding_snapshot_id,tid)
     rid=rrepo.upsert(project_id,sid,tid,candidate,run.understanding_run_id); relationship_ids.add(rid); rrepo.add_to_snapshot(draft.understanding_snapshot_id,rid)
     for e in candidate.evidence: erepo.upsert(rid,e); evidence_count+=1
    c.execute(text('''UPDATE ekr_understanding.understanding_snapshot SET object_count=:o,relationship_count=:r,summary_json=summary_json || CAST(:s AS JSONB) WHERE understanding_snapshot_id=:id'''),{'o':len(object_ids),'r':len(relationship_ids),'s':json.dumps({'evidence_count':evidence_count,'warnings':warnings}),'id':draft.understanding_snapshot_id})
    published=sr.publish_snapshot(draft.understanding_snapshot_id); rr.complete_run(run.understanding_run_id,{'snapshot_id':published.understanding_snapshot_id,'strategy_counts':counts,'evidence_count':evidence_count,'warnings':warnings},len(object_ids),len(relationship_ids),len(warnings))
    return RelationshipBuildResult(run.understanding_run_id,published.understanding_snapshot_id,project_id,len(object_ids),len(relationship_ids),evidence_count,counts,tuple(warnings))
  except Exception as exc:
   with self.database_engine.begin() as c: UnderstandingRunRepository(c).fail_run(run.understanding_run_id,str(exc))
   raise
