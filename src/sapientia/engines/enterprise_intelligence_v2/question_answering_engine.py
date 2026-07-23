from __future__ import annotations
import re
from typing import Any
from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence_v2.enterprise_intelligence_repository import EnterpriseIntelligenceRepository

class EnterpriseQuestionAnsweringEngine:
    """Evidence-first deterministic answer builder. An LLM may later verbalise this result, but never invent its facts."""
    def __init__(self, database_engine=None): self.database_engine=database_engine or get_engine()

    @staticmethod
    def classify(question: str) -> str:
        q=question.lower()
        if any(x in q for x in ('impact','affected','downstream','upstream','depend')): return 'IMPACT'
        if any(x in q for x in ('why','root cause','cause','changed','decrease','increase')): return 'ROOT_CAUSE'
        if any(x in q for x in ('recommend','should','action','investigate')): return 'RECOMMENDATION'
        return 'EXPLANATION'

    @staticmethod
    def _match_objects(question: str, objects: list[dict[str,Any]]) -> list[dict[str,Any]]:
        q=re.sub(r'[^a-z0-9 ]',' ',question.lower())
        return [o for o in objects if str(o['canonical_name']).lower() in q or all(t in q for t in str(o['canonical_name']).lower().split())]

    def answer(self, project_id: int, business_domain: str, question: str, persist: bool=True) -> dict[str,Any]:
        with self.database_engine.begin() as connection:
            repo=EnterpriseIntelligenceRepository(connection)
            reasoning_run_id=repo.latest_reasoning_run_id(project_id,business_domain)
            context=repo.reasoning_context(project_id,reasoning_run_id)
            qtype=self.classify(question); matched=self._match_objects(question,context['objects'])
            matched_ids={int(o['enterprise_object_id']) for o in matched}
            relevant_edges=[e for e in context['edges'] if not matched_ids or int(e['source_enterprise_object_id']) in matched_ids or int(e['target_enterprise_object_id']) in matched_ids]
            relevant_causes=[c for c in context['root_causes'] if not matched_ids or int(c['affected_enterprise_object_id']) in matched_ids]
            evidence=[]
            for edge in relevant_edges[:20]:
                evidence.append({"evidence_type":"DEPENDENCY_EDGE","evidence_key":f"dependency_edge:{edge['dependency_edge_id']}",
                    "source_schema":"ekr_reasoning","source_table":"dependency_edge","source_record_id":int(edge['dependency_edge_id']),
                    "relevance_score":float(edge['confidence_score']),"summary":f"{edge['source_name']} -> {edge['target_name']} ({edge['dependency_type']})"})
            if qtype=='ROOT_CAUSE' and relevant_causes:
                top=relevant_causes[:5]; answer_text="The strongest upstream root-cause candidates are: "+"; ".join(f"{c['candidate_name']} ({float(c['confidence_score']):.2f})" for c in top)+"."
                confidence=sum(float(c['confidence_score']) for c in top)/len(top)
            elif relevant_edges:
                names=', '.join(o['canonical_name'] for o in matched) or 'the requested domain'
                answer_text=f"Sapientia found {len(relevant_edges)} evidence-backed dependency connection(s) relevant to {names}. " + "; ".join(e['summary'] for e in evidence[:5])+"."
                confidence=sum(float(e['confidence_score']) for e in relevant_edges)/len(relevant_edges)
            elif matched:
                answer_text=f"Sapientia recognises {', '.join(o['canonical_name'] for o in matched)}, but no reasoning edges currently support a stronger answer."
                confidence=.35
            else:
                answer_text="Sapientia could not match the question to an active enterprise object or evidence-backed reasoning path."
                confidence=0.0
            missing=[] if evidence else ["No dependency or reasoning evidence matched the question."]
            result={"question":question,"question_type":qtype,"answer_text":answer_text,"confidence":round(confidence,4),
                    "status":"ANSWERED" if confidence>=.6 else "PARTIAL" if confidence>0 else "INSUFFICIENT_EVIDENCE",
                    "matched_objects":matched,"evidence":evidence,"assumptions":[],"missing_evidence":missing,"conflicting_evidence":[]}
            if persist:
                result.update(repo.save_answer(None,project_id,business_domain,question,qtype,result))
            return result
