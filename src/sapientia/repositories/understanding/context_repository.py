from __future__ import annotations
import json
from sqlalchemy import text
class ContextRepository:
    def __init__(self,connection): self.connection=connection
    def replace_context(self,project_id:int,snapshot_id:int,object_id:int,summary:str,confidence:float,counts:dict,context:dict)->int:
        version=int(self.connection.execute(text("SELECT COALESCE(MAX(context_version),0)+1 FROM ekr_understanding.object_context WHERE enterprise_object_id=:o"),{"o":object_id}).scalar_one())
        self.connection.execute(text("UPDATE ekr_understanding.object_context SET context_status='RETIRED' WHERE enterprise_object_id=:o AND context_status='PUBLISHED'"),{"o":object_id})
        return int(self.connection.execute(text("""INSERT INTO ekr_understanding.object_context(project_id,enterprise_object_id,understanding_snapshot_id,context_version,context_status,confidence_score,relationship_count,process_count,evidence_count,upstream_count,downstream_count,summary_text,context_json,published_at) VALUES(:p,:o,:s,:v,'PUBLISHED',:c,:r,:pr,:e,:u,:d,:summary,CAST(:j AS JSONB),NOW()) RETURNING object_context_id"""),{"p":project_id,"o":object_id,"s":snapshot_id,"v":version,"c":confidence,"r":counts["relationship_count"],"pr":counts["process_count"],"e":counts["evidence_count"],"u":counts["upstream_count"],"d":counts["downstream_count"],"summary":summary,"j":json.dumps(context)}).scalar_one())
    def add_fact(self,context_id:int,fact_type:str,fact_key:str,value:str|None,confidence:float,evidence_count:int=0,related_object_id:int|None=None,related_process_id:int|None=None,fact:dict|None=None)->None:
        self.connection.execute(text("""INSERT INTO ekr_understanding.object_context_fact(object_context_id,fact_type,fact_key,fact_value_text,related_enterprise_object_id,related_business_process_id,confidence_score,evidence_count,fact_json) VALUES(:c,:t,:k,:v,:o,:p,:score,:e,CAST(:j AS JSONB)) ON CONFLICT(object_context_id,fact_type,fact_key) DO UPDATE SET fact_value_text=EXCLUDED.fact_value_text,confidence_score=EXCLUDED.confidence_score,evidence_count=EXCLUDED.evidence_count,fact_json=EXCLUDED.fact_json"""),{"c":context_id,"t":fact_type,"k":fact_key,"v":value,"o":related_object_id,"p":related_process_id,"score":confidence,"e":evidence_count,"j":json.dumps(fact or {})})
    def get_latest(self,object_id:int):
        row=self.connection.execute(text("SELECT * FROM ekr_understanding.object_context WHERE enterprise_object_id=:o AND context_status='PUBLISHED' ORDER BY context_version DESC LIMIT 1"),{"o":object_id}).mappings().one_or_none()
        return dict(row) if row else None
