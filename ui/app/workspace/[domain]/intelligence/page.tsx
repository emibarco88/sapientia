"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  BrainCircuit,
  CircleAlert,
  History,
  Lightbulb,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  Target,
  TrendingUp,
} from "lucide-react";

import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type Assessment = {
  assessment_id: number;
  assessment_version: number;
  knowledge_version?: number | null;
  assessment_status: string;
  assessment_title: string;
  executive_summary?: string | null;
  overall_confidence?: number | null;
  generated_at: string;
  intelligence_report_id?: number | null;
};

type IntelligenceObject = {
  intelligence_object_id: number;
  object_type: string;
  title: string;
  description?: string | null;
  severity?: string | null;
  priority?: string | null;
  confidence_score?: number | null;
  evidence_count: number;
};

type ObjectSummary = {
  assessment_id: number;
  total_objects: number;
  total_evidence: number;
  by_type: Record<string, { object_count: number; evidence_count: number; high_severity_count: number }>;
};

const titleCaseDomain = (value: string) => value.toLowerCase().replace(/\b\w/g, (character) => character.toUpperCase());

const TYPE_ORDER = ["FINDING", "RISK", "OPPORTUNITY", "KPI", "RECOMMENDATION", "OBSERVATION", "ROOT_CAUSE", "BUSINESS_IMPACT"];

const typeIcon = (type: string) => {
  if (type === "RISK") return <CircleAlert size={18} />;
  if (type === "OPPORTUNITY") return <TrendingUp size={18} />;
  if (type === "KPI") return <Target size={18} />;
  if (type === "RECOMMENDATION") return <ListChecks size={18} />;
  if (type === "FINDING") return <Lightbulb size={18} />;
  return <BrainCircuit size={18} />;
};

