"use client";

import {
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  CircleAlert,
  Database,
  FileText,
  Loader2,
  Network,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type IntelligenceReport = {
  intelligence_report_id: number;
  domain_code: string;
  domain_name: string;
  report_scope: string;
  report_type: string;
  report_title: string;
  summary_text: string | null;
  created_at: string;
};

type IntelligenceFinding = {
  intelligence_finding_id: number;
  finding_type: string;
  finding_title: string;
  finding_description: string;
  finding_interpretation: string | null;
  confidence_score: number | null;
  severity_level: string | null;
  evidence_count: number;
};

type EnterpriseConcept = {
  enterprise_concept_id: number;
  concept_name: string;
  concept_type: string;
  concept_description: string | null;
  confidence_score: number | null;
  concept_status: string | null;
  evidence_count: number;
};

type FindingEvidence = {
  intelligence_evidence_id: number;
  evidence_type: string | null;
  evidence_source: string | null;
  evidence_text: string | null;
  dataset_id: number | null;
  dataset_name: string | null;
  column_name: string | null;
  document_id: number | null;
  document_name: string | null;
  knowledge_item_name: string | null;
  confidence_score: number | null;
};

type ReportResponse = {
  report: IntelligenceReport;
  findings: IntelligenceFinding[];
  concepts: EnterpriseConcept[];
};

type EvidenceResponse = {
  finding: IntelligenceFinding;
  evidence: FindingEvidence[];
};

export default function IntelligenceReportDetailPage() {
  const params = useParams();
  const domain = String(params.domain).toUpperCase();
  const reportId = Number(params.reportId);

  const [response, setResponse] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedFindingId, setExpandedFindingId] = useState<number | null>(null);
  const [evidence, setEvidence] = useState<Record<number, FindingEvidence[]>>({});
  const [evidenceLoading, setEvidenceLoading] = useState<number | null>(null);

  const loadReport = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch<ReportResponse>(`/intelligence/reports/${reportId}`);
      if (data.report.domain_code.toUpperCase() !== domain) {
        throw new Error("This report belongs to a different business area.");
      }
      setResponse(data);
    } catch (cause) {
      setResponse(null);
      setError(getMessage(cause, "Unable to load the intelligence report."));
    } finally {
      setLoading(false);
    }
  }, [domain, reportId]);

  useEffect(() => {
    void loadReport();
  }, [loadReport]);

  async function toggleEvidence(findingId: number) {
    if (expandedFindingId === findingId) {
      setExpandedFindingId(null);
      return;
    }

    setExpandedFindingId(findingId);
    if (evidence[findingId]) return;

    setEvidenceLoading(findingId);
    try {
      const data = await apiFetch<EvidenceResponse>(`/intelligence/findings/${findingId}/evidence`);
      setEvidence((current) => ({
        ...current,
        [findingId]: Array.isArray(data.evidence) ? data.evidence : [],
      }));
    } catch (cause) {
      setError(getMessage(cause, "Unable to load supporting evidence."));
    } finally {
      setEvidenceLoading(null);
    }
  }

  const report = response?.report;
  const findings = response?.findings ?? [];
  const concepts = response?.concepts ?? [];
  const evidenceCount = findings.reduce((total, finding) => total + Number(finding.evidence_count || 0), 0);
  const highPriorityCount = findings.filter((finding) => ["CRITICAL", "HIGH"].includes(String(finding.severity_level || "").toUpperCase())).length;

  return (
    <AppShell>
      <div className="sap-page intelligence-detail-page">
        <Link href={`/workspace/${domain}/reports`} className="intelligence-back-link">
          <ArrowLeft size={15} aria-hidden="true" /> Back to intelligence
        </Link>

        <header className="intelligence-detail-heading">
          <div>
            <span className="sap-eyebrow">{domain} Intelligence Report</span>
            <h1>{report?.report_title || "Intelligence Report"}</h1>
            <p>{report ? `Generated ${formatDateTime(report.created_at)}` : "Loading report details…"}</p>
          </div>
          {report && (
            <Link className="sap-button sap-button-primary" href={`/workspace/${domain}/ai`}>
              Ask AI Advisor <BrainCircuit size={16} aria-hidden="true" />
            </Link>
          )}
        </header>

        {error && (
          <div className="friendly-alert intelligence-error" role="alert">
            <CircleAlert size={18} aria-hidden="true" />
            <span>{error}</span>
            <button type="button" onClick={() => void loadReport()}>Try again</button>
          </div>
        )}

        {loading ? (
          <div className="intelligence-loading-state" aria-live="polite">
            <span className="intelligence-loading-mark"><Sparkles size={22} /></span>
            <div><strong>Loading intelligence report</strong><span>Retrieving findings, evidence and concepts…</span></div>
          </div>
        ) : !response || !report ? (
          <EmptyState title="Report unavailable" description="The requested intelligence report could not be loaded." />
        ) : (
          <>
            <section className="intelligence-metric-grid" aria-label="Report summary">
              <SummaryMetric label="Findings" value={findings.length} />
              <SummaryMetric label="Evidence items" value={evidenceCount} />
              <SummaryMetric label="Concepts" value={concepts.length} />
              <SummaryMetric label="High priority" value={highPriorityCount} priority />
            </section>

            <section className="intelligence-panel intelligence-narrative">
              <span className="intelligence-hero-icon"><Sparkles size={21} aria-hidden="true" /></span>
              <div>
                <span className="sap-eyebrow">Enterprise narrative</span>
                <h2>Consolidated business interpretation</h2>
                <p>{report.summary_text || "No narrative summary is available for this report."}</p>
                <div className="intelligence-hero-meta">
                  <span>{humanise(report.report_type)}</span>
                  <span>{humanise(report.report_scope)}</span>
                  <span>Report #{report.intelligence_report_id}</span>
                </div>
              </div>
            </section>

            <section className="intelligence-panel intelligence-detail-section">
              <div>
                <span className="sap-eyebrow">Evidence-backed findings</span>
                <h2>What deserves attention</h2>
                <p className="intelligence-panel-subtitle">Each finding includes its interpretation, confidence and traceable supporting evidence.</p>
              </div>

              {findings.length ? (
                <div className="intelligence-finding-list">
                  {findings.map((finding) => (
                    <FindingCard
                      key={finding.intelligence_finding_id}
                      finding={finding}
                      expanded={expandedFindingId === finding.intelligence_finding_id}
                      evidence={evidence[finding.intelligence_finding_id] || []}
                      evidenceLoading={evidenceLoading === finding.intelligence_finding_id}
                      onToggle={() => void toggleEvidence(finding.intelligence_finding_id)}
                    />
                  ))}
                </div>
              ) : (
                <EmptyState title="No findings in this report" description="The intelligence engine did not produce findings for this snapshot." />
              )}
            </section>

            <section className="intelligence-panel intelligence-detail-section">
              <div>
                <span className="sap-eyebrow">Knowledge foundation</span>
                <h2>Enterprise concepts used by this report</h2>
                <p className="intelligence-panel-subtitle">Business concepts available to the intelligence layer when the report was generated.</p>
              </div>

              {concepts.length ? (
                <div className="intelligence-concept-grid">
                  {concepts.map((concept) => <ConceptCard key={concept.enterprise_concept_id} concept={concept} />)}
                </div>
              ) : (
                <EmptyState title="No enterprise concepts" description="No enterprise concepts were available for this report." />
              )}
            </section>

            <section className="intelligence-panel intelligence-narrative">
              <span className="intelligence-hero-icon"><BrainCircuit size={21} aria-hidden="true" /></span>
              <div>
                <span className="sap-eyebrow">Continue the analysis</span>
                <h2>Ask questions grounded in this business area</h2>
                <p>Use the AI Advisor to explore the concepts, findings, evidence and intelligence narrative associated with {domain}.</p>
                <Link className="sap-text-link" href={`/workspace/${domain}/ai`}>Open AI Advisor</Link>
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}

function SummaryMetric({ label, value, priority = false }: { label: string; value: number; priority?: boolean }) {
  return (
    <article className={`intelligence-metric-card ${priority ? "is-priority" : ""}`}>
      <span className="intelligence-metric-icon">{priority ? <CircleAlert size={19} /> : <CheckCircle2 size={19} />}</span>
      <div><strong>{value}</strong><span>{label}</span></div>
    </article>
  );
}

function FindingCard({ finding, expanded, evidence, evidenceLoading, onToggle }: {
  finding: IntelligenceFinding;
  expanded: boolean;
  evidence: FindingEvidence[];
  evidenceLoading: boolean;
  onToggle: () => void;
}) {
  const high = ["CRITICAL", "HIGH"].includes(String(finding.severity_level || "").toUpperCase());
  return (
    <article className="intelligence-finding-card">
      <div className="intelligence-finding-main">
        <div className="intelligence-finding-top">
          <div>
            <span className="intelligence-finding-type">{humanise(finding.finding_type)}</span>
            <h3>{finding.finding_title}</h3>
          </div>
          <div className="intelligence-finding-tags">
            <span className={`intelligence-tag ${high ? "is-high" : ""}`}>{finding.severity_level || "INFO"}</span>
            <span className="intelligence-tag">{formatConfidence(finding.confidence_score)}</span>
          </div>
        </div>
        <p className="intelligence-finding-description">{finding.finding_description}</p>
        {finding.finding_interpretation && <div className="intelligence-interpretation"><strong>Business interpretation:</strong> {finding.finding_interpretation}</div>}
        <button type="button" onClick={onToggle} className="intelligence-evidence-button">
          <Network size={14} aria-hidden="true" />
          {expanded ? "Hide evidence" : `View evidence (${finding.evidence_count || 0})`}
        </button>
      </div>

      {expanded && (
        <div className="intelligence-evidence-list">
          {evidenceLoading ? (
            <div className="intelligence-evidence-button"><Loader2 size={14} className="animate-spin" /> Loading evidence…</div>
          ) : evidence.length ? (
            evidence.map((item) => <EvidenceCard key={item.intelligence_evidence_id} evidence={item} />)
          ) : (
            <p className="intelligence-panel-subtitle">No detailed evidence records are associated with this finding.</p>
          )}
        </div>
      )}
    </article>
  );
}

function EvidenceCard({ evidence }: { evidence: FindingEvidence }) {
  const sourceLabel = evidence.column_name
    ? `${evidence.dataset_name || "Dataset"}.${evidence.column_name}`
    : evidence.dataset_name || evidence.document_name || evidence.knowledge_item_name || evidence.evidence_source || "Enterprise evidence";

  return (
    <div className="intelligence-evidence-item">
      <span className="intelligence-report-icon">
        {evidence.dataset_id ? <Database size={16} /> : evidence.document_id ? <FileText size={16} /> : <CheckCircle2 size={16} />}
      </span>
      <div>
        <div className="intelligence-evidence-source">{sourceLabel}</div>
        {evidence.evidence_text && <p>{evidence.evidence_text}</p>}
      </div>
      <span className="intelligence-tag">{formatConfidence(evidence.confidence_score)}</span>
    </div>
  );
}

function ConceptCard({ concept }: { concept: EnterpriseConcept }) {
  return (
    <article className="intelligence-concept-card">
      <h3>{concept.concept_name}</h3>
      <span>{humanise(concept.concept_type)}</span>
      <p>{concept.concept_description || "No description is available."}</p>
      <div className="intelligence-concept-meta">
        <span>{concept.evidence_count || 0} evidence items</span>
        <span>{formatConfidence(concept.confidence_score)}</span>
      </div>
    </article>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="intelligence-empty-state">
      <ShieldAlert size={26} aria-hidden="true" />
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

function humanise(value: string | null) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatConfidence(value: number | null): string {
  if (value === null) return "N/A";
  const numeric = Number(value);
  return `${Math.round((numeric <= 1 ? numeric * 100 : numeric) * 10) / 10}%`;
}

function formatDateTime(value: string | null): string {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not available" : new Intl.DateTimeFormat("en-AU", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function getMessage(cause: unknown, fallback: string): string {
  return cause instanceof Error ? cause.message : fallback;
}
