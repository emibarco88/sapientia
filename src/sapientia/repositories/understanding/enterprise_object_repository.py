import json
from sqlalchemy import text
from sapientia.engines.enterprise_understanding.relationship_models import ObjectReference
class EnterpriseObjectRepository:
 def __init__(self,connection): self.connection=connection
 def upsert(self,obj:ObjectReference)->int:
  return int(self.connection.execute(text('''INSERT INTO ekr_understanding.enterprise_object(project_id,object_type_code,source_schema,source_table,source_object_id,canonical_name,canonical_key,description,business_domain,metadata_json) VALUES(:project_id,:object_type_code,:source_schema,:source_table,:source_object_id,:canonical_name,:canonical_key,:description,:business_domain,CAST(:metadata_json AS JSONB)) ON CONFLICT(project_id,source_schema,source_table,source_object_id) DO UPDATE SET canonical_name=EXCLUDED.canonical_name,canonical_key=EXCLUDED.canonical_key,description=EXCLUDED.description,business_domain=EXCLUDED.business_domain,metadata_json=EXCLUDED.metadata_json,status='ACTIVE',updated_at=NOW() RETURNING enterprise_object_id'''),{**obj.__dict__,'metadata_json':json.dumps(obj.metadata)}).scalar_one())
 def add_to_snapshot(self,snapshot_id:int,object_id:int)->None:
  self.connection.execute(text('''INSERT INTO ekr_understanding.snapshot_object(understanding_snapshot_id,object_type_code,object_id,object_metadata_json) SELECT :snapshot_id,object_type_code,enterprise_object_id,jsonb_build_object('canonical_key',canonical_key) FROM ekr_understanding.enterprise_object WHERE enterprise_object_id=:object_id ON CONFLICT DO NOTHING'''),{'snapshot_id':snapshot_id,'object_id':object_id})
