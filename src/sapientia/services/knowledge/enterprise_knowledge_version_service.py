"""Enterprise Knowledge fingerprinting and version persistence."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text
from sapientia.db.connection import get_engine


class EnterpriseKnowledgeVersionService:
    """Creates immutable domain knowledge versions from material EKR content."""

    def resolve_current(self, project_id: int, business_domain: str) -> dict[str, Any]:
        domain = str(business_domain or "").strip().upper()
        if not domain:
            raise ValueError("A business domain is required.")

        snapshot = self._build_snapshot(project_id, domain)
        engine = get_engine()
        with engine.begin() as connection:
            domain_row = connection.execute(text("""
                SELECT business_domain_id
                FROM ekr_business.business_domain
                WHERE UPPER(domain_code)=UPPER(:domain)
            """), {"domain": domain}).mappings().fetchone()
            if not domain_row:
                raise ValueError(f"Unknown business domain: {domain}")
            domain_id = int(domain_row["business_domain_id"])

            existing = connection.execute(text("""
                SELECT knowledge_version_id, knowledge_version, knowledge_fingerprint,
                       snapshot_json, created_at
                FROM ekr_knowledge.enterprise_knowledge_version
                WHERE project_id=:project_id
                  AND business_domain_id=:domain_id
                  AND knowledge_fingerprint=:fingerprint
                ORDER BY knowledge_version DESC
                LIMIT 1
            """), {"project_id": project_id, "domain_id": domain_id,
                    "fingerprint": snapshot["fingerprint"]}).mappings().fetchone()
            if existing:
                result=dict(existing); result["created"]=False; return result

            next_version = int(connection.execute(text("""
                SELECT COALESCE(MAX(knowledge_version),0)+1
                FROM ekr_knowledge.enterprise_knowledge_version
                WHERE project_id=:project_id AND business_domain_id=:domain_id
            """), {"project_id":project_id,"domain_id":domain_id}).scalar_one())

            row=connection.execute(text("""
                INSERT INTO ekr_knowledge.enterprise_knowledge_version
                (project_id,business_domain_id,knowledge_version,knowledge_fingerprint,
                 snapshot_schema_version,snapshot_json,object_count,relationship_count,
                 dataset_count,column_count,concept_count,version_reason)
                VALUES
                (:project_id,:domain_id,:version,:fingerprint,'1.0',CAST(:snapshot AS JSONB),
                 :object_count,:relationship_count,:dataset_count,:column_count,:concept_count,
                 'MATERIAL_KNOWLEDGE_CHANGE')
                RETURNING knowledge_version_id,knowledge_version,knowledge_fingerprint,
                          snapshot_json,created_at
            """), {
                "project_id":project_id,"domain_id":domain_id,"version":next_version,
                "fingerprint":snapshot["fingerprint"],
                "snapshot":json.dumps(snapshot,sort_keys=True,default=str),
                **snapshot["counts"],
            }).mappings().one()
            result=dict(row); result["created"]=True; return result

    def _build_snapshot(self, project_id: int, domain: str) -> dict[str, Any]:
        engine=get_engine()
        queries={
            "datasets": """
                SELECT d.dataset_id,d.name,d.object_type,d.location,d.row_count,d.column_count
                FROM ekr_core.dataset d
                JOIN ekr_core.source_system s ON s.source_system_id=d.source_system_id
                JOIN ekr_business.business_domain bd ON bd.business_domain_id=d.business_domain_id
                WHERE s.project_id=:project_id AND UPPER(bd.domain_code)=UPPER(:domain)
                ORDER BY d.dataset_id
            """,
            "columns": """
                SELECT c.column_id,c.dataset_id,c.name,c.data_type,c.ordinal_position,
                       c.nullable_flag,c.max_length,c.precision_value,c.scale_value,c.raw_metadata
                FROM ekr_core.column c
                JOIN ekr_core.dataset d ON d.dataset_id=c.dataset_id
                JOIN ekr_core.source_system s ON s.source_system_id=d.source_system_id
                JOIN ekr_business.business_domain bd ON bd.business_domain_id=d.business_domain_id
                WHERE s.project_id=:project_id AND UPPER(bd.domain_code)=UPPER(:domain)
                ORDER BY c.dataset_id,c.ordinal_position,c.column_id
            """,
            "dataset_profiles": """
                SELECT dp.dataset_id,dp.row_count,dp.column_count,dp.duplicate_rows,dp.profile_json
                FROM ekr_profile.dataset_profile dp
                JOIN ekr_core.dataset d ON d.dataset_id=dp.dataset_id
                JOIN ekr_core.source_system s ON s.source_system_id=d.source_system_id
                JOIN ekr_business.business_domain bd ON bd.business_domain_id=d.business_domain_id
                WHERE s.project_id=:project_id AND UPPER(bd.domain_code)=UPPER(:domain)
                ORDER BY dp.dataset_id,dp.dataset_profile_id
            """,
            "column_semantics": """
                SELECT cs.column_id,cs.semantic_type,cs.business_meaning,cs.business_domain,
                       cs.is_pii,cs.sensitivity_level,cs.is_key_candidate,cs.key_type,
                       cs.confidence_score,cs.detection_method,cs.reasoning,cs.semantic_json,cs.reasoning_json
                FROM ekr_semantic.column_semantic cs
                JOIN ekr_core.column c ON c.column_id=cs.column_id
                JOIN ekr_core.dataset d ON d.dataset_id=c.dataset_id
                JOIN ekr_core.source_system s ON s.source_system_id=d.source_system_id
                JOIN ekr_business.business_domain bd ON bd.business_domain_id=d.business_domain_id
                WHERE s.project_id=:project_id AND UPPER(bd.domain_code)=UPPER(:domain)
                ORDER BY cs.column_id,cs.column_semantic_id
            """,
            "enterprise_objects": """
                SELECT enterprise_object_id,object_type_code,source_schema,source_table,
                       source_object_id,canonical_name,canonical_key,description,business_domain,
                       status,metadata_json
                FROM ekr_understanding.enterprise_object
                WHERE project_id=:project_id AND UPPER(COALESCE(business_domain,''))=UPPER(:domain)
                ORDER BY canonical_key,enterprise_object_id
            """,
            "relationships": """
                SELECT r.operational_relationship_id,r.source_enterprise_object_id,
                       r.target_enterprise_object_id,r.relationship_type_code,r.discovery_class,
                       r.generation_method,r.confidence_score,r.status,r.reasoning,r.metadata_json
                FROM ekr_understanding.operational_relationship r
                JOIN ekr_understanding.enterprise_object s
                  ON s.enterprise_object_id=r.source_enterprise_object_id
                WHERE r.project_id=:project_id
                  AND UPPER(COALESCE(s.business_domain,''))=UPPER(:domain)
                ORDER BY r.source_enterprise_object_id,r.target_enterprise_object_id,
                         r.relationship_type_code,r.operational_relationship_id
            """,
            "processes": """
                SELECT business_process_id,process_key,process_name,description,business_domain,
                       process_class,generation_method,confidence_score,status,metadata_json
                FROM ekr_understanding.business_process
                WHERE project_id=:project_id AND UPPER(COALESCE(business_domain,''))=UPPER(:domain)
                ORDER BY process_key,business_process_id
            """,
            "concepts": """
                SELECT enterprise_concept_id,concept_name,concept_type,concept_description,
                       confidence_score,concept_status,concept_json
                FROM ekr_intelligence.enterprise_concept
                WHERE project_id=:project_id AND business_domain_id=(
                    SELECT business_domain_id FROM ekr_business.business_domain
                    WHERE UPPER(domain_code)=UPPER(:domain)
                )
                ORDER BY concept_name,enterprise_concept_id
            """,
        }
        payload={"project_id":project_id,"business_domain":domain,"schema_version":"1.0"}
        with engine.connect() as connection:
            for name,sql in queries.items():
                rows=connection.execute(text(sql),{"project_id":project_id,"domain":domain}).mappings().all()
                payload[name]=[dict(r) for r in rows]
        canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
        fingerprint=hashlib.sha256(canonical.encode()).hexdigest()
        counts={
            "dataset_count":len(payload["datasets"]),
            "column_count":len(payload["columns"]),
            "object_count":len(payload["enterprise_objects"]),
            "relationship_count":len(payload["relationships"]),
            "concept_count":len(payload["concepts"]),
        }
        return {"fingerprint":fingerprint,"counts":counts,"content":payload}
