"use client";

import {
  ArrowRight,
  BookOpen,
  CircleAlert,
  FileText,
  Network,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import ConceptExplorer, { KnowledgeConcept } from "@/components/knowledge/ConceptExplorer";
import KnowledgeSummary from "@/components/knowledge/KnowledgeSummary";
import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type Finding = {
  intelligence_finding_id: number;
  intelligence_report_id?: number | null;
  finding_title: string;
  finding_description: string;
  severity_level: string | null;
  confidence_score: number | null;
};

type WorkspaceResponse = {
  domain?: {
    domain_code: string;
    domain_name: string;
    description: string | null;
  };
  summary: {
    datasets: number;
    enterprise_concepts: number;
    findings: number;
    reports: number;
  };
  concepts: KnowledgeConcept[];
  findings: Finding[];
  latest_report: {
    intelligence_report_id: number;
    report_title: string;
    summary_text: string | null;
    created_at: string | null;
  } | null;
};

export default function EnterpriseKnowledgePage() {
  const params = useParams();
  const domain = String(params.domain).toUpperCase();
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadKnowledge = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setWorkspace(await apiFetch<WorkspaceResponse>(`/domains/${domain}/workspace`));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Enterprise knowledge could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [domain]);

  useEffect(() => {
    void loadKnowledge();
  }, [loadKnowledge]);

  const name = workspace?.domain?.domain_name || domain;
  const concepts = workspace?.concepts || [];
  const findings = workspace?.findings || [];
  const evidenceCount = useMemo(
    () => concepts.reduce((total, concept) => total + (Number(concept.evidence_count) || 0), 0),
    [concepts],
  );

  return (
    <AppShell>
      <div className="sap-page knowledge-page">
        <header className="sap-page-header knowledge-page-header">
          <div className="sap-page-header-copy">
            <span className="sap-eyebrow">Enterprise Knowledge</span>
            <h1 className="sap-page-title">What Sapientia understands about {name}</h1>
            <p className="sap-page-description">
              Explore the business concepts and supporting evidence Sapientia has learned from the selected business area.
            </p>
          </div>
          <Link className="sap-button sap-button-primary" href={`/workspace/${domain}/ai`}>
            Ask AI Advisor
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </header>

        {error && (
          <div className="friendly-alert knowledge-error" role="alert">
            <CircleAlert size={18} aria-hidden="true" />
            <span>{error}</span>
            <button type="button" onClick={() => void loadKnowledge()}>Try again</button>
          </div>
        )}

        {loading ? (
          <div className="knowledge-loading-state" aria-live="polite">
            <span className="knowledge-loading-mark"><BookOpen size={22} aria-hidden="true" /></span>
            <div>
              <strong>Building the enterprise knowledge view</strong>
              <span>Loading concepts, evidence and connected findings…</span>
            </div>
          </div>
        ) : (
          <>
            <KnowledgeSummary
              concepts={workspace?.summary.enterprise_concepts || concepts.length}
              datasets={workspace?.summary.datasets || 0}
              evidence={evidenceCount}
              findings={workspace?.summary.findings || findings.length}
            />

            <section className="knowledge-overview-grid">
              <article className="knowledge-narrative-panel">
                <div className="knowledge-panel-heading">
                  <span className="knowledge-panel-icon"><Sparkles size={20} aria-hidden="true" /></span>
                  <div>
                    <span className="sap-eyebrow">Current enterprise narrative</span>
                    <h2>{workspace?.latest_report?.report_title || `${name} knowledge foundation`}</h2>
                  </div>
                </div>
                <p>
                  {workspace?.latest_report?.summary_text ||
                    `Sapientia has established a reusable knowledge foundation for ${name} from the available concepts and evidence.`}
                </p>
                {workspace?.latest_report ? (
                  <Link href={`/workspace/${domain}/reports`}>
                    Review supporting report <ArrowRight size={15} aria-hidden="true" />
                  </Link>
                ) : (
                  <Link href={`/workspace/${domain}/reports`}>
                    Explore intelligence <ArrowRight size={15} aria-hidden="true" />
                  </Link>
                )}
              </article>

              <article className="knowledge-health-panel">
                <div className="knowledge-panel-heading">
                  <span className="knowledge-panel-icon knowledge-panel-icon-secondary"><Network size={20} aria-hidden="true" /></span>
                  <div>
                    <span className="sap-eyebrow">Knowledge coverage</span>
                    <h2>Evidence-backed understanding</h2>
                  </div>
                </div>
                <dl>
                  <div><dt>Concepts with evidence</dt><dd>{concepts.filter((concept) => concept.evidence_count > 0).length}</dd></div>
                  <div><dt>Average evidence per concept</dt><dd>{concepts.length ? (evidenceCount / concepts.length).toFixed(1) : "0"}</dd></div>
                  <div><dt>Connected business findings</dt><dd>{findings.length}</dd></div>
                </dl>
              </article>
            </section>

            {concepts.length ? (
              <ConceptExplorer concepts={concepts} />
            ) : (
              <section className="knowledge-empty-state">
                <BookOpen size={26} aria-hidden="true" />
                <h2>No enterprise concepts yet</h2>
                <p>Complete the enterprise understanding process to create business concepts and evidence.</p>
              </section>
            )}

            {findings.length > 0 && (
              <section className="knowledge-findings-section">
                <div className="sap-section-header">
                  <div>
                    <span className="sap-eyebrow">Connected intelligence</span>
                    <h2 className="sap-section-title">What the knowledge is revealing</h2>
                    <p className="sap-section-description">Recent findings grounded in the selected business area.</p>
                  </div>
                  <Link className="sap-text-link" href={`/workspace/${domain}/reports`}>
                    View all intelligence <ArrowRight size={15} aria-hidden="true" />
                  </Link>
                </div>
                <div className="knowledge-finding-list">
                  {findings.slice(0, 4).map((finding) => (
                    <article key={finding.intelligence_finding_id}>
                      <span className={`knowledge-finding-icon ${finding.severity_level?.toLowerCase() === "high" ? "is-high" : ""}`}>
                        {finding.severity_level?.toLowerCase() === "high" ? <CircleAlert size={18} aria-hidden="true" /> : <FileText size={18} aria-hidden="true" />}
                      </span>
                      <div>
                        <div className="knowledge-finding-title-row">
                          <h3>{finding.finding_title}</h3>
                          {finding.severity_level && <span>{finding.severity_level}</span>}
                        </div>
                        <p>{finding.finding_description}</p>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
