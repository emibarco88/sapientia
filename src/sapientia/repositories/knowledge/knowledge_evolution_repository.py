"""Persistence gateway for Enterprise Knowledge evolution."""
from __future__ import annotations
import json
from typing import Any
from sqlalchemy import text

class EnterpriseKnowledgeEvolutionRepository:
    def __init__(self, connection):
        self.connection = connection

    def version(self, knowledge_version_id:int, project_id:int)->dict[str,Any]:
        row=self.connection.execute(text("""
          SELECT kv.*,bd.domain_code,bd.domain_name
          FROM ekr_knowledge.enterprise_knowledge_version kv
          JOIN ekr_business.business_domain bd ON bd.business_domain_id=kv.business_domain_id
          WHERE kv.knowledge_version_id=:id AND kv.project_id=:project_id
        """),{"id":knowledge_version_id,"project_id":project_id}).mappings().fetchone()
        return dict(row) if row else {}

    def previous(self,current_id:int,project_id:int)->dict[str,Any]:
        row=self.connection.execute(text("""
          WITH c AS (
            SELECT project_id,business_domain_id,knowledge_version
            FROM ekr_knowledge.enterprise_knowledge_version
            WHERE knowledge_version_id=:id AND project_id=:project_id
          )
          SELECT kv.* FROM ekr_knowledge.enterprise_knowledge_version kv
          JOIN c ON c.project_id=kv.project_id AND c.business_domain_id=kv.business_domain_id
          WHERE kv.knowledge_version<c.knowledge_version
          ORDER BY kv.knowledge_version DESC LIMIT 1
        """),{"id":current_id,"project_id":project_id}).mappings().fetchone()
        return dict(row) if row else {}

    def existing(self,previous_id:int,current_id:int,project_id:int)->dict[str,Any]:
        cid=self.connection.execute(text("""
          SELECT knowledge_comparison_id
          FROM ekr_knowledge.enterprise_knowledge_version_comparison
          WHERE previous_knowledge_version_id=:p AND current_knowledge_version_id=:c AND project_id=:project_id
        """),{"p":previous_id,"c":current_id,"project_id":project_id}).scalar()
        return self.get(int(cid),project_id) if cid else {}

    def save(self,previous:dict,current:dict,project_id:int,counts:dict,summary:str,changes:list[dict])->dict[str,Any]:
        material=counts['ADDED']+counts['CHANGED']+counts['REMOVED']
        cid=self.connection.execute(text("""
          INSERT INTO ekr_knowledge.enterprise_knowledge_version_comparison(
            project_id,business_domain_id,previous_knowledge_version_id,current_knowledge_version_id,
            previous_version,current_version,added_item_count,changed_item_count,removed_item_count,
            unchanged_item_count,material_change_count,change_summary,comparison_json
          ) VALUES(
            :project_id,:domain_id,:previous_id,:current_id,:previous_version,:current_version,
            :added,:changed,:removed,:unchanged,:material,:summary,CAST(:comparison_json AS JSONB)
          )
          ON CONFLICT(previous_knowledge_version_id,current_knowledge_version_id) DO UPDATE SET
            added_item_count=EXCLUDED.added_item_count,changed_item_count=EXCLUDED.changed_item_count,
            removed_item_count=EXCLUDED.removed_item_count,unchanged_item_count=EXCLUDED.unchanged_item_count,
            material_change_count=EXCLUDED.material_change_count,change_summary=EXCLUDED.change_summary,
            comparison_json=EXCLUDED.comparison_json,created_at=NOW()
          RETURNING knowledge_comparison_id
        """),{
          'project_id':project_id,'domain_id':current['business_domain_id'],
          'previous_id':previous['knowledge_version_id'],'current_id':current['knowledge_version_id'],
          'previous_version':previous['knowledge_version'],'current_version':current['knowledge_version'],
          'added':counts['ADDED'],'changed':counts['CHANGED'],'removed':counts['REMOVED'],
          'unchanged':counts['UNCHANGED'],'material':material,'summary':summary,
          'comparison_json':json.dumps({'counts':counts,'material_change_count':material,'summary':summary})
        }).scalar_one()
        self.connection.execute(text("DELETE FROM ekr_knowledge.enterprise_knowledge_item_change WHERE knowledge_comparison_id=:id"),{'id':cid})
        stmt=text("""
          INSERT INTO ekr_knowledge.enterprise_knowledge_item_change(
            knowledge_comparison_id,item_category,item_key,change_type,item_name,changed_fields,
            change_summary,previous_json,current_json
          ) VALUES(:comparison_id,:item_category,:item_key,:change_type,:item_name,
                   CAST(:changed_fields AS JSONB),:change_summary,CAST(:previous_json AS JSONB),CAST(:current_json AS JSONB))
        """)
        for ch in changes:
            self.connection.execute(stmt,{**ch,'comparison_id':cid,
                'changed_fields':json.dumps(ch.get('changed_fields',[])),
                'previous_json':json.dumps(ch.get('previous'),default=str) if ch.get('previous') is not None else None,
                'current_json':json.dumps(ch.get('current'),default=str) if ch.get('current') is not None else None})
        return self.get(int(cid),project_id)

    def get(self,comparison_id:int,project_id:int)->dict[str,Any]:
        row=self.connection.execute(text("""
          SELECT c.*,bd.domain_code,bd.domain_name
          FROM ekr_knowledge.enterprise_knowledge_version_comparison c
          JOIN ekr_business.business_domain bd ON bd.business_domain_id=c.business_domain_id
          WHERE c.knowledge_comparison_id=:id AND c.project_id=:project_id
        """),{'id':comparison_id,'project_id':project_id}).mappings().fetchone()
        if not row:return {}
        result=dict(row)
        result['changes']=[dict(r) for r in self.connection.execute(text("""
          SELECT * FROM ekr_knowledge.enterprise_knowledge_item_change
          WHERE knowledge_comparison_id=:id
          ORDER BY CASE change_type WHEN 'ADDED' THEN 1 WHEN 'CHANGED' THEN 2 WHEN 'REMOVED' THEN 3 ELSE 4 END,
                   item_category,item_name,item_key
        """),{'id':comparison_id}).mappings().all()]
        return result

    def timeline(self,project_id:int,business_domain:str)->list[dict[str,Any]]:
        rows=self.connection.execute(text("""
          SELECT kv.knowledge_version_id,kv.knowledge_version,kv.knowledge_fingerprint,
                 kv.dataset_count,kv.column_count,kv.object_count,kv.relationship_count,kv.concept_count,
                 kv.version_reason,kv.created_at,bd.domain_code,bd.domain_name,
                 a.assessment_id,a.assessment_version,a.assessment_status,a.generated_at AS assessment_generated_at,
                 c.knowledge_comparison_id,c.added_item_count,c.changed_item_count,c.removed_item_count,
                 c.unchanged_item_count,c.material_change_count,c.change_summary
          FROM ekr_knowledge.enterprise_knowledge_version kv
          JOIN ekr_business.business_domain bd ON bd.business_domain_id=kv.business_domain_id
          LEFT JOIN LATERAL(
            SELECT x.assessment_id,x.assessment_version,x.assessment_status,x.generated_at
            FROM ekr_intelligence.enterprise_intelligence_assessment x
            WHERE x.knowledge_version_id=kv.knowledge_version_id
            ORDER BY x.assessment_version DESC LIMIT 1
          ) a ON TRUE
          LEFT JOIN ekr_knowledge.enterprise_knowledge_version_comparison c
            ON c.current_knowledge_version_id=kv.knowledge_version_id
          WHERE kv.project_id=:project_id AND UPPER(bd.domain_code)=UPPER(:domain)
          ORDER BY kv.knowledge_version DESC
        """),{'project_id':project_id,'domain':business_domain}).mappings().all()
        return [dict(r) for r in rows]

    def status(self,project_id:int,business_domain:str)->dict[str,Any]:
        row=self.connection.execute(text("""
          SELECT bd.business_domain_id,bd.domain_code,bd.domain_name,
                 kv.knowledge_version_id,kv.knowledge_version,kv.created_at AS knowledge_created_at,
                 kv.dataset_count,kv.column_count,kv.object_count,kv.relationship_count,kv.concept_count,
                 a.assessment_id,a.assessment_version,a.knowledge_version_id AS assessed_knowledge_version_id,
                 akv.knowledge_version AS assessed_knowledge_version,a.generated_at AS assessment_generated_at
          FROM ekr_business.business_domain bd
          LEFT JOIN LATERAL(
            SELECT * FROM ekr_knowledge.enterprise_knowledge_version x
            WHERE x.project_id=:project_id AND x.business_domain_id=bd.business_domain_id
            ORDER BY x.knowledge_version DESC LIMIT 1
          ) kv ON TRUE
          LEFT JOIN LATERAL(
            SELECT * FROM ekr_intelligence.enterprise_intelligence_assessment x
            WHERE x.project_id=:project_id AND x.business_domain_id=bd.business_domain_id
            ORDER BY x.assessment_version DESC LIMIT 1
          ) a ON TRUE
          LEFT JOIN ekr_knowledge.enterprise_knowledge_version akv ON akv.knowledge_version_id=a.knowledge_version_id
          WHERE UPPER(bd.domain_code)=UPPER(:domain)
        """),{'project_id':project_id,'domain':business_domain}).mappings().fetchone()
        if not row:return {}
        result=dict(row)
        current=result.get('knowledge_version')
        assessed=result.get('assessed_knowledge_version')
        result['assessment_current']=bool(current is not None and assessed is not None and current==assessed)
        result['knowledge_ahead_of_assessment']=bool(current is not None and (assessed is None or current>assessed))
        return result
