
"""Compares versioned Enterprise Intelligence Assessments."""
from __future__ import annotations
from decimal import Decimal
from typing import Any
from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence.assessment_evolution_repository import EnterpriseIntelligenceEvolutionRepository

class EnterpriseIntelligenceEvolutionService:
    FIELDS=("title","description","interpretation","status","category","severity","priority",
            "confidence_score","probability_score","impact_score","estimated_value",
            "estimated_value_currency","enterprise_object_id","source_object_type",
            "source_object_id","source_schema","source_table","source_record_id")

    def compare_with_previous(self,current_assessment_id:int,project_id:int=1)->dict[str,Any]:
        engine=get_engine()
        with engine.begin() as connection:
            repo=EnterpriseIntelligenceEvolutionRepository(connection)
            current=repo.assessment(current_assessment_id,project_id)
            if not current: raise ValueError("Current assessment was not found.")
            previous=repo.previous(current_assessment_id,project_id)
            if not previous:
                return {"comparison_created":False,"reason":"This is the first assessment for the business domain.",
                        "current_assessment_id":current_assessment_id,
                        "current_version":current["assessment_version"]}
            return self._compare(repo,previous,current,project_id)

    def compare(self,previous_assessment_id:int,current_assessment_id:int,project_id:int=1,refresh:bool=False):
        engine=get_engine()
        with engine.begin() as connection:
            repo=EnterpriseIntelligenceEvolutionRepository(connection)
            previous=repo.assessment(previous_assessment_id,project_id)
            current=repo.assessment(current_assessment_id,project_id)
            if not previous or not current: raise ValueError("Both assessments must exist.")
            if previous["business_domain_id"]!=current["business_domain_id"]:
                raise ValueError("Assessments must belong to the same business domain.")
            if previous["assessment_version"]>=current["assessment_version"]:
                raise ValueError("The previous assessment must have an earlier version.")
            if not refresh:
                existing=repo.existing(previous_assessment_id,current_assessment_id,project_id)
                if existing:return existing
            return self._compare(repo,previous,current,project_id)

    def get(self,comparison_id:int,project_id:int=1):
        engine=get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceEvolutionRepository(connection).get(comparison_id,project_id)

    def timeline(self,project_id:int,business_domain:str):
        engine=get_engine()
        with engine.connect() as connection:
            return EnterpriseIntelligenceEvolutionRepository(connection).timeline(project_id,business_domain)

    def _compare(self,repo,previous,current,project_id):
        old={self._identity(x):x for x in repo.objects(previous["assessment_id"])}
        new={self._identity(x):x for x in repo.objects(current["assessment_id"])}
        changes=[]; counts={"NEW":0,"CHANGED":0,"RESOLVED":0,"UNCHANGED":0}
        for identity in sorted(set(old)|set(new)):
            ch=self._change(old.get(identity),new.get(identity))
            changes.append(ch); counts[ch["change_type"]]+=1
        delta=self._delta(previous.get("overall_confidence"),current.get("overall_confidence"))
        return repo.save(previous,current,project_id,counts,delta,changes)

    @staticmethod
    def _identity(item):
        return (str(item.get("object_type") or "").upper(),str(item.get("object_key") or "").strip().lower())

    def _change(self,old,new):
        source=new or old or {}
        if old is None: change_type="NEW"; fields=[]
        elif new is None: change_type="RESOLVED"; fields=[]
        else:
            fields=[f for f in self.FIELDS if self._normalise(old.get(f))!=self._normalise(new.get(f))]
            change_type="CHANGED" if fields else "UNCHANGED"
        pc=self._number(old.get("confidence_score")) if old else None
        cc=self._number(new.get("confidence_score")) if new else None
        title=source.get("title") or source.get("object_key") or "Intelligence object"
        summary={"NEW":f"{title} was introduced in the current assessment.",
                 "RESOLVED":f"{title} is no longer present in the current assessment.",
                 "UNCHANGED":f"{title} is unchanged.",
                 "CHANGED":f"{title} changed: {', '.join(fields)}."}[change_type]
        return {
          "previous_object_id":old.get("intelligence_object_id") if old else None,
          "current_object_id":new.get("intelligence_object_id") if new else None,
          "object_type":str(source.get("object_type") or "UNKNOWN").upper(),
          "object_key":str(source.get("object_key") or ""),
          "change_type":change_type,"title":source.get("title"),
          "previous_severity":old.get("severity") if old else None,
          "current_severity":new.get("severity") if new else None,
          "previous_confidence":pc,"current_confidence":cc,"confidence_delta":self._delta(pc,cc),
          "changed_fields":fields,"change_summary":summary,
          "change_json":{"previous":self._snapshot(old),"current":self._snapshot(new)}
        }

    @staticmethod
    def _snapshot(item):
        if not item:return None
        keys=("intelligence_object_id","object_type","object_key","title","description","interpretation",
              "status","category","severity","priority","confidence_score","probability_score",
              "impact_score","estimated_value","estimated_value_currency")
        return {k:item.get(k) for k in keys}

    @staticmethod
    def _normalise(value):
        if isinstance(value,Decimal):return float(value)
        if isinstance(value,str):return value.strip()
        return value

    @staticmethod
    def _number(value):
        if value is None:return None
        try:return float(value)
        except (TypeError,ValueError):return None

    @classmethod
    def _delta(cls,old,new):
        oldn=cls._number(old); newn=cls._number(new)
        return None if oldn is None or newn is None else round(newn-oldn,6)
