from __future__ import annotations
from sqlalchemy import text
from sapientia.db.connection import get_engine
from sapientia.engines.enterprise_understanding.context_models import ContextBuildResult
from sapientia.repositories.understanding.context_repository import ContextRepository

class EnterpriseContextEngine:
    def __init__(self,database_engine=None): self.database_engine=database_engine or get_engine()
    def build(self,project_id:int,understanding_snapshot_id:int|None=None)->ContextBuildResult:
        warnings=[]; contexts=facts=0
        with self.database_engine.begin() as c:
            if understanding_snapshot_id is None:
                understanding_snapshot_id=c.execute(text("SELECT understanding_snapshot_id FROM ekr_understanding.understanding_snapshot WHERE project_id=:p AND snapshot_status='PUBLISHED' ORDER BY snapshot_version DESC LIMIT 1"),{"p":project_id}).scalar_one_or_none()
            if understanding_snapshot_id is None: raise ValueError(f"No published understanding snapshot found for project {project_id}.")
            objects=c.execute(text("SELECT * FROM ekr_understanding.enterprise_object WHERE project_id=:p AND status='ACTIVE' ORDER BY enterprise_object_id"),{"p":project_id}).mappings().all()
            repo=ContextRepository(c)
            for obj in objects:
                oid=int(obj["enterprise_object_id"])
                rels=c.execute(text("""SELECT r.*, s.canonical_name source_name, t.canonical_name target_name,
                    (SELECT COUNT(*) FROM ekr_understanding.relationship_evidence e WHERE e.operational_relationship_id=r.operational_relationship_id) evidence_count
                    FROM ekr_understanding.operational_relationship r
                    JOIN ekr_understanding.enterprise_object s ON s.enterprise_object_id=r.source_enterprise_object_id
                    JOIN ekr_understanding.enterprise_object t ON t.enterprise_object_id=r.target_enterprise_object_id
                    WHERE r.project_id=:p AND r.status='ACTIVE' AND (r.source_enterprise_object_id=:o OR r.target_enterprise_object_id=:o)"""),{"p":project_id,"o":oid}).mappings().all()
                processes=c.execute(text("""SELECT DISTINCT bp.business_process_id,bp.process_name,bp.confidence_score,ps.step_number,ps.step_role
                    FROM ekr_understanding.process_step ps JOIN ekr_understanding.business_process bp ON bp.business_process_id=ps.business_process_id
                    WHERE ps.enterprise_object_id=:o AND bp.status='ACTIVE'"""),{"o":oid}).mappings().all()
                upstream=[r for r in rels if int(r["target_enterprise_object_id"])==oid]
                downstream=[r for r in rels if int(r["source_enterprise_object_id"])==oid]
                evidence_count=sum(int(r["evidence_count"] or 0) for r in rels)
                confidence_values=[float(r["confidence_score"]) for r in rels]+[float(p["confidence_score"]) for p in processes]
                confidence=sum(confidence_values)/len(confidence_values) if confidence_values else 0.0
                counts={"relationship_count":len(rels),"process_count":len(processes),"evidence_count":evidence_count,"upstream_count":len(upstream),"downstream_count":len(downstream)}
                summary=f"{obj['canonical_name']} participates in {len(processes)} process(es), has {len(upstream)} upstream and {len(downstream)} downstream relationship(s), supported by {evidence_count} evidence record(s)."
                context={"object":{"id":oid,"name":obj["canonical_name"],"type":obj["object_type_code"],"business_domain":obj["business_domain"],"description":obj["description"]},"counts":counts,"upstream":[dict(r) for r in upstream],"downstream":[dict(r) for r in downstream],"processes":[dict(p) for p in processes]}
                context_id=repo.replace_context(project_id,int(understanding_snapshot_id),oid,summary,confidence,counts,context); contexts+=1
                for r in upstream:
                    repo.add_fact(context_id,"UPSTREAM_RELATIONSHIP",f"relationship:{r['operational_relationship_id']}",str(r["source_name"]),float(r["confidence_score"]),int(r["evidence_count"] or 0),int(r["source_enterprise_object_id"]),fact={"relationship_type_code":r["relationship_type_code"]}); facts+=1
                for r in downstream:
                    repo.add_fact(context_id,"DOWNSTREAM_RELATIONSHIP",f"relationship:{r['operational_relationship_id']}",str(r["target_name"]),float(r["confidence_score"]),int(r["evidence_count"] or 0),int(r["target_enterprise_object_id"]),fact={"relationship_type_code":r["relationship_type_code"]}); facts+=1
                for p in processes:
                    repo.add_fact(context_id,"PROCESS_MEMBERSHIP",f"process:{p['business_process_id']}",str(p["process_name"]),float(p["confidence_score"]),0,related_process_id=int(p["business_process_id"]),fact={"step_number":int(p["step_number"]),"step_role":p["step_role"]}); facts+=1
        return ContextBuildResult(project_id,int(understanding_snapshot_id),contexts,facts,tuple(warnings))
