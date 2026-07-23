import json
from sqlalchemy import text
class RelationshipEvidenceRepository:
 def __init__(self,connection): self.connection=connection
 def upsert(self,relationship_id,e)->int:
  return int(self.connection.execute(text('''INSERT INTO ekr_understanding.relationship_evidence(operational_relationship_id,evidence_type,source_schema,source_table,source_record_id,evidence_key,evidence_score,reasoning,evidence_json) VALUES(:r,:t,:ss,:st,:sid,:k,:sc,:rea,CAST(:j AS JSONB)) ON CONFLICT(operational_relationship_id,evidence_key) DO UPDATE SET evidence_score=EXCLUDED.evidence_score,reasoning=EXCLUDED.reasoning,evidence_json=EXCLUDED.evidence_json RETURNING relationship_evidence_id'''),{'r':relationship_id,'t':e.evidence_type,'ss':e.source_schema,'st':e.source_table,'sid':e.source_record_id,'k':e.evidence_key,'sc':max(0,min(1,e.evidence_score)),'rea':e.reasoning,'j':json.dumps(e.evidence)}).scalar_one())
