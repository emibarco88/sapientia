"use client";

import { ArrowRight, CircleAlert, Clock3, FileText, Lightbulb, Network, ShieldCheck, Sparkles, Target, TrendingUp } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type Workspace = {
  domain?: { domain_code?: string; domain_name?: string; description?: string | null };
  summary?: { datasets?: number; enterprise_concepts?: number; findings?: number; reports?: number };
  findings?: Array<{ intelligence_finding_id: number | string; finding_title?: string; finding_description?: string; finding_interpretation?: string; severity_level?: string; finding_type?: string; created_at?: string | null }>;
  concepts?: Array<{ enterprise_concept_id: number | string; concept_name?: string; concept_description?: string; confidence_score?: number | string; evidence_count?: number }>;
  latest_report?: { report_title?: string; summary_text?: string | null; created_at?: string | null; intelligence_report_id?: number } | null;
};
type Assessment = { assessment_id: number; assessment_version: number; assessment_status: string; assessment_title: string; executive_summary?: string | null; overall_confidence?: number | null; generated_at: string; };
type IntelligenceObject = { intelligence_object_id: number; object_type: string; title: string; description?: string | null; severity?: string | null; priority?: string | null; confidence_score?: number | null; evidence_count: number; };

const objectIcon = (type: string) => type === "RISK" ? <CircleAlert size={17} /> : type === "RECOMMENDATION" ? <Target size={17} /> : type === "OPPORTUNITY" ? <TrendingUp size={17} /> : <Lightbulb size={17} />;

