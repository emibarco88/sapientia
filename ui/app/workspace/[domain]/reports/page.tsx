"use client";

import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  FileText,
  Lightbulb,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type IntelligenceReport = {
  intelligence_report_id: number;
  report_scope: string;
  report_type: string;
  report_title: string;
  summary_text: string | null;
  created_at: string;
  findings: number;
  evidence_items: number;
  high_priority_findings: number;
};

export default function EnterpriseIntelligencePage() {
  const params = useParams();
  const domain = String(params.domain).toUpperCase();
  const [reports, setReports] = useState<IntelligenceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadReports = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiFetch<IntelligenceReport[]>(`/intelligence/${domain}/reports`);
      setReports(Array.isArray(result) ? result : []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Enterprise intelligence could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [domain]);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  const totals = useMemo(
    () =>
      reports.reduce(
        (value, report) => ({
          findings: value.findings + Number(report.findings || 0),
          evidence: value.evidence + Number(report.evidence_items || 0),
          priority: value.priority + Number(report.high_priority_findings || 0),
        }),
        { findings: 0, evidence: 0, priority: 0 },
      ),
    [reports],
  );

  const latestReport = reports[0] ?? null;

  return (
    <AppShell>
      <div className="sap-page intelligence-page">
        <header className="sap-page-header intelligence-page-header">
          <div className="sap-page-header-copy">
            <span className="sap-eyebrow">Enterprise Intelligence</span>
            <h1 className="sap-page-title">What Sapientia is revealing about {domain}</h1>
            <p className="sap-page-description">
              Review evidence-backed findings, priority signals and business narratives generated from the selected business area.
            </p>
          </div>
          <Link className="sap-button sap-button-primary" href={`/workspace/${domain}/ai`}>
            Ask AI Advisor
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </header>

        {error && (
          <div className="friendly-alert intelligence-error" role="alert">
            <CircleAlert size={18} aria-hidden="true" />
            <span>{error}</span>
            <button type="button" onClick={() => void loadReports()}>Try again</button>
          </div>
        )}

        {loading ? (
          <div className="intelligence-loading-state" aria-live="polite">
            <span className="intelligence-loading-mark"><Sparkles size={22} aria-hidden="true" /></span>
            <div><strong>Loading enterprise intelligence</strong><span>Retrieving reports, findings and evidence…</span></div>
          </div>
        ) : (
          <>
            <section className="intelligence-metric-grid" aria-label="Intelligence summary">
              <SummaryMetric icon={<FileText size={19} />} label="Reports" value={reports.length} />
              <SummaryMetric icon={<Lightbulb size={19} />} label="Business findings" value={totals.findings} />
              <SummaryMetric icon={<ShieldCheck size={19} />} label="Evidence items" value={totals.evidence} />
              <SummaryMetric icon={<CircleAlert size={19} />} label="Priority findings" value={totals.priority} priority />
            </section>

            {latestReport && (
              <section className="intelligence-hero-panel">
                <div className="intelligence-hero-icon"><Sparkles size={22} aria-hidden="true" /></div>
                <div className="intelligence-hero-copy">
                  <span className="sap-eyebrow">Latest enterprise narrative</span>
                  <h2>{latestReport.report_title}</h2>
                  <p>{latestReport.summary_text || "Open the latest report to explore its findings and supporting evidence."}</p>
                  <div className="intelligence-hero-meta">
                    <span><CalendarDays size={14} /> {formatDate(latestReport.created_at)}</span>
                    <span><CheckCircle2 size={14} /> {latestReport.findings || 0} findings</span>
                    <span><ShieldCheck size={14} /> {latestReport.evidence_items || 0} evidence items</span>
                  </div>
                </div>
                <Link className="intelligence-hero-link" href={`/workspace/${domain}/reports/${latestReport.intelligence_report_id}`}>
                  Open latest report <ArrowRight size={16} />
                </Link>
              </section>
            )}

            <section className="intelligence-library-section">
              <div className="sap-section-header">
                <div>
                  <span className="sap-eyebrow">Intelligence history</span>
                  <h2 className="sap-section-title">Enterprise reports</h2>
                  <p className="sap-section-description">Each report captures what Sapientia understood when the analysis was generated.</p>
                </div>
                <span className="intelligence-report-count">{reports.length} {reports.length === 1 ? "report" : "reports"}</span>
              </div>

              {reports.length ? (
                <div className="intelligence-report-list">
                  {reports.map((report, index) => (
                    <Link
                      key={report.intelligence_report_id}
                      href={`/workspace/${domain}/reports/${report.intelligence_report_id}`}
                      className="intelligence-report-card"
                    >
                      <span className="intelligence-report-icon"><FileText size={20} aria-hidden="true" /></span>
                      <div className="intelligence-report-content">
                        <div className="intelligence-report-meta">
                          <span>{index === 0 ? "Latest intelligence" : humanise(report.report_type)}</span>
                          <span><CalendarDays size={13} /> {formatDate(report.created_at)}</span>
                        </div>
                        <h3>{report.report_title}</h3>
                        <p>{report.summary_text || "Open this report to explore its findings and supporting evidence."}</p>
                        <footer>
                          <span><CheckCircle2 size={14} /> {report.findings || 0} findings</span>
                          <span><ShieldCheck size={14} /> {report.evidence_items || 0} evidence</span>
                          {report.high_priority_findings > 0 && (
                            <span className="intelligence-priority-label"><CircleAlert size={14} /> {report.high_priority_findings} priority</span>
                          )}
                        </footer>
                      </div>
                      <ArrowRight className="intelligence-report-arrow" size={18} aria-hidden="true" />
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="intelligence-empty-state">
                  <Lightbulb size={26} aria-hidden="true" />
                  <h3>No enterprise intelligence yet</h3>
                  <p>Generate intelligence from the Enterprise Overview to create the first report for this business area.</p>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}

function SummaryMetric({ icon, label, value, priority = false }: { icon: React.ReactNode; label: string; value: number; priority?: boolean }) {
  return (
    <article className={`intelligence-metric-card ${priority ? "is-priority" : ""}`}>
      <span className="intelligence-metric-icon">{icon}</span>
      <div><strong>{value}</strong><span>{label}</span></div>
    </article>
  );
}

function humanise(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date unavailable"
    : new Intl.DateTimeFormat("en-AU", { day: "numeric", month: "short", year: "numeric" }).format(date);
}
