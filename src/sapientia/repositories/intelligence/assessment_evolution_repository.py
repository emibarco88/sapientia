
"""Persistence for Enterprise Intelligence assessment evolution."""
from __future__ import annotations
import json
from typing import Any
from sqlalchemy import text

class EnterpriseIntelligenceEvolutionRepository:
    def __init__(self, connection):
        self.connection = connection

    def assessment(self, assessment_id:int, project_id:int)->dict[str,Any]:
        row=self.connection.execute(text("""
          SELECT a.*,bd.domain_code,bd.domain_name
          FROM ekr_intelligence.enterprise_intelligence_assessment a
          JOIN ekr_business.business_domain bd ON bd.business_domain_id=a.business_domain_id
          WHERE a.assessment_id=:assessment_id AND a.project_id=:project_id
        """),{"assessment_id":assessment_id,"project_id":project_id}).mappings().fetchone()
        return dict(row) if row else {}

    def previous(self,current_assessment_id:int,project_id:int)->dict[str,Any]:
        row=self.connection.execute(text("""
          WITH c AS (
            SELECT project_id,business_domain_id,assessment_version
            FROM ekr_intelligence.enterprise_intelligence_assessment
            WHERE assessment_id=:assessment_id AND project_id=:project_id
          )
          SELECT a.* FROM ekr_intelligence.enterprise_intelligence_assessment a
          JOIN c ON c.project_id=a.project_id AND c.business_domain_id=a.business_domain_id
          WHERE a.assessment_version<c.assessment_version
          ORDER BY a.assessment_version DESC LIMIT 1
        """),{"assessment_id":current_assessment_id,"project_id":project_id}).mappings().fetchone()
        return dict(row) if row else {}

    def objects(self,assessment_id:int)->list[dict[str,Any]]:
        rows=self.connection.execute(text("""
          SELECT intelligence_object_id,object_type,object_key,title,description,interpretation,
                 status,category,severity,priority,confidence_score,probability_score,impact_score,
                 estimated_value,estimated_value_currency,enterprise_object_id,source_object_type,
                 source_object_id,source_schema,source_table,source_record_id
          FROM ekr_intelligence.enterprise_intelligence_object
          WHERE assessment_id=:assessment_id ORDER BY object_type,object_key
        """),{"assessment_id":assessment_id}).mappings().all()
        return [dict(r) for r in rows]

    def existing(self,previous_id:int,current_id:int,project_id:int)->dict[str,Any]:
        cid=self.connection.execute(text("""
          SELECT assessment_comparison_id FROM ekr_intelligence.enterprise_intelligence_assessment_comparison
          WHERE previous_assessment_id=:p AND current_assessment_id=:c AND project_id=:project_id
        """),{"p":previous_id,"c":current_id,"project_id":project_id}).scalar()
        return self.get(int(cid),project_id) if cid else {}

    def save(self,previous:dict,current:dict,project_id:int,counts:dict,confidence_delta,changes:list)->dict:
        cid=self.connection.execute(text("""
          INSERT INTO ekr_intelligence.enterprise_intelligence_assessment_comparison(
            project_id,business_domain_id,previous_assessment_id,current_assessment_id,
            previous_version,current_version,new_object_count,changed_object_count,
            resolved_object_count,unchanged_object_count,confidence_delta,comparison_json
          ) VALUES(
            :project_id,:domain_id,:previous_id,:current_id,:previous_version,:current_version,
            :new_count,:changed_count,:resolved_count,:unchanged_count,:confidence_delta,
            CAST(:comparison_json AS JSONB)
          )
          ON CONFLICT(previous_assessment_id,current_assessment_id) DO UPDATE SET
            new_object_count=EXCLUDED.new_object_count,
            changed_object_count=EXCLUDED.changed_object_count,
            resolved_object_count=EXCLUDED.resolved_object_count,
            unchanged_object_count=EXCLUDED.unchanged_object_count,
            confidence_delta=EXCLUDED.confidence_delta,
            comparison_json=EXCLUDED.comparison_json,
            created_at=NOW()
          RETURNING assessment_comparison_id
        """),{
          "project_id":project_id,"domain_id":current["business_domain_id"],
          "previous_id":previous["assessment_id"],"current_id":current["assessment_id"],
          "previous_version":previous["assessment_version"],"current_version":current["assessment_version"],
          "new_count":counts["NEW"],"changed_count":counts["CHANGED"],
          "resolved_count":counts["RESOLVED"],"unchanged_count":counts["UNCHANGED"],
          "confidence_delta":confidence_delta,
          "comparison_json":json.dumps({"counts":counts,"confidence_delta":confidence_delta})
        }).scalar_one()
        self.connection.execute(text("""
          DELETE FROM ekr_intelligence.enterprise_intelligence_object_change
          WHERE assessment_comparison_id=:cid
        """),{"cid":cid})
        stmt=text("""
          INSERT INTO ekr_intelligence.enterprise_intelligence_object_change(
            assessment_comparison_id,previous_intelligence_object_id,current_intelligence_object_id,
            object_type,object_key,change_type,title,previous_severity,current_severity,
            previous_confidence,current_confidence,confidence_delta,changed_fields,change_summary,change_json
          ) VALUES(
            :cid,:previous_object_id,:current_object_id,:object_type,:object_key,:change_type,:title,
            :previous_severity,:current_severity,:previous_confidence,:current_confidence,
            :confidence_delta,CAST(:changed_fields AS JSONB),:change_summary,CAST(:change_json AS JSONB)
          )
        """)
        for ch in changes:
            self.connection.execute(stmt,{**ch,"cid":cid,
              "changed_fields":json.dumps(ch.get("changed_fields",[])),
              "change_json":json.dumps(ch.get("change_json",{}),default=str)})
        return self.get(int(cid),project_id)

    def get(self,comparison_id:int,project_id:int)->dict[str,Any]:
        row=self.connection.execute(text("""
          SELECT c.*,bd.domain_code,bd.domain_name
          FROM ekr_intelligence.enterprise_intelligence_assessment_comparison c
          JOIN ekr_business.business_domain bd ON bd.business_domain_id=c.business_domain_id
          WHERE c.assessment_comparison_id=:cid AND c.project_id=:project_id
        """),{"cid":comparison_id,"project_id":project_id}).mappings().fetchone()
        if not row:return {}
        result=dict(row)
        result["changes"]=[dict(r) for r in self.connection.execute(text("""
          SELECT * FROM ekr_intelligence.enterprise_intelligence_object_change
          WHERE assessment_comparison_id=:cid
          ORDER BY CASE change_type WHEN 'NEW' THEN 1 WHEN 'CHANGED' THEN 2 WHEN 'RESOLVED' THEN 3 ELSE 4 END,
                   object_type,title
        """),{"cid":comparison_id}).mappings().all()]
        return result

    def timeline(self,project_id:int,business_domain:str)->list[dict[str,Any]]:
        rows=self.connection.execute(text("""
          SELECT a.assessment_id,a.assessment_version,a.assessment_status,a.assessment_title,
                 a.executive_summary,a.overall_confidence,a.generated_at,bd.domain_code,bd.domain_name,
                 COALESCE(o.object_count,0)::INTEGER object_count,
                 COALESCE(o.finding_count,0)::INTEGER finding_count,
                 COALESCE(o.risk_count,0)::INTEGER risk_count,
                 COALESCE(o.opportunity_count,0)::INTEGER opportunity_count,
                 c.assessment_comparison_id,c.new_object_count,c.changed_object_count,
                 c.resolved_object_count,c.unchanged_object_count,c.confidence_delta
          FROM ekr_intelligence.enterprise_intelligence_assessment a
          JOIN ekr_business.business_domain bd ON bd.business_domain_id=a.business_domain_id
          LEFT JOIN LATERAL(
            SELECT COUNT(*) object_count,
              COUNT(*) FILTER(WHERE object_type='FINDING') finding_count,
              COUNT(*) FILTER(WHERE object_type='RISK') risk_count,
              COUNT(*) FILTER(WHERE object_type='OPPORTUNITY') opportunity_count
            FROM ekr_intelligence.enterprise_intelligence_object x WHERE x.assessment_id=a.assessment_id
          ) o ON TRUE
          LEFT JOIN ekr_intelligence.enterprise_intelligence_assessment_comparison c
            ON c.current_assessment_id=a.assessment_id
          WHERE a.project_id=:project_id AND UPPER(bd.domain_code)=UPPER(:domain)
          ORDER BY a.assessment_version DESC
        """),{"project_id":project_id,"domain":business_domain}).mappings().all()
        return [dict(r) for r in rows]
