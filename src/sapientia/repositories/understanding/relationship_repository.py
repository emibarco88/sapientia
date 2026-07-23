import json
from sqlalchemy import text
class RelationshipRepository:
 def __init__(self,connection): self.connection=connection
 def upsert(self,project_id,source_id,target_id,candidate,run_id)->int:
  return int(self.connection.execute(text('''INSERT INTO ekr_understanding.operational_relationship(project_id,source_enterprise_object_id,target_enterprise_object_id,relationship_type_code,discovery_class,generation_method,confidence_score,reasoning,metadata_json,first_discovered_run_id,last_confirmed_run_id) VALUES(:p,:s,:t,:rt,:dc,:gm,:cs,:r,CAST(:m AS JSONB),:run,:run) ON CONFLICT(project_id,source_enterprise_object_id,target_enterprise_object_id,relationship_type_code) DO UPDATE SET confidence_score=GREATEST(ekr_understanding.operational_relationship.confidence_score,EXCLUDED.confidence_score),generation_method=EXCLUDED.generation_method,reasoning=EXCLUDED.reasoning,metadata_json=EXCLUDED.metadata_json,last_confirmed_run_id=EXCLUDED.last_confirmed_run_id,status='ACTIVE',updated_at=NOW() RETURNING operational_relationship_id'''),{'p':project_id,'s':source_id,'t':target_id,'rt':candidate.relationship_type_code,'dc':candidate.discovery_class,'gm':candidate.generation_method,'cs':max(0,min(1,candidate.confidence_score)),'r':candidate.reasoning,'m':json.dumps(candidate.metadata),'run':run_id}).scalar_one())
 def add_to_snapshot(self,snapshot_id,relationship_id):
  self.connection.execute(text('INSERT INTO ekr_understanding.snapshot_relationship(understanding_snapshot_id,operational_relationship_id) VALUES(:s,:r) ON CONFLICT DO NOTHING'),{'s':snapshot_id,'r':relationship_id})
