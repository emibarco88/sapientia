from __future__ import annotations
from collections import Counter, defaultdict
from typing import Any
from sapientia.db.connection import get_engine
from sapientia.repositories.intelligence_v2.enterprise_intelligence_repository import EnterpriseIntelligenceRepository

class EnterpriseIntelligenceEngine:
    """Creates deterministic findings and recommendations from U5 reasoning output."""
    def __init__(self, database_engine=None): self.database_engine = database_engine or get_engine()

    @staticmethod
    def _derive(context: dict[str, Any]) -> tuple[list[dict[str,Any]], list[dict[str,Any]]]:
        findings: list[dict[str,Any]] = []; recommendations: list[dict[str,Any]] = []
        edges = context["edges"]; objects = {int(o["enterprise_object_id"]): o for o in context["objects"]}
        incoming=Counter(); outgoing=Counter(); evidence=defaultdict(int)
        for e in edges:
            s=int(e["source_enterprise_object_id"]); t=int(e["target_enterprise_object_id"])
            outgoing[s]+=1; incoming[t]+=1; evidence[s]+=int(e["evidence_count"] or 0); evidence[t]+=int(e["evidence_count"] or 0)
        for oid, obj in objects.items():
            degree=incoming[oid]+outgoing[oid]
            if degree >= 3:
                conf=min(1.0, .55 + .05*degree + .02*evidence[oid])
                findings.append({"finding_type":"CRITICAL_DEPENDENCY","severity":"HIGH" if degree>=5 else "MEDIUM",
                    "title":f"{obj['canonical_name']} is a highly connected dependency",
                    "finding_text":f"{obj['canonical_name']} has {incoming[oid]} upstream and {outgoing[oid]} downstream dependency connection(s).",
                    "enterprise_object_id":oid,"confidence_score":round(conf,4),"evidence_count":evidence[oid],"degree":degree})
            if degree and evidence[oid] == 0:
                findings.append({"finding_type":"EVIDENCE_GAP","severity":"MEDIUM","title":f"Evidence gap for {obj['canonical_name']}",
                    "finding_text":f"{obj['canonical_name']} participates in {degree} dependency connection(s) without linked relationship evidence.",
                    "enterprise_object_id":oid,"confidence_score":.7,"evidence_count":0,"degree":degree})
        for finding in findings:
            if finding["finding_type"] == "CRITICAL_DEPENDENCY":
                recommendations.append({"finding_title":finding["title"],"priority":"HIGH","title":f"Protect {objects[finding['enterprise_object_id']]['canonical_name']}",
                    "recommendation_text":"Validate monitoring, ownership, recovery procedures and downstream notification for this dependency.",
                    "rationale_text":"Highly connected objects can propagate operational or data failures across multiple enterprise processes.",
                    "confidence_score":finding["confidence_score"]})
            else:
                recommendations.append({"finding_title":finding["title"],"priority":"MEDIUM","title":f"Strengthen evidence for {objects[finding['enterprise_object_id']]['canonical_name']}",
                    "recommendation_text":"Attach lineage, business-rule, process or document evidence to the relationships supporting this object.",
                    "rationale_text":"Sapientia should not present high-confidence intelligence without traceable evidence.","confidence_score":.75})
        return findings, recommendations

    def generate(
        self,
        project_id: int,
        business_domain: str,
        reasoning_run_id: int | None = None,
    ) -> dict[str, Any]:
        normalized_domain = str(business_domain or "").strip().upper()
        run_id = None

        try:
            with self.database_engine.begin() as connection:
                repo = EnterpriseIntelligenceRepository(connection)
                reasoning_run_id = (
                    reasoning_run_id
                    or repo.latest_reasoning_run_id(
                        project_id,
                        normalized_domain,
                    )
                )
                if reasoning_run_id is None:
                    raise ValueError(
                        "No completed enterprise reasoning run is available."
                    )

                run_id = repo.create_run(
                    project_id,
                    reasoning_run_id,
                    normalized_domain,
                )
                context = repo.reasoning_context(
                    project_id,
                    reasoning_run_id,
                )
                findings, recommendations = self._derive(context)

                finding_ids: dict[str, int] = {}
                for finding in findings:
                    finding_ids[finding["title"]] = repo.add_finding(
                        run_id,
                        finding,
                    )

                persisted_recommendations: list[dict[str, Any]] = []
                for recommendation in recommendations:
                    recommendation_payload = dict(recommendation)
                    finding_title = recommendation_payload.pop(
                        "finding_title",
                        None,
                    )
                    repo.add_recommendation(
                        run_id,
                        finding_ids.get(finding_title),
                        recommendation_payload,
                    )
                    persisted_recommendations.append(
                        recommendation_payload
                    )

                confidence = (
                    round(
                        sum(
                            finding["confidence_score"]
                            for finding in findings
                        )
                        / len(findings),
                        4,
                    )
                    if findings
                    else 0.0
                )

                summary = (
                    f"Sapientia analysed {len(context['objects'])} "
                    f"enterprise objects and {len(context['edges'])} "
                    f"dependency connections. It identified "
                    f"{len(findings)} insight(s) and generated "
                    f"{len(persisted_recommendations)} recommendation(s)."
                )

                output = {
                    "enterprise_intelligence_run_id": run_id,
                    "reasoning_run_id": reasoning_run_id,
                    "business_domain": normalized_domain,
                    "executive_summary": summary,
                    "confidence": confidence,
                    "findings": findings,
                    "recommendations": persisted_recommendations,
                }

                repo.complete_run(
                    run_id,
                    summary,
                    confidence,
                    output,
                )
                return output

        except Exception as exc:
            if run_id is not None:
                with self.database_engine.begin() as failure_connection:
                    EnterpriseIntelligenceRepository(
                        failure_connection
                    ).fail_run(run_id, str(exc))
            raise
