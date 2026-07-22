"use client";

import Link from "next/link";

import {
  ArrowRight,
  BrainCircuit,
  FileText,
  Sparkles,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { useParams } from "next/navigation";

import Sidebar from "@/components/layout/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import WorkspaceTabs from "@/components/workspace/WorkspaceTabs";

import Badge from "@/components/ui/Badge";
import MetricCard from "@/components/ui/MetricCard";
import Panel from "@/components/ui/Panel";

import { apiFetch } from "@/lib/api";


type WorkspaceDomain = {
  business_domain_id: number;
  domain_code: string;
  domain_name: string;
  description: string | null;
  industry: string | null;
};


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
  intelligence_report_id?: number | null;
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
  domain?: WorkspaceDomain;

  summary: WorkspaceSummary;

  datasets: WorkspaceDataset[];
  concepts: WorkspaceConcept[];
  findings: WorkspaceFinding[];

  latest_report:
    LatestReport | null;
};


export default function EnterpriseWorkspacePage() {
  const params = useParams();

  const domain = String(
    params.domain
  ).toUpperCase();

  const [
    workspace,
    setWorkspace,
  ] = useState<
    WorkspaceResponse | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  const loadWorkspace =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const response =
          await apiFetch<WorkspaceResponse>(
            `/domains/${domain}/workspace`
          );

        setWorkspace(response);

      } catch (cause) {
        console.error(
          `Failed to load ${domain} workspace:`,
          cause
        );

        setWorkspace(null);

        setError(
          getMessage(
            cause,
            `Sapientia could not load the ${domain} workspace.`
          )
        );

      } finally {
        setLoading(false);
      }
    }, [domain]);


  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);


  const summary =
    workspace?.summary;

  const datasets =
    workspace?.datasets || [];

  const concepts =
    workspace?.concepts || [];

  const findings =
    workspace?.findings || [];

  const latestReport =
    workspace?.latest_report;

  const workspaceName =
    workspace?.domain?.domain_name
    || summary?.domain_name
    || domain;

  const intelligenceReady =
    Boolean(
      latestReport
      || Number(
        summary?.findings || 0
      ) > 0
    );


  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <Link
          href="/workspaces"
          className="text-sm font-semibold text-indigo-600 hover:text-indigo-500"
        >
          ← Choose another workspace
        </Link>

        <div className="mb-8 mt-6 rounded-[2rem] bg-gradient-to-br from-[#071333] via-[#111f4d] to-[#4f46e5] p-8 text-white shadow-xl">
          <div className="flex flex-col justify-between gap-8 xl:flex-row xl:items-start">
            <div>
              <p className="mb-3 text-sm uppercase tracking-[0.25em] text-indigo-200">
                Enterprise Workspace
              </p>

              <h1 className="text-5xl font-bold">
                {workspaceName}
              </h1>

              <p className="mt-4 max-w-3xl text-lg leading-7 text-indigo-100">
                {workspace?.domain?.description
                  || (
                    "Enterprise assets, business "
                    + "understanding, intelligence "
                    + "and AI-ready context."
                  )}
              </p>
            </div>

            <div className="flex flex-col items-start gap-3 xl:items-end">
              <Badge
                tone={
                  intelligenceReady
                    ? "green"
                    : "slate"
                }
              >
                {intelligenceReady
                  ? "Intelligence Ready"
                  : "Building Intelligence"}
              </Badge>

              {latestReport && (
                <Link
                  href={
                    `/workspace/${domain}/reports/${latestReport.intelligence_report_id}`
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2.5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/20"
                >
                  Open latest report

                  <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </div>
          </div>
        </div>

        <WorkspaceTabs
          domain={domain}
        />

        {error && (
          <div className="mb-8 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <WorkspaceLoading />
        ) : !workspace ? (
          <EmptyState
            title="Workspace unavailable"
            description="The workspace could not be loaded."
          />
        ) : (
          <>
            <section className="mb-10">
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
                <MetricCard
                  label="Active Datasets"
                  value={
                    summary?.datasets ?? 0
                  }
                />

                <MetricCard
                  label="Semantic Columns"
                  value={
                    summary?.semantic_columns
                    ?? 0
                  }
                />

                <MetricCard
                  label="Enterprise Concepts"
                  value={
                    summary?.enterprise_concepts
                    ?? 0
                  }
                />

                <MetricCard
                  label="Intelligence Findings"
                  value={
                    summary?.findings ?? 0
                  }
                />
              </div>
            </section>

            <section className="mb-10 grid grid-cols-1 gap-6 xl:grid-cols-3">
              <div className="xl:col-span-2">
                <Panel
                  title="Enterprise Narrative"
                  subtitle={`What Sapientia currently understands about ${workspaceName}.`}
                >
                  {latestReport ? (
                    <>
                      <div className="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-fuchsia-50 p-6">
                        <div className="flex items-start gap-4">
                          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white">
                            <Sparkles className="h-5 w-5" />
                          </div>

                          <div>
                            <h3 className="text-xl font-bold text-slate-950">
                              {
                                latestReport.report_title
                              }
                            </h3>

                            <p className="mt-3 whitespace-pre-wrap leading-7 text-slate-700">
                              {
                                latestReport.summary_text
                                || "No narrative summary is available."
                              }
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
                        <p className="text-sm text-slate-400">
                          Generated{" "}
                          {
                            formatDateTime(
                              latestReport.created_at
                            )
                          }
                        </p>

                        <Link
                          href={
                            `/workspace/${domain}/reports/${latestReport.intelligence_report_id}`
                          }
                          className="inline-flex items-center gap-2 font-semibold text-indigo-600 hover:text-indigo-500"
                        >
                          Explore report and evidence

                          <ArrowRight className="h-4 w-4" />
                        </Link>
                      </div>
                    </>
                  ) : (
                    <EmptyState
                      title="No intelligence report yet"
                      description="Generate Enterprise Intelligence from an active connector to create the first business narrative."
                    />
                  )}
                </Panel>
              </div>

              <Panel
                title="Workspace Actions"
                subtitle="Continue exploring this business domain."
              >
                <div className="space-y-3">
                  <WorkspaceAction
                    href={
                      `/workspace/${domain}/reports`
                    }
                    icon={
                      <FileText className="h-5 w-5" />
                    }
                    title="Intelligence Reports"
                    description={`${summary?.reports ?? 0} generated report(s)`}
                  />

                  <WorkspaceAction
                    href={
                      `/workspace/${domain}/ai`
                    }
                    icon={
                      <BrainCircuit className="h-5 w-5" />
                    }
                    title="Ask Sapientia"
                    description="Ask grounded questions using concepts, findings and reports."
                  />
                </div>
              </Panel>
            </section>

            <section
              id="assets"
              className="mb-10"
            >
              <Panel
                title="Enterprise Assets"
                subtitle={`Current data assets associated with ${workspaceName}.`}
              >
                {datasets.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {datasets.map(
                      (dataset) => (
                        <div
                          key={
                            dataset.dataset_id
                          }
                          className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-indigo-300"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h3 className="font-bold text-slate-950">
                                {
                                  dataset.name
                                }
                              </h3>

                              <p className="mt-1 text-sm text-slate-500">
                                {
                                  dataset.source_system_name
                                  || dataset.source_type
                                  || "Enterprise source"
                                }
                              </p>
                            </div>

                            <Badge tone="slate">
                              {
                                dataset.object_type
                                || "DATASET"
                              }
                            </Badge>
                          </div>

                          <div className="mt-5 grid grid-cols-2 gap-3">
                            <DatasetMetric
                              label="Columns"
                              value={
                                dataset.column_count
                                ?? 0
                              }
                            />

                            <DatasetMetric
                              label="Rows"
                              value={
                                dataset.row_count
                                ?? "N/A"
                              }
                            />
                          </div>

                          {dataset.location && (
                            <p className="mt-4 break-all text-xs text-slate-400">
                              {
                                dataset.location
                              }
                            </p>
                          )}
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <EmptyState
                    title="No active datasets"
                    description="Discover assets from an Enterprise Connector assigned to this workspace."
                  />
                )}
              </Panel>
            </section>

            <section
              id="understanding"
              className="mb-10"
            >
              <Panel
                title="Enterprise Understanding"
                subtitle="Business concepts consolidated from semantic and knowledge evidence."
              >
                {concepts.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {concepts.map(
                      (concept) => (
                        <div
                          key={
                            concept.enterprise_concept_id
                          }
                          className="rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-indigo-300"
                        >
                          <div className="mb-3 flex items-start justify-between gap-4">
                            <div>
                              <h3 className="text-xl font-bold text-slate-950">
                                {
                                  concept.concept_name
                                }
                              </h3>

                              <p className="mt-1 text-sm font-semibold text-indigo-600">
                                {
                                  concept.concept_type
                                }
                              </p>
                            </div>

                            <Badge tone="indigo">
                              {
                                formatConfidence(
                                  concept.confidence_score
                                )
                              }
                            </Badge>
                          </div>

                          <p className="leading-6 text-slate-600">
                            {
                              concept.concept_description
                              || (
                                "No business description "
                                + "is currently available."
                              )
                            }
                          </p>

                          <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
                            <span>
                              Evidence:{" "}
                              {
                                concept.evidence_count
                                ?? 0
                              }
                            </span>

                            <span>
                              {
                                concept.concept_status
                                || "ACTIVE"
                              }
                            </span>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                ) : (
                  <EmptyState
                    title="No enterprise concepts"
                    description="Build Enterprise Understanding from an active connector to generate reusable business concepts."
                  />
                )}
              </Panel>
            </section>

            <section
              id="intelligence"
              className="mb-10"
            >
              <Panel
                title="Latest Intelligence Findings"
                subtitle="Explainable findings generated by Sapientia's intelligence layer."
              >
                {findings.length > 0 ? (
                  <>
                    <div className="space-y-4">
                      {findings
                        .slice(0, 8)
                        .map(
                          (finding) => (
                            <FindingCard
                              key={
                                finding.intelligence_finding_id
                              }
                              finding={
                                finding
                              }
                            />
                          )
                        )}
                    </div>

                    <Link
                      href={
                        latestReport
                          ? `/workspace/${domain}/reports/${latestReport.intelligence_report_id}`
                          : `/workspace/${domain}/reports`
                      }
                      className="mt-6 inline-flex items-center gap-2 font-semibold text-indigo-600 hover:text-indigo-500"
                    >
                      View all findings and evidence

                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </>
                ) : (
                  <EmptyState
                    title="No intelligence findings"
                    description="Generate Enterprise Intelligence to create findings, evidence and a business narrative."
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


function WorkspaceAction({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-4 rounded-2xl border border-slate-200 p-4 transition hover:border-indigo-300 hover:bg-indigo-50/40"
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
        {icon}
      </div>

      <div className="min-w-0 flex-1">
        <p className="font-bold text-slate-950">
          {title}
        </p>

        <p className="mt-1 text-sm leading-5 text-slate-500">
          {description}
        </p>
      </div>

      <ArrowRight className="h-4 w-4 text-slate-300 transition group-hover:translate-x-1 group-hover:text-indigo-600" />
    </Link>
  );
}


function FindingCard({
  finding,
}: {
  finding: WorkspaceFinding;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
            {
              finding.finding_type
            }
          </p>

          <h3 className="mt-2 text-lg font-bold text-slate-950">
            {
              finding.finding_title
            }
          </h3>
        </div>

        <Badge
          tone={
            severityTone(
              finding.severity_level
            )
          }
        >
          {
            finding.severity_level
            || "INFO"
          }
        </Badge>
      </div>

      <p className="mt-3 leading-6 text-slate-600">
        {
          finding.finding_description
        }
      </p>

      {finding.finding_interpretation && (
        <p className="mt-3 rounded-xl border border-slate-200 bg-white p-4 text-sm leading-6 text-slate-600">
          <strong>
            Interpretation:
          </strong>{" "}
          {
            finding.finding_interpretation
          }
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
        <span>
          Confidence:{" "}
          {
            formatConfidence(
              finding.confidence_score
            )
          }
        </span>

        <span>
          {
            formatDateTime(
              finding.created_at
            )
          }
        </span>
      </div>
    </div>
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

      <p className="mt-1 font-bold text-slate-950">
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
      <h3 className="font-bold text-slate-900">
        {title}
      </h3>

      <p className="mx-auto mt-2 max-w-xl leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
}


function WorkspaceLoading() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-4">
        {Array.from({
          length: 4,
        }).map((_, index) => (
          <div
            key={index}
            className="h-28 animate-pulse rounded-2xl bg-slate-200"
          />
        ))}
      </div>

      <div className="h-80 animate-pulse rounded-3xl bg-slate-200" />
    </div>
  );
}


function severityTone(
  severity: string | null
):
  | "red"
  | "amber"
  | "indigo"
  | "green"
  | "slate" {
  const value =
    String(
      severity || ""
    ).toUpperCase();

  if (
    value === "CRITICAL"
    || value === "HIGH"
  ) {
    return "red";
  }

  if (value === "MEDIUM") {
    return "amber";
  }

  if (value === "LOW") {
    return "indigo";
  }

  return "slate";
}


function formatConfidence(
  value: number | null
): string {
  if (value === null) {
    return "N/A";
  }

  const numeric =
    Number(value);

  return `${
    Math.round(
      (
        numeric <= 1
          ? numeric * 100
          : numeric
      ) * 10
    ) / 10
  }%`;
}


function formatDateTime(
  value: string | null
): string {
  if (!value) {
    return "Not available";
  }

  return new Date(
    value
  ).toLocaleString();
}


function getMessage(
  cause: unknown,
  fallback: string
): string {
  return cause instanceof Error
    ? cause.message
    : fallback;
}