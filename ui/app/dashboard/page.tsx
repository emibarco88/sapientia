"use client";

import {
  ArrowRight,
  Building2,
  CheckCircle2,
  FileText,
  MessageSquareText,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import EnterpriseJourney from "@/components/enterprise/EnterpriseJourney";
import Sidebar from "@/components/layout/Sidebar";
import { apiFetch } from "@/lib/api";

type Domain = {
  business_domain_id: number;
  domain_code: string;
  domain_name: string;
  datasets: number;
  concepts: number;
  intelligence_reports: number;
};

type WorkspaceSummary = {
  datasets: number;
  enterprise_concepts: number;
  findings: number;
  reports: number;
};

type LatestReport = {
  intelligence_report_id: number;
  report_title: string;
  summary_text: string | null;
  created_at: string | null;
};

type Finding = {
  intelligence_finding_id: number;
  finding_title: string;
  finding_description: string;
  created_at: string | null;
};

type WorkspaceResponse = {
  domain?: {
    domain_code: string;
    domain_name: string;
    description: string | null;
  };
  summary: WorkspaceSummary;
  findings: Finding[];
  latest_report: LatestReport | null;
};

export default function EnterpriseOverviewPage() {
  const router = useRouter();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const activeDomain = domains[0] ?? null;
  const activeDomainCode = activeDomain?.domain_code?.toUpperCase() ?? "";

  const loadEnterprise = useCallback(async (showRefresh = false) => {
    if (showRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");

    try {
      const domainData = await apiFetch<Domain[]>("/domains");
      const domainList = Array.isArray(domainData) ? domainData : [];
      setDomains(domainList);

      const firstDomain = domainList[0];
      if (!firstDomain) {
        setWorkspace(null);
        return;
      }

      const workspaceData = await apiFetch<WorkspaceResponse>(
        `/domains/${firstDomain.domain_code}/workspace`
      );
      setWorkspace(workspaceData);
    } catch (cause) {
      console.error("Failed to load enterprise overview:", cause);
      setError(
        cause instanceof Error
          ? cause.message
          : "Sapientia could not load your enterprise."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadEnterprise();
  }, [loadEnterprise]);

  const totalSources = useMemo(
    () => domains.reduce((total, domain) => total + Number(domain.datasets || 0), 0),
    [domains]
  );

  const totalConcepts = useMemo(
    () => domains.reduce((total, domain) => total + Number(domain.concepts || 0), 0),
    [domains]
  );

  const totalReports = useMemo(
    () =>
      domains.reduce(
        (total, domain) => total + Number(domain.intelligence_reports || 0),
        0
      ),
    [domains]
  );

  const connected = totalSources > 0;
  const discovered = Boolean(workspace && Number(workspace.summary.datasets || 0) > 0);
  const understood = totalConcepts > 0;
  const intelligenceReady = Boolean(
    totalReports > 0 ||
      Number(workspace?.summary.findings || 0) > 0 ||
      workspace?.latest_report
  );

  const enterpriseName = "Your Enterprise";
  const latestFinding = workspace?.findings?.[0] ?? null;

  if (loading) {
    return (
      <main className="app-shell">
        <Sidebar />
        <section className="app-content">
          <div className="overview-loading" aria-live="polite">
            <span className="loading-orb">
              <Sparkles size={22} aria-hidden="true" />
            </span>
            <h1>Preparing your enterprise</h1>
            <p>Sapientia is bringing your business knowledge together.</p>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <Sidebar />

      <section className="app-content">
        <header className="overview-header">
          <div>
            <span className="eyebrow">Enterprise</span>
            <h1>{enterpriseName}</h1>
            <p>
              A clear view of what Sapientia understands and what you can do next.
            </p>
          </div>

          <button
            className="quiet-button"
            disabled={refreshing}
            onClick={() => void loadEnterprise(true)}
            type="button"
          >
            <RefreshCw
              className={refreshing ? "spin" : ""}
              size={17}
              aria-hidden="true"
            />
            {refreshing ? "Refreshing" : "Refresh"}
          </button>
        </header>

        {error && (
          <div className="friendly-alert" role="alert">
            <strong>We could not refresh the enterprise overview.</strong>
            <span>{error}</span>
          </div>
        )}

        {!activeDomain ? (
          <section className="empty-enterprise-card">
            <div className="empty-enterprise-icon">
              <Building2 size={28} aria-hidden="true" />
            </div>
            <span className="eyebrow">Welcome to Sapientia</span>
            <h2>Start building your enterprise intelligence</h2>
            <p>
              Connect your first business source. Sapientia will then discover your
              information, learn its meaning and prepare intelligence you can explore.
            </p>
            <Link className="primary-action" href="/sources">
              Connect a data source
              <ArrowRight size={17} aria-hidden="true" />
            </Link>
          </section>
        ) : (
          <>
            <section className="enterprise-hero">
              <div className="enterprise-hero-copy">
                <div className="ready-pill">
                  <CheckCircle2 size={16} aria-hidden="true" />
                  {intelligenceReady ? "Enterprise ready" : "Enterprise in progress"}
                </div>

                <h2>
                  {intelligenceReady
                    ? "Your enterprise intelligence is ready to explore."
                    : "Sapientia is learning how your business works."}
                </h2>

                <p>
                  {intelligenceReady
                    ? "Ask business questions, review evidence-backed findings and explore what Sapientia has learned."
                    : "Continue the guided journey to turn connected business information into useful intelligence."}
                </p>

                <div className="hero-actions">
                  {intelligenceReady ? (
                    <Link
                      className="primary-action"
                      href={`/workspace/${activeDomainCode}/ai`}
                    >
                      Open Enterprise Intelligence Agent
                      <ArrowRight size={17} aria-hidden="true" />
                    </Link>
                  ) : (
                    <Link className="primary-action" href="/sources">
                      Continue setup
                      <ArrowRight size={17} aria-hidden="true" />
                    </Link>
                  )}

                  <Link
                    className="secondary-action"
                    href={`/workspace/${activeDomainCode}`}
                  >
                    View enterprise
                  </Link>
                </div>
              </div>

              <div className="agent-preview" aria-label="Enterprise Intelligence Agent">
                <span className="agent-preview-icon">
                  <MessageSquareText size={21} aria-hidden="true" />
                </span>
                <div>
                  <span>Enterprise Intelligence Agent</span>
                  <strong>{intelligenceReady ? "Ready" : "Preparing"}</strong>
                  <p>
                    {intelligenceReady
                      ? "Grounded in your enterprise knowledge and supporting evidence."
                      : "It will become available when enterprise intelligence is ready."}
                  </p>
                </div>
              </div>
            </section>

            <div className="overview-grid">
              <section className="surface-card journey-card">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">Guided setup</span>
                    <h2>Enterprise journey</h2>
                  </div>
                  <span className="section-supporting-text">
                    {intelligenceReady ? "Complete" : "In progress"}
                  </span>
                </div>

                <EnterpriseJourney
                  connected={connected}
                  discovered={discovered}
                  understood={understood}
                  intelligenceReady={intelligenceReady}
                />
              </section>

              <aside className="overview-side-column">
                <section className="surface-card">
                  <div className="section-heading compact-heading">
                    <div>
                      <span className="eyebrow">Enterprise knowledge</span>
                      <h2>What Sapientia understands</h2>
                    </div>
                  </div>

                  <div className="knowledge-list">
                    {domains.map((domain) => (
                      <Link
                        className="knowledge-item"
                        href={`/workspace/${domain.domain_code}`}
                        key={domain.business_domain_id}
                      >
                        <span className="knowledge-icon">
                          <Building2 size={17} aria-hidden="true" />
                        </span>
                        <span>
                          <strong>{domain.domain_name || domain.domain_code}</strong>
                          <small>
                            {Number(domain.concepts || 0) > 0
                              ? "Business knowledge available"
                              : "Information connected"}
                          </small>
                        </span>
                        <ArrowRight size={16} aria-hidden="true" />
                      </Link>
                    ))}
                  </div>
                </section>

                <section className="surface-card latest-card">
                  <div className="section-heading compact-heading">
                    <div>
                      <span className="eyebrow">Latest intelligence</span>
                      <h2>What changed recently</h2>
                    </div>
                  </div>

                  {latestFinding ? (
                    <div className="latest-intelligence">
                      <span className="latest-icon">
                        <Sparkles size={18} aria-hidden="true" />
                      </span>
                      <div>
                        <strong>{latestFinding.finding_title}</strong>
                        <p>{latestFinding.finding_description}</p>
                      </div>
                    </div>
                  ) : workspace?.latest_report ? (
                    <div className="latest-intelligence">
                      <span className="latest-icon">
                        <FileText size={18} aria-hidden="true" />
                      </span>
                      <div>
                        <strong>{workspace.latest_report.report_title}</strong>
                        <p>
                          {workspace.latest_report.summary_text ||
                            "A new enterprise intelligence report is available."}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="gentle-empty-state">
                      <p>
                        New findings will appear here once enterprise intelligence has
                        been generated.
                      </p>
                    </div>
                  )}

                  {workspace?.latest_report && (
                    <Link
                      className="text-action"
                      href={`/workspace/${activeDomainCode}/reports/${workspace.latest_report.intelligence_report_id}`}
                    >
                      Open latest report
                      <ArrowRight size={16} aria-hidden="true" />
                    </Link>
                  )}
                </section>
              </aside>
            </div>
          </>
        )}
      </section>
    </main>
  );
}