export default function BusinessDomainPage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain || "").toUpperCase();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [objects, setObjects] = useState<IntelligenceObject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const workspaceData = await apiFetch<Workspace>(`/domains/${encodeURIComponent(domain)}/workspace`);
      setWorkspace(workspaceData);
      try {
        const history = await apiFetch<{ assessments: Assessment[] }>(`/intelligence/assessments/domain/${encodeURIComponent(domain)}?project_id=1`);
        const list = history.assessments || [];
        setAssessments(list);
        if (list[0]) {
          const objectData = await apiFetch<{ objects: IntelligenceObject[] }>(`/intelligence/assessments/${list[0].assessment_id}/objects?project_id=1`);
          setObjects(objectData.objects || []);
        } else setObjects([]);
      } catch { setAssessments([]); setObjects([]); }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "This business domain could not be loaded."); }
    finally { setLoading(false); }
  }, [domain]);

  useEffect(() => { void load(); }, [load]);

  const name = workspace?.domain?.domain_name || domain;
  const latest = assessments[0];
  const findings = objects.filter((item) => ["FINDING", "OBSERVATION", "ROOT_CAUSE", "BUSINESS_IMPACT"].includes(item.object_type));
  const risks = objects.filter((item) => item.object_type === "RISK");
  const opportunities = objects.filter((item) => item.object_type === "OPPORTUNITY");
  const recommendations = objects.filter((item) => item.object_type === "RECOMMENDATION");
  const confidence = latest?.overall_confidence != null ? Math.round(Number(latest.overall_confidence) * 100) : null;
  const generated = latest?.generated_at || workspace?.latest_report?.created_at;
  const summary = latest?.executive_summary || workspace?.latest_report?.summary_text || workspace?.domain?.description || `Sapientia is building an evidence-backed understanding of ${name}.`;
  const timeline = useMemo(() => [
    ...(generated ? [{ date: generated, title: "Latest enterprise assessment generated", detail: `${objects.length} intelligence items were considered.` }] : []),
    ...recommendations.slice(0, 2).map((item) => ({ date: generated || "", title: item.title, detail: "Recommendation added to the current assessment." })),
    ...(workspace?.findings || []).slice(0, 2).map((item) => ({ date: item.created_at || "", title: item.finding_title || "Finding identified", detail: item.finding_description || "New evidence-backed finding." })),
  ].slice(0, 5), [generated, objects.length, recommendations, workspace?.findings]);

  return (
    <AppShell>
      <div className="vnext-page vnext-domain-page">
        <header className="vnext-domain-hero">
          <div><span className="vnext-eyebrow">Business domain</span><h1>{name}</h1><p>{workspace?.domain?.description || `A living view of what Sapientia currently understands about ${name}.`}</p></div>
        </header>

        {error && <div className="vnext-alert">{error}</div>}
        {loading ? <div className="vnext-loading">Understanding {name}…</div> : (
          <>
<section className="vnext-assessment-hero">
              <div className="vnext-assessment-copy"><span className="vnext-eyebrow">Current business assessment</span><h2>{latest?.assessment_title || workspace?.latest_report?.report_title || `${name} business assessment`}</h2><p>{summary}</p><div className="vnext-assessment-meta">{generated && <span><Clock3 size={14} /> Updated {new Date(generated).toLocaleString("en-AU")}</span>}{latest && <span><ShieldCheck size={14} /> Version {latest.assessment_version}</span>}{confidence != null && <span>{confidence}% confidence</span>}</div></div>
              <div className="vnext-health-summary"><span>Current signal</span><strong>{risks.length > 2 ? "Needs attention" : risks.length > 0 ? "Review advised" : "Stable"}</strong><small>{risks.length} risks · {recommendations.length} recommendations</small></div>
            </section>

            <section className="vnext-business-signals">
              <div className="vnext-section-heading"><div><span className="vnext-eyebrow">What matters now</span><h2>Business signals</h2><p>Prioritised explanations rather than technical platform statistics.</p></div></div>
              <div className="vnext-signal-grid">
                <Signal title="Key findings" icon={<Lightbulb size={19} />} items={findings} empty="No material findings have been identified yet." />
                <Signal title="Risks requiring attention" icon={<CircleAlert size={19} />} items={risks} empty="No priority risks have been identified." />
                <Signal title="Opportunities" icon={<TrendingUp size={19} />} items={opportunities} empty="No opportunities have been identified yet." />
              </div>
            </section>

            <section className="vnext-recommendations">
              <div className="vnext-section-heading"><div><span className="vnext-eyebrow">What to do next</span><h2>Recommendations</h2></div><Link href={`/workspace/${domain}/intelligence`}>Review full assessment <ArrowRight size={15} /></Link></div>
              {recommendations.length ? <div className="vnext-recommendation-list">{recommendations.slice(0, 6).map((item, index) => <article key={item.intelligence_object_id}><span>{index + 1}</span><div><h3>{item.title}</h3><p>{item.description || "Review this recommended action in the full assessment."}</p><small>{item.priority ? `${item.priority} priority` : "Recommended action"} · {item.evidence_count || 0} evidence references</small></div></article>)}</div> : <div className="vnext-soft-empty">Recommendations will appear when Sapientia identifies evidence-backed actions.</div>}
            </section>

            <section className="vnext-two-column">
              <article className="vnext-evidence-panel"><div className="vnext-section-heading"><div><span className="vnext-eyebrow">Why Sapientia believes this</span><h2>Evidence and business understanding</h2></div></div><p>The current view is grounded in {workspace?.summary?.datasets ?? 0} datasets and {workspace?.summary?.enterprise_concepts ?? 0} enterprise concepts.</p><div className="vnext-concept-list">{(workspace?.concepts || []).slice(0, 5).map((concept) => <div key={concept.enterprise_concept_id}><FileText size={16} /><span><strong>{concept.concept_name || "Business concept"}</strong><small>{concept.evidence_count || 0} evidence references</small></span></div>)}</div><Link href={`/workspace/${domain}/explorer`}>Explore evidence and relationships <ArrowRight size={15} /></Link></article>
              <article className="vnext-timeline"><div className="vnext-section-heading"><div><span className="vnext-eyebrow">Enterprise timeline</span><h2>How {name} is evolving</h2></div></div>{timeline.length ? timeline.map((item, index) => <div className="vnext-timeline-item" key={`${item.title}-${index}`}><span /><div><time>{item.date ? new Date(item.date).toLocaleDateString("en-AU", { day: "numeric", month: "short", year: "numeric" }) : "Current"}</time><h3>{item.title}</h3><p>{item.detail}</p></div></div>) : <div className="vnext-soft-empty">Change history will appear as assessments evolve.</div>}</article>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}

function Signal({ title, icon, items, empty }: { title: string; icon: React.ReactNode; items: IntelligenceObject[]; empty: string }) {
  return <article className="vnext-signal-card"><div className="vnext-signal-heading"><span>{icon}</span><h3>{title}</h3><strong>{items.length}</strong></div>{items.length ? <div>{items.slice(0, 4).map((item) => <div className="vnext-signal-item" key={item.intelligence_object_id}><h4>{item.title}</h4><p>{item.description || "No additional explanation was provided."}</p><small>{item.severity ? `${item.severity} severity · ` : ""}{item.evidence_count || 0} evidence</small></div>)}</div> : <p className="vnext-signal-empty">{empty}</p>}</article>;
}
