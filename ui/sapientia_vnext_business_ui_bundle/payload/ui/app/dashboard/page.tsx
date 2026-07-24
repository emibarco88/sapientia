"use client";

import { ArrowRight, Building2, RefreshCw, Sparkles } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { healthLabel } from "@/components/vnext/DomainStatus";
import { apiFetch } from "@/lib/api";

type Domain = { business_domain_id?: number; domain_code: string; domain_name?: string; description?: string | null; datasets?: number; concepts?: number; intelligence_reports?: number; };
type Workspace = { summary?: { datasets?: number; enterprise_concepts?: number; findings?: number; reports?: number }; latest_report?: { report_title?: string; summary_text?: string | null; created_at?: string | null } | null; findings?: Array<{ severity_level?: string; finding_title?: string }> };
type DomainView = Domain & { workspace?: Workspace; failed?: boolean };

export default function EnterpriseOverviewPage() {
  const [domains, setDomains] = useState<DomainView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const list = await apiFetch<Domain[]>("/domains");
      const domainList = Array.isArray(list) ? list : [];
      const enriched = await Promise.all(domainList.map(async (domain) => {
        try {
          const workspace = await apiFetch<Workspace>(`/domains/${encodeURIComponent(domain.domain_code)}/workspace`);
          return { ...domain, workspace };
        } catch { return { ...domain, failed: true }; }
      }));
      setDomains(enriched);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Sapientia could not load the enterprise overview.");
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const totals = useMemo(() => domains.reduce((acc, domain) => ({
    domains: acc.domains + 1,
    sources: acc.sources + Number(domain.workspace?.summary?.datasets ?? domain.datasets ?? 0),
    findings: acc.findings + Number(domain.workspace?.summary?.findings ?? 0),
  }), { domains: 0, sources: 0, findings: 0 }), [domains]);

  return (
    <AppShell>
      <div className="vnext-page">
        <header className="vnext-hero">
          <div>
            <span className="vnext-eyebrow">The Enterprise Intelligence Platform</span>
            <h1>What part of your business would you like to understand?</h1>
            <p>Open a business domain to review its current state, important changes, risks, recommendations and supporting evidence.</p>
          </div>
          <button type="button" className="vnext-icon-button" onClick={() => void load()} aria-label="Refresh enterprise"><RefreshCw size={18} /></button>
        </header>

        <section className="vnext-enterprise-summary" aria-label="Enterprise summary">
          <div><span>Business domains</span><strong>{totals.domains}</strong></div>
          <div><span>Connected sources</span><strong>{totals.sources}</strong></div>
          <div><span>Current findings</span><strong>{totals.findings}</strong></div>
          <div className="vnext-summary-message"><Sparkles size={18} /><span>Sapientia turns enterprise knowledge into evidence-backed explanations.</span></div>
        </section>

        {error && <div className="vnext-alert">{error}</div>}
        {loading ? <div className="vnext-loading">Reading your enterprise…</div> : domains.length === 0 ? (
          <section className="vnext-empty"><Building2 size={28} /><h2>No business domains are available yet</h2><p>Connect and discover enterprise sources to establish the first business domain.</p><Link href="/sources">Manage sources</Link></section>
        ) : (
          <section>
            <div className="vnext-section-heading"><div><span className="vnext-eyebrow">Business domains</span><h2>Your enterprise at a glance</h2></div></div>
            <div className="vnext-domain-grid">
              {domains.map((domain) => {
                const findingCount = Number(domain.workspace?.summary?.findings ?? 0);
                const risks = domain.workspace?.findings?.filter((item) => ["HIGH", "CRITICAL"].includes(String(item.severity_level).toUpperCase())).length ?? 0;
                const status = healthLabel(findingCount, risks);
                const summary = domain.workspace?.latest_report?.summary_text || domain.description || "Sapientia is building a business understanding from the available enterprise evidence.";
                return (
                  <Link className="vnext-domain-card" href={`/domains/${encodeURIComponent(domain.domain_code.toUpperCase())}`} key={domain.domain_code}>
                    <div className="vnext-domain-card-top"><span className="vnext-domain-icon">{(domain.domain_name || domain.domain_code).slice(0, 1).toUpperCase()}</span><span className={`vnext-status vnext-status-${status.tone}`}>{status.label}</span></div>
                    <h3>{domain.domain_name || domain.domain_code}</h3>
                    <p>{summary}</p>
                    <div className="vnext-domain-card-meta"><span>{findingCount} findings</span><span>{risks} priority risks</span><span>{domain.workspace?.summary?.enterprise_concepts ?? domain.concepts ?? 0} understood concepts</span></div>
                    <span className="vnext-card-link">Open business domain <ArrowRight size={16} /></span>
                  </Link>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
