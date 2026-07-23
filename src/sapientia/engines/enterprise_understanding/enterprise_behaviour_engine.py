from __future__ import annotations
import json
from sqlalchemy import text
from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_understanding.foundation_models import UnderstandingScope
from sapientia.engines.enterprise_understanding.behaviour_models import BehaviourBuildResult
from sapientia.engines.enterprise_understanding.strategies.relationship_chain_strategy import RelationshipChainStrategy
from sapientia.repositories.understanding.understanding_run_repository import UnderstandingRunRepository
from sapientia.repositories.understanding.snapshot_repository import UnderstandingSnapshotRepository
from sapientia.repositories.understanding.process_repository import ProcessRepository

class EnterpriseBehaviourEngine:
    def __init__(self,database_engine=None,strategies=None):
        self.database_engine=database_engine or get_engine(); self.strategies=list(strategies or [RelationshipChainStrategy()])
    def build(self,project_id:int,scope_type:str="enterprise",scope_reference:str|None=None,model_version:str="3.0"):
        scope=UnderstandingScope(project_id,scope_type,scope_reference,()); scope.validate()
        with self.database_engine.begin() as c: run=UnderstandingRunRepository(c).create_run(scope,model_version,{"increment":"U3","strategies":[s.name for s in self.strategies]})
        try:
            with self.database_engine.begin() as c:
                rr=UnderstandingRunRepository(c); sr=UnderstandingSnapshotRepository(c); rr.update_stage(run.understanding_run_id,"DISCOVERING_BEHAVIOUR")
                candidates=[]; warnings=[]
                for strategy in self.strategies:
                    try: candidates.extend(strategy.discover(c,project_id))
                    except Exception as exc: warnings.append(f"{strategy.name}: {exc}")
                rr.update_stage(run.understanding_run_id,"PERSISTING_PROCESSES")
                draft=sr.create_draft(run.understanding_run_id,{"increment":"U3","process_candidates":len(candidates)})
                repo=ProcessRepository(c); process_count=step_count=transition_count=0
                for candidate in candidates:
                    pid=repo.upsert_process(project_id,candidate,run.understanding_run_id)
                    steps,transitions=repo.replace_structure(pid,candidate); repo.add_to_snapshot(draft.understanding_snapshot_id,pid,{"confidence_score":candidate.confidence_score})
                    process_count+=1; step_count+=steps; transition_count+=transitions
                c.execute(text("UPDATE ekr_understanding.understanding_snapshot SET summary_json=summary_json || CAST(:s AS JSONB) WHERE understanding_snapshot_id=:id"),{"s":json.dumps({"process_count":process_count,"process_step_count":step_count,"process_transition_count":transition_count,"warnings":warnings}),"id":draft.understanding_snapshot_id})
                published=sr.publish_snapshot(draft.understanding_snapshot_id)
                rr.complete_run(run.understanding_run_id,{"snapshot_id":published.understanding_snapshot_id,"process_count":process_count,"step_count":step_count,"transition_count":transition_count,"warnings":warnings},0,transition_count,len(warnings))
                return BehaviourBuildResult(run.understanding_run_id,published.understanding_snapshot_id,project_id,process_count,step_count,transition_count,tuple(warnings))
        except Exception as exc:
            with self.database_engine.begin() as c: UnderstandingRunRepository(c).fail_run(run.understanding_run_id,str(exc))
            raise
