from __future__ import annotations
import json
from sqlalchemy import text
from sapientia.engines.enterprise_understanding.behaviour_models import ProcessCandidate

class ProcessRepository:
    def __init__(self, connection): self.connection=connection
    def upsert_process(self, project_id:int, candidate:ProcessCandidate, run_id:int)->int:
        row=self.connection.execute(text("""
            INSERT INTO ekr_understanding.business_process(project_id,process_key,process_name,description,business_domain,process_class,generation_method,confidence_score,first_discovered_run_id,last_confirmed_run_id,metadata_json)
            VALUES(:project_id,:process_key,:process_name,:description,:business_domain,'DISCOVERED',:generation_method,:confidence_score,:run_id,:run_id,CAST(:metadata AS JSONB))
            ON CONFLICT(project_id,process_key) DO UPDATE SET process_name=EXCLUDED.process_name,description=EXCLUDED.description,business_domain=EXCLUDED.business_domain,generation_method=EXCLUDED.generation_method,confidence_score=EXCLUDED.confidence_score,last_confirmed_run_id=EXCLUDED.last_confirmed_run_id,metadata_json=EXCLUDED.metadata_json,status='ACTIVE',updated_at=NOW()
            RETURNING business_process_id
        """),{"project_id":project_id,"process_key":candidate.process_key,"process_name":candidate.process_name,"description":candidate.description,"business_domain":candidate.business_domain,"generation_method":candidate.generation_method,"confidence_score":candidate.confidence_score,"run_id":run_id,"metadata":json.dumps(candidate.metadata)}).scalar_one()
        return int(row)
    def replace_structure(self, process_id:int, candidate:ProcessCandidate)->tuple[int,int]:
        self.connection.execute(text("DELETE FROM ekr_understanding.process_transition WHERE business_process_id=:id"),{"id":process_id})
        self.connection.execute(text("DELETE FROM ekr_understanding.process_step WHERE business_process_id=:id"),{"id":process_id})
        step_ids={}
        for step in candidate.steps:
            sid=self.connection.execute(text("""INSERT INTO ekr_understanding.process_step(business_process_id,enterprise_object_id,step_number,step_role,step_name,confidence_score,metadata_json) VALUES(:p,:o,:n,:r,:name,:c,CAST(:m AS JSONB)) RETURNING process_step_id"""),{"p":process_id,"o":step.enterprise_object_id,"n":step.step_number,"r":step.step_role,"name":step.canonical_name,"c":step.confidence_score,"m":json.dumps(step.metadata)}).scalar_one()
            step_ids[step.enterprise_object_id]=int(sid)
        for tr in candidate.transitions:
            self.connection.execute(text("""INSERT INTO ekr_understanding.process_transition(business_process_id,source_process_step_id,target_process_step_id,operational_relationship_id,confidence_score,reasoning,metadata_json) VALUES(:p,:s,:t,:r,:c,:reasoning,CAST(:m AS JSONB))"""),{"p":process_id,"s":step_ids[tr.source_enterprise_object_id],"t":step_ids[tr.target_enterprise_object_id],"r":tr.operational_relationship_id,"c":tr.confidence_score,"reasoning":tr.reasoning,"m":json.dumps({"relationship_type_code":tr.relationship_type_code})})
        return len(candidate.steps),len(candidate.transitions)
    def add_to_snapshot(self,snapshot_id:int,process_id:int,metadata:dict|None=None)->None:
        self.connection.execute(text("""INSERT INTO ekr_understanding.snapshot_process(understanding_snapshot_id,business_process_id,process_metadata_json) VALUES(:s,:p,CAST(:m AS JSONB)) ON CONFLICT(understanding_snapshot_id,business_process_id) DO UPDATE SET process_metadata_json=EXCLUDED.process_metadata_json"""),{"s":snapshot_id,"p":process_id,"m":json.dumps(metadata or {})})