export default function IntelligenceAssessmentPage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain || "").toUpperCase();
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [objects, setObjects] = useState<IntelligenceObject[]>([]);
  const [summary, setSummary] = useState<ObjectSummary | null>(null);
  const [activeType, setActiveType] = useState<string>("PRIORITISED");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generationMessage, setGenerationMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<{ assessments: Assessment[] }>(
        `/intelligence/assessments/domain/${encodeURIComponent(domain)}?project_id=1`,
      );
      const history = response.assessments || [];
      setAssessments(history);
      if (history[0]) {
        const assessmentId = history[0].assessment_id;
        const [objectResponse, summaryResponse] = await Promise.all([
          apiFetch<{ objects: IntelligenceObject[] }>(
            `/intelligence/assessments/${assessmentId}/objects?project_id=1`,
          ),
          apiFetch<ObjectSummary>(
            `/intelligence/assessments/${assessmentId}/objects/summary?project_id=1`,
          ),
        ]);
        setObjects(objectResponse.objects || []);
        setSummary(summaryResponse);
      } else {
        setObjects([]);
        setSummary(null);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Intelligence assessments could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [domain]);

  const generateAssessment = useCallback(async () => {
    setGenerating(true);
    setError(null);
    setGenerationMessage(null);
    try {
      const result = await apiFetch<{
        status?: string;
        message?: string;
        assessment_version?: number;
        duplicate_prevented?: boolean;
      }>(
        `/intelligence/${encodeURIComponent(domain)}/generate`,
        { method: "POST", body: JSON.stringify({ project_id: 1, persist: true, force: false }) },
      );
      setGenerationMessage(
        result.message ||
          (result.duplicate_prevented
            ? "No relevant knowledge changes were detected. The latest assessment remains current."
            : `Assessment version ${result.assessment_version || "new"} generated successfully.`),
      );
      if (!result.duplicate_prevented) {
        await load();
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The assessment could not be generated.");
    } finally {
      setGenerating(false);
    }
  }, [domain, load]);

  useEffect(() => { void load(); }, [load]);
  const latest = assessments[0];
  const isTechnicalObservation = (item: IntelligenceObject) => {
    const value = `${item.title || ""} ${item.description || ""}`.toUpperCase();
    return value.includes("SAPENTIA_DEMO.") || value.includes("SAPIENTIA_DEMO.") || value.includes("GL_TRANSACTIONS") || value.includes("THREE_WAY_MATCH") || value.includes(".INVOICES");
  };
  const visibleObjects = useMemo(() => {
    if (activeType === "ALL") return objects;
    if (activeType === "PRIORITISED") return objects.filter((item) => !isTechnicalObservation(item));
    if (activeType === "TECHNICAL") return objects.filter(isTechnicalObservation);
    return objects.filter((item) => item.object_type === activeType);
  }, [activeType, objects]);
  const availableTypes = TYPE_ORDER.filter((type) => (summary?.by_type[type]?.object_count || 0) > 0);

  return (
    <AppShell>
      <div className="sap-page intelligence-page">
        <header className="sap-page-header">
          <div className="sap-page-header-copy">
            <span className="sap-eyebrow">Enterprise Intelligence</span>
            <h1 className="sap-page-title">{titleCaseDomain(domain)} Intelligence Assessment</h1>
            <p className="sap-page-description">
              Structured findings, risks, opportunities, KPIs and recommendations backed by enterprise evidence.
            </p>
          </div>
          <div className="p2d-intelligence-actions">
            <button className="sap-button sap-button-primary" type="button" disabled={generating} onClick={() => void generateAssessment()}>
              <RefreshCw size={16} className={generating ? "p2d-spin" : ""}/> {generating ? "Generating Assessment…" : latest ? "Generate New Assessment" : "Generate Assessment"}
            </button>
            <Link className="sap-button sap-button-secondary" href={`/workspace/${domain}/reports`}>Open Reports <ArrowRight size={16}/></Link>
          </div>
        </header>

        {error && <div className="friendly-alert" role="alert">{error}</div>}
        {generationMessage && <div className="p2d-success" role="status">{generationMessage}</div>}
        {loading ? <p>Loading Enterprise Intelligence…</p> : assessments.length === 0 ? (
          <section className="intelligence-empty-state">
            <BrainCircuit size={28} />
            <h2>No assessment has been generated yet</h2>
            <p>Enterprise knowledge is ready to be assessed intentionally. Use Generate Assessment when you want to publish a versioned business assessment and report.</p>
          </section>
        ) : (
          <>
            <section className="intelligence-hero-panel">
              <div className="intelligence-hero-icon"><BrainCircuit size={22} /></div>
              <div className="intelligence-hero-copy">
                <span className="sap-eyebrow">Latest assessment · Version {latest.assessment_version}{latest.knowledge_version ? ` · Knowledge ${latest.knowledge_version}` : ""}</span>
                <h2>{latest.assessment_title}</h2>
                <p>{latest.executive_summary || "The latest assessment is ready for review."}</p>
                <div className="intelligence-hero-meta">
                  <span><ShieldCheck size={14} /> {latest.assessment_status}</span>
                  <span><History size={14} /> {new Date(latest.generated_at).toLocaleString("en-AU")}</span>
                  <span>{summary?.total_objects || 0} assessment items</span>
                  <span>{summary?.total_evidence || 0} evidence references</span>
                </div>
              {visibleObjects.length === 0 && <div className="intelligence-empty-filter">No assessment items match this view.</div>}
              </div>
            </section>

            <section className="intelligence-library-section">
              <div className="sap-section-header">
                <div><span className="sap-eyebrow">Structured assessment</span><h2 className="sap-section-title">Assessment items</h2></div>
              </div>
              <p className="intelligence-library-intro">Assessment items are generated conclusions and actions. The prioritised view emphasises business-readable findings and recommendations; source-level dependency observations remain available under Technical.</p>
              <div className="intelligence-object-filters" role="tablist" aria-label="Assessment item types">
                <button className={activeType === "PRIORITISED" ? "is-active" : ""} onClick={() => setActiveType("PRIORITISED")}>Prioritised <span>{objects.filter((item) => !isTechnicalObservation(item)).length}</span></button>
                <button className={activeType === "ALL" ? "is-active" : ""} onClick={() => setActiveType("ALL")}>All items <span>{objects.length}</span></button>
                <button className={activeType === "TECHNICAL" ? "is-active" : ""} onClick={() => setActiveType("TECHNICAL")}>Technical <span>{objects.filter(isTechnicalObservation).length}</span></button>
                {availableTypes.map((type) => (
                  <button key={type} className={activeType === type ? "is-active" : ""} onClick={() => setActiveType(type)}>
                    {type.replaceAll("_", " ")} <span>{summary?.by_type[type]?.object_count || 0}</span>
                  </button>
                ))}
              </div>

              <div className="intelligence-object-grid">
                {visibleObjects.map((item) => (
                  <article className={`intelligence-object-card ${isTechnicalObservation(item) ? "is-technical" : ""}`} key={item.intelligence_object_id}>
                    <span className="intelligence-object-classification">{isTechnicalObservation(item) ? "Technical observation" : "Business assessment"}</span>
                    <span className={`intelligence-object-type intelligence-object-type-${item.object_type.toLowerCase()}`}>
                      {typeIcon(item.object_type)} {item.object_type.replaceAll("_", " ")}
                    </span>
                    <h3>{item.title}</h3>
                    <p>{item.description || "No additional description was generated."}</p>
                    <div className="intelligence-object-meta">
                      {item.severity && <span>Severity: {item.severity}</span>}
                      {item.priority && <span>Priority: {item.priority}</span>}
                      {item.confidence_score != null && <span>Confidence: {Math.round(item.confidence_score * 100)}%</span>}
                      <span>{item.evidence_count || 0} evidence</span>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="intelligence-library-section">
              <div className="sap-section-header"><div><span className="sap-eyebrow">Assessment history</span><h2 className="sap-section-title">Versions</h2></div></div>
              <div className="intelligence-report-list">
                {assessments.map((assessment) => (
                  <article className="intelligence-report-card" key={assessment.assessment_id}>
                    <span className="intelligence-report-icon"><History size={20} /></span>
                    <div className="intelligence-report-content">
                      <div className="intelligence-report-meta"><span>Version {assessment.assessment_version}</span>{assessment.knowledge_version && <span>Knowledge {assessment.knowledge_version}</span>}<span>{assessment.assessment_status}</span></div>
                      <h3>{assessment.assessment_title}</h3>
                      <p>{assessment.executive_summary || "No executive summary was recorded."}</p>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
