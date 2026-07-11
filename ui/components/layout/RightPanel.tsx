"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import Badge from "@/components/ui/Badge";
import { apiFetch } from "@/lib/api";

type Domain = {
  business_domain_id: number;
  domain_code: string;
  domain_name: string;
  datasets: number;
  concepts: number;
  intelligence_reports: number;
};

type Connector = {
  connector_id: number;
  connector_name: string;
  connector_type_name: string;
  connector_status: string;
  datasets: number;
  columns: number;
  last_discovered_at: string | null;
};

type WorkspaceResponse = {
  summary?: {
    domain_code?: string;
    domain_name?: string;
    datasets?: number;
    columns?: number;
    semantic_columns?: number;
    intelligence_links?: number;
    enterprise_concepts?: number;
    findings?: number;
  };
  concepts?: Array<{
    enterprise_concept_id: number;
    concept_name: string;
    concept_type: string;
    confidence_score: number | null;
  }>;
  findings?: Array<{
    intelligence_finding_id: number;
    finding_type: string;
    finding_title: string;
    severity_level: string | null;
  }>;
};

export default function RightPanel() {
  const pathname = usePathname();

  const [domains, setDomains] = useState<Domain[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const domain = useMemo(() => {
    const match = pathname.match(/^\/workspace\/([^/]+)/);
    return match ? decodeURIComponent(match[1]).toUpperCase() : null;
  }, [pathname]);

  const pageType = useMemo(() => {
    if (pathname.startsWith("/sources")) return "connectors";
    if (pathname === "/workspaces") return "workspaces";
    if (pathname.startsWith("/workspace/") && pathname.endsWith("/ai")) {
      return "ai";
    }
    if (pathname.startsWith("/workspace/")) return "workspace";
    return "dashboard";
  }, [pathname]);

  useEffect(() => {
    async function loadContext() {
      setLoading(true);
      setWorkspace(null);

      try {
        if (pageType === "connectors") {
          const connectorData = await apiFetch("/sources");
          setConnectors(Array.isArray(connectorData) ? connectorData : []);
          return;
        }

        if (pageType === "workspace" || pageType === "ai") {
          if (!domain) return;

          const workspaceData = await apiFetch(
            `/domains/${domain}/workspace`
          );

          setWorkspace(workspaceData || null);
          return;
        }

        const [domainData, connectorData] = await Promise.all([
          apiFetch("/domains"),
          apiFetch("/sources"),
        ]);

        setDomains(Array.isArray(domainData) ? domainData : []);
        setConnectors(Array.isArray(connectorData) ? connectorData : []);
      } catch (error) {
        console.error("Failed to load context panel:", error);
      } finally {
        setLoading(false);
      }
    }

    void loadContext();
  }, [domain, pageType]);

  return (
    <aside className="fixed right-0 top-0 z-30 h-screen w-96 overflow-y-auto border-l border-slate-200 bg-white p-6">
      {loading ? (
        <ContextLoading />
      ) : (
        <>
          {pageType === "dashboard" && (
            <DashboardContext
              domains={domains}
              connectors={connectors}
            />
          )}

          {pageType === "workspaces" && (
            <WorkspacesContext domains={domains} />
          )}

          {pageType === "connectors" && (
            <ConnectorsContext connectors={connectors} />
          )}

          {pageType === "workspace" && domain && (
            <WorkspaceContext
              domain={domain}
              workspace={workspace}
            />
          )}

          {pageType === "ai" && domain && (
            <AIContext
              domain={domain}
              workspace={workspace}
            />
          )}
        </>
      )}
    </aside>
  );
}

function DashboardContext({
  domains,
  connectors,
}: {
  domains: Domain[];
  connectors: Connector[];
}) {
  const connectedConnectors = connectors.filter(
    (connector) => connector.connector_status === "CONNECTED"
  ).length;

  return (
    <>
      <ContextHeader
        title="Platform Overview"
        description="Live information from the Sapientia Enterprise Knowledge Repository."
      />

      <div className="mb-8 grid grid-cols-2 gap-3">
        <ContextMetric label="Workspaces" value={domains.length} />
        <ContextMetric label="Connectors" value={connectors.length} />
        <ContextMetric label="Connected" value={connectedConnectors} />
        <ContextMetric
          label="Datasets"
          value={domains.reduce(
            (total, item) => total + Number(item.datasets || 0),
            0
          )}
        />
      </div>

      <ContextSection title="Business Workspaces">
        <div className="space-y-3">
          {domains.slice(0, 6).map((domain) => (
            <Link
              key={domain.business_domain_id}
              href={`/workspace/${domain.domain_code}`}
              className="block rounded-2xl border border-slate-200 p-4 hover:border-indigo-300"
            >
              <p className="font-semibold text-slate-950">
                {domain.domain_code}
              </p>
              <p className="mt-1 text-sm text-slate-500">
                {domain.datasets} datasets · {domain.concepts} concepts
              </p>
            </Link>
          ))}
        </div>
      </ContextSection>

      <Link
        href="/workspaces"
        className="mt-6 block rounded-xl bg-indigo-600 py-3 text-center text-sm font-semibold text-white hover:bg-indigo-500"
      >
        Open Workspaces
      </Link>
    </>
  );
}

function WorkspacesContext({ domains }: { domains: Domain[] }) {
  return (
    <>
      <ContextHeader
        title="Enterprise Workspaces"
        description="Choose the business area you want Sapientia to explain."
      />

      <ContextSection title="Available Domains">
        <div className="space-y-3">
          {domains.map((domain) => (
            <Link
              key={domain.business_domain_id}
              href={`/workspace/${domain.domain_code}`}
              className="block rounded-2xl border border-slate-200 p-4 hover:border-indigo-300"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-950">
                    {domain.domain_code}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {domain.domain_name}
                  </p>
                </div>

                <Badge tone="indigo">{domain.concepts} concepts</Badge>
              </div>
            </Link>
          ))}

          {domains.length === 0 && (
            <EmptyContext text="No business domains were found." />
          )}
        </div>
      </ContextSection>
    </>
  );
}

function ConnectorsContext({
  connectors,
}: {
  connectors: Connector[];
}) {
  const connected = connectors.filter(
    (connector) => connector.connector_status === "CONNECTED"
  ).length;

  return (
    <>
      <ContextHeader
        title="Connector Health"
        description="Live connector status and discovery information."
      />

      <div className="mb-8 grid grid-cols-2 gap-3">
        <ContextMetric label="Configured" value={connectors.length} />
        <ContextMetric label="Connected" value={connected} />
        <ContextMetric
          label="Datasets"
          value={connectors.reduce(
            (total, connector) =>
              total + Number(connector.datasets || 0),
            0
          )}
        />
        <ContextMetric
          label="Columns"
          value={connectors.reduce(
            (total, connector) =>
              total + Number(connector.columns || 0),
            0
          )}
        />
      </div>

      <ContextSection title="Configured Connectors">
        <div className="space-y-3">
          {connectors.map((connector) => (
            <div
              key={connector.connector_id}
              className="rounded-2xl border border-slate-200 p-4"
            >
              <div className="flex justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-950">
                    {connector.connector_name}
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    {connector.connector_type_name}
                  </p>
                </div>

                <Badge
                  tone={
                    connector.connector_status === "CONNECTED"
                      ? "green"
                      : "slate"
                  }
                >
                  {connector.connector_status}
                </Badge>
              </div>

              <p className="mt-3 text-xs text-slate-400">
                Last discovery:{" "}
                {connector.last_discovered_at
                  ? new Date(
                      connector.last_discovered_at
                    ).toLocaleString()
                  : "Not yet discovered"}
              </p>
            </div>
          ))}

          {connectors.length === 0 && (
            <EmptyContext text="No connectors have been configured." />
          )}
        </div>
      </ContextSection>
    </>
  );
}

function WorkspaceContext({
  domain,
  workspace,
}: {
  domain: string;
  workspace: WorkspaceResponse | null;
}) {
  const summary = workspace?.summary || {};
  const findings = workspace?.findings || [];

  return (
    <>
      <ContextHeader
        title={`${domain} Context`}
        description="Current business understanding for this enterprise workspace."
      />

      <div className="mb-8 grid grid-cols-2 gap-3">
        <ContextMetric label="Datasets" value={summary.datasets ?? 0} />
        <ContextMetric
          label="Concepts"
          value={summary.enterprise_concepts ?? 0}
        />
        <ContextMetric label="Findings" value={summary.findings ?? 0} />
        <ContextMetric
          label="Semantic"
          value={summary.semantic_columns ?? 0}
        />
      </div>

      <ContextSection title="Latest Intelligence">
        <div className="space-y-3">
          {findings.slice(0, 5).map((finding) => (
            <div
              key={finding.intelligence_finding_id}
              className="rounded-2xl bg-slate-50 p-4"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                {finding.finding_type}
              </p>
              <p className="mt-2 text-sm font-medium text-slate-900">
                {finding.finding_title}
              </p>
            </div>
          ))}

          {findings.length === 0 && (
            <EmptyContext text="No intelligence findings are available." />
          )}
        </div>
      </ContextSection>

      <Link
        href={`/workspace/${domain}/ai`}
        className="mt-6 block rounded-xl bg-indigo-600 py-3 text-center text-sm font-semibold text-white hover:bg-indigo-500"
      >
        Ask Sapientia
      </Link>
    </>
  );
}

function AIContext({
  domain,
  workspace,
}: {
  domain: string;
  workspace: WorkspaceResponse | null;
}) {
  const concepts = workspace?.concepts || [];
  const findings = workspace?.findings || [];

  return (
    <>
      <ContextHeader
        title={`${domain} AI Context`}
        description="Grounding information available to the Sapientia AI Advisor."
      />

      <div className="mb-8 grid grid-cols-2 gap-3">
        <ContextMetric label="Concepts" value={concepts.length} />
        <ContextMetric label="Findings" value={findings.length} />
      </div>

      <ContextSection title="Relevant Concepts">
        <div className="space-y-3">
          {concepts.slice(0, 6).map((concept) => (
            <div
              key={concept.enterprise_concept_id}
              className="rounded-2xl border border-slate-200 p-4"
            >
              <p className="font-semibold text-slate-950">
                {concept.concept_name}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {concept.concept_type}
              </p>
            </div>
          ))}

          {concepts.length === 0 && (
            <EmptyContext text="No concepts are available for grounding." />
          )}
        </div>
      </ContextSection>

      <Link
        href={`/workspace/${domain}`}
        className="mt-6 block rounded-xl border border-slate-200 py-3 text-center text-sm font-semibold text-slate-700 hover:border-indigo-300"
      >
        Return to Workspace
      </Link>
    </>
  );
}

function ContextHeader({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mb-7">
      <h2 className="text-2xl font-bold text-slate-950">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
}

function ContextSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-7">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-500">
        {title}
      </h3>
      {children}
    </section>
  );
}

function ContextMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
    </div>
  );
}

function EmptyContext({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 p-5 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function ContextLoading() {
  return (
    <div>
      <div className="mb-4 h-8 animate-pulse rounded-lg bg-slate-200" />
      <div className="mb-8 h-12 animate-pulse rounded-lg bg-slate-100" />

      <div className="grid grid-cols-2 gap-3">
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className="h-24 animate-pulse rounded-2xl bg-slate-100"
          />
        ))}
      </div>
    </div>
  );
}