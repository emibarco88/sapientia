"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import Sidebar from "@/components/layout/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import MetricCard from "@/components/ui/MetricCard";
import Panel from "@/components/ui/Panel";
import Badge from "@/components/ui/Badge";
import WorkspaceTabs from "@/components/workspace/WorkspaceTabs";
import { apiFetch } from "@/lib/api";

type WorkspaceSummary = {
  domain_code: string;
  domain_name: string;
  datasets: number;
  columns: number;
  semantic_columns: number;
  intelligence_links: number;
  enterprise_concepts: number;
  findings: number;
  reports: number;
};

type WorkspaceDataset = {
  dataset_id: number;
  name: string;
  source_type?: string | null;
  object_type: string | null;
  location: string | null;
  row_count: number | null;
  column_count: number | null;
  source_system_name: string | null;
  created_at: string | null;
};

type WorkspaceConcept = {
  enterprise_concept_id: number;
  concept_name: string;
  concept_type: string;
  concept_description: string | null;
  confidence_score: number | null;
  concept_status: string | null;
  evidence_count: number;
};

type WorkspaceFinding = {
  intelligence_finding_id: number;
  finding_type: string;
  finding_title: string;
  finding_description: string;
  finding_interpretation: string | null;
  confidence_score: number | null;
  severity_level: string | null;
  created_at: string | null;
};

type LatestReport = {
  intelligence_report_id: number;
  report_title: string;
  summary_text: string | null;
  created_at: string | null;
};

type WorkspaceResponse = {
  summary: WorkspaceSummary;
  datasets: WorkspaceDataset[];
  concepts: WorkspaceConcept[];
  findings: WorkspaceFinding[];
  latest_report: LatestReport | null;
};

export default function EnterpriseWorkspacePage() {
  const params = useParams();
  const domain = String(params.domain).toUpperCase();

  const [summary, setSummary] =
    useState<WorkspaceSummary | null>(null);

  const [datasets, setDatasets] =
    useState<WorkspaceDataset[]>([]);

  const [concepts, setConcepts] =
    useState<WorkspaceConcept[]>([]);

  const [findings, setFindings] =
    useState<WorkspaceFinding[]>([]);

  const [latestReport, setLatestReport] =
    useState<LatestReport | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadWorkspace() {
      setLoading(true);
      setError("");

      try {
        const data: WorkspaceResponse = await apiFetch(
          `/domains/${domain}/workspace`
        );

        setSummary(data.summary || null);
        setDatasets(
          Array.isArray(data.datasets) ? data.datasets : []
        );
        setConcepts(
          Array.isArray(data.concepts) ? data.concepts : []
        );
        setFindings(
          Array.isArray(data.findings) ? data.findings : []
        );
        setLatestReport(data.latest_report || null);
      } catch (loadError) {
        console.error(
          `Failed to load ${domain} workspace:`,
          loadError
        );

        setError(
          `Sapientia could not load the ${domain} workspace.`
        );

        setSummary(null);
        setDatasets([]);
        setConcepts([]);
        setFindings([]);
        setLatestReport(null);
      } finally {
        setLoading(false);
      }
    }

    void loadWorkspace();
  }, [domain]);

  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <Link
          href="/workspaces"
          className="text-sm font-medium text-indigo-600"
        >
          ← Choose another workspace
        </Link>

        <div className="mt-6 mb-8 rounded-[2rem] bg-gradient-to-br from-[#071333] via-[#111f4d] to-[#4f46e5] p-8 text-white shadow-xl">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="mb-3 text-sm uppercase tracking-[0.25em] text-indigo-200">
                Enterprise Workspace
              </p>

              <h1 className="text-5xl font-bold">{domain}</h1>

              <p className="mt-4 max-w-3xl text-indigo-100">
                {summary?.domain_name ||
                  `Enterprise knowledge, business understanding and intelligence for ${domain}.`}
              </p>
            </div>

            <Badge
              tone={
                Number(summary?.enterprise_concepts || 0) > 0
                  ? "green"
                  : "slate"
              }
            >
              {Number(summary?.enterprise_concepts || 0) > 0
                ? "AI Ready"
                : "Awaiting Intelligence"}
            </Badge>
          </div>
        </div>

        <WorkspaceTabs domain={domain} />

        {error && (
          <div className="mb-8 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <WorkspaceLoading />
        ) : (
          <>
            <section id="overview" className="mb-10">
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
                <MetricCard
                  label="Datasets"
                  value={summary?.datasets ?? 0}
                />

                <MetricCard
                  label="Columns"
                  value={summary?.columns ?? 0}
                />

                <MetricCard
                  label="Enterprise Concepts"
                  value={summary?.enterprise_concepts ?? 0}
                />

                <MetricCard
                  label="Intelligence Findings"
                  value={summary?.findings ?? 0}
                />
              </div>
            </section>

            <section className="mb-10 grid grid-cols-1 gap-6 xl:grid-cols-2">
              <Panel
                title="Enterprise Narrative"
                subtitle={`What Sapientia currently understands about ${domain}.`}
              >
                {latestReport?.summary_text ? (
                  <>
                    <p className="whitespace-pre-wrap leading-7 text-slate-700">
                      {latestReport.summary_text}
                    </p>

                    <p className="mt-5 text-xs text-slate-400">
                      Generated by report{" "}
                      {latestReport.intelligence_report_id}
                      {latestReport.created_at
                        ? ` on ${new Date(
                            latestReport.created_at
                          ).toLocaleString()}`
                        : ""}
                    </p>
                  </>
                ) : (
                  <p className="leading-7 text-slate-700">
                    Sapientia has discovered{" "}
                    <strong>{summary?.datasets ?? 0}</strong>{" "}
                    dataset(s),{" "}
                    <strong>
                      {summary?.semantic_columns ?? 0}
                    </strong>{" "}
                    semantic classification(s),{" "}
                    <strong>
                      {summary?.enterprise_concepts ?? 0}
                    </strong>{" "}
                    enterprise concept(s), and{" "}
                    <strong>{summary?.findings ?? 0}</strong>{" "}
                    intelligence finding(s) for {domain}.
                  </p>
                )}
              </Panel>

              <Panel
                title="AI Workspace"
                subtitle={`Ask grounded questions about ${domain}.`}
              >
                <div className="rounded-2xl bg-gradient-to-br from-indigo-50 to-fuchsia-50 p-6">
                  <h3 className="text-lg font-bold text-slate-950">
                    Ask Sapientia about {domain}
                  </h3>

                  <p className="mt-2 leading-6 text-slate-600">
                    Answers use enterprise concepts, findings,
                    fusion links and persisted intelligence context.
                  </p>
                </div>

                <Link
                  href={`/workspace/${domain}/ai`}
                  className="mt-5 block rounded-xl bg-indigo-600 py-3 text-center font-semibold text-white hover:bg-indigo-500"
                >
                  Open AI Advisor
                </Link>
              </Panel>
            </section>

            <section id="sources" className="mb-10">
              <Panel
                title="Enterprise Datasets"
                subtitle={`Data assets currently associated with the ${domain} business domain.`}
              >
                {datasets.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {datasets.map((dataset) => (
                      <div
                        key={dataset.dataset_id}
                        className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-indigo-300"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <h3 className="font-bold text-slate-950">
                              {dataset.name}
                            </h3>

                            <p className="mt-1 text-sm text-slate-500">
                              {dataset.source_system_name ||
                                dataset.source_type ||
                                "Enterprise source"}
                            </p>
                          </div>

                          <Badge tone="slate">
                            {dataset.object_type || "DATASET"}
                          </Badge>
                        </div>

                        <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
                          <DatasetMetric
                            label="Columns"
                            value={dataset.column_count ?? 0}
                          />

                          <DatasetMetric
                            label="Rows"
                            value={dataset.row_count ?? "N/A"}
                          />
                        </div>

                        {dataset.location && (
                          <p className="mt-4 break-all text-xs text-slate-400">
                            {dataset.location}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No datasets found"
                    description={`No datasets are currently assigned to the ${domain} business domain.`}
                  />
                )}
              </Panel>
            </section>

            <section id="understanding" className="mb-10">
              <Panel
                title="Enterprise Understanding"
                subtitle="Business concepts consolidated from semantic, knowledge and fusion evidence."
              >
                {concepts.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {concepts.map((concept) => (
                      <div
                        key={concept.enterprise_concept_id}
                        className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-indigo-300"
                      >
                        <div className="mb-3 flex items-start justify-between gap-4">
                          <div>
                            <h3 className="text-xl font-bold text-slate-950">
                              {concept.concept_name}
                            </h3>

                            <p className="mt-1 text-sm font-medium text-indigo-600">
                              {concept.concept_type}
                            </p>
                          </div>

                          <Badge tone="indigo">
                            {formatConfidence(
                              concept.confidence_score
                            )}
                          </Badge>
                        </div>

                        <p className="leading-6 text-slate-600">
                          {concept.concept_description ||
                            "No business description is currently available."}
                        </p>

                        <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
                          <span>
                            Evidence: {concept.evidence_count ?? 0}
                          </span>

                          <span>
                            {concept.concept_status || "ACTIVE"}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No enterprise concepts found"
                    description={`Run the Enterprise Concept Engine for ${domain} to build business understanding.`}
                  />
                )}
              </Panel>
            </section>

            <section id="intelligence" className="mb-10">
              <Panel
                title="Enterprise Intelligence"
                subtitle="Findings generated from Sapientia's intelligence layer."
              >
                {findings.length > 0 ? (
                  <div className="space-y-4">
                    {findings.map((finding) => (
                      <div
                        key={finding.intelligence_finding_id}
                        className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
                      >
                        <div className="mb-2 flex justify-between gap-4">
                          <p className="text-sm font-semibold text-indigo-600">
                            {finding.finding_type}
                          </p>

                          <Badge tone="slate">
                            {finding.severity_level || "INFO"}
                          </Badge>
                        </div>

                        <h3 className="font-bold text-slate-950">
                          {finding.finding_title}
                        </h3>

                        <p className="mt-2 leading-6 text-slate-600">
                          {finding.finding_description}
                        </p>

                        {finding.finding_interpretation && (
                          <p className="mt-3 text-sm leading-6 text-slate-500">
                            <span className="font-semibold">
                              Why it matters:
                            </span>{" "}
                            {finding.finding_interpretation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyState
                    title="No intelligence findings found"
                    description={`Generate an Enterprise Intelligence report for ${domain} to populate this section.`}
                  />
                )}
              </Panel>
            </section>
          </>
        )}
      </section>
    </main>
  );
}

function DatasetMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className="mt-1 font-semibold text-slate-900">
        {value}
      </p>
    </div>
  );
}

function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
      <h3 className="font-bold text-slate-900">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
}

function WorkspaceLoading() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className="h-36 animate-pulse rounded-2xl bg-white"
          />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {[1, 2].map((item) => (
          <div
            key={item}
            className="h-64 animate-pulse rounded-3xl bg-white"
          />
        ))}
      </div>
    </div>
  );
}

function formatConfidence(
  confidence: number | null
): string {
  if (confidence === null || confidence === undefined) {
    return "N/A";
  }

  const numericConfidence = Number(confidence);

  if (numericConfidence <= 1) {
    return `${Math.round(numericConfidence * 100)}%`;
  }

  return `${Math.round(numericConfidence)}%`;
}