"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import Sidebar from "@/components/layout/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import PageHeader from "@/components/ui/PageHeader";
import MetricCard from "@/components/ui/MetricCard";
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

export default function WorkspacesPage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadWorkspaces() {
      setLoading(true);
      setError("");

      try {
        const data = await apiFetch("/domains");
        setDomains(Array.isArray(data) ? data : []);
      } catch (loadError) {
        console.error("Failed to load workspaces:", loadError);
        setError("Unable to load enterprise workspaces.");
        setDomains([]);
      } finally {
        setLoading(false);
      }
    }

    void loadWorkspaces();
  }, []);

  const totalDatasets = domains.reduce(
    (total, domain) => total + Number(domain.datasets || 0),
    0
  );

  const totalConcepts = domains.reduce(
    (total, domain) => total + Number(domain.concepts || 0),
    0
  );

  const totalReports = domains.reduce(
    (total, domain) =>
      total + Number(domain.intelligence_reports || 0),
    0
  );

  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <PageHeader
          label="Enterprise Workspaces"
          title="Choose a business area"
          description="Open a workspace to explore its enterprise knowledge, business concepts, intelligence findings, reports and AI capabilities."
        />

        <div className="mb-8 grid grid-cols-1 gap-5 xl:grid-cols-4">
          <MetricCard label="Business Domains" value={domains.length} />
          <MetricCard label="Datasets" value={totalDatasets} />
          <MetricCard label="Concepts" value={totalConcepts} />
          <MetricCard label="Reports" value={totalReports} />
        </div>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-10 text-slate-500">
            Loading enterprise workspaces...
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            {domains.map((domain) => (
              <Link
                key={domain.business_domain_id}
                href={`/workspace/${domain.domain_code}`}
                className="group rounded-3xl border border-slate-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:border-indigo-300 hover:shadow-lg"
              >
                <div className="flex items-start justify-between gap-5">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600">
                      Business Workspace
                    </p>

                    <h2 className="mt-3 text-3xl font-bold text-slate-950">
                      {domain.domain_code}
                    </h2>

                    <p className="mt-2 text-slate-500">
                      {domain.domain_name}
                    </p>
                  </div>

                  <Badge tone="green">AI Ready</Badge>
                </div>

                <div className="mt-8 grid grid-cols-3 gap-4">
                  <WorkspaceMetric
                    label="Datasets"
                    value={domain.datasets}
                  />
                  <WorkspaceMetric
                    label="Concepts"
                    value={domain.concepts}
                  />
                  <WorkspaceMetric
                    label="Reports"
                    value={domain.intelligence_reports}
                  />
                </div>

                <div className="mt-7 flex items-center justify-between border-t border-slate-100 pt-5">
                  <p className="text-sm text-slate-500">
                    Knowledge · Understanding · Intelligence · AI
                  </p>

                  <span className="text-sm font-semibold text-indigo-600 group-hover:translate-x-1">
                    Open workspace →
                  </span>
                </div>
              </Link>
            ))}

            {domains.length === 0 && (
              <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500 xl:col-span-2">
                No business workspaces are currently available.
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}

function WorkspaceMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-2xl bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-xl font-bold text-slate-950">
        {value ?? 0}
      </p>
    </div>
  );
}