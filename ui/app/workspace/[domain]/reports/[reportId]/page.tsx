"use client";

import Link from "next/link";

import {
  ArrowLeft,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileText,
  Loader2,
  Network,
  ShieldAlert,
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


type IntelligenceReport = {
  intelligence_report_id: number;
  project_id: number;
  business_domain_id: number;

  domain_code: string;
  domain_name: string;

  report_scope: string;
  report_type: string;
  report_title: string;

  summary_text: string | null;

  report_json:
    Record<string, unknown> | null;

  ai_context_json:
    Record<string, unknown> | null;

  created_at: string;
};


type IntelligenceFinding = {
  intelligence_finding_id: number;
  intelligence_report_id: number;

  finding_type: string;
  finding_title: string;
  finding_description: string;
  finding_interpretation: string | null;

  confidence_score: number | null;
  severity_level: string | null;

  source_object_type: string | null;
  source_object_id: number | null;

  evidence_count: number;
  created_at: string;
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
  intelligence_finding_id: number;

  evidence_type: string | null;
  evidence_source: string | null;
  evidence_text: string | null;

  dataset_id: number | null;
  dataset_name: string | null;

  column_id: number | null;
  column_name: string | null;

  document_id: number | null;
  document_name: string | null;

  knowledge_item_id: number | null;
  knowledge_item_name: string | null;

  intelligence_link_id: number | null;
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


export default function ReportDetailPage() {
  const params = useParams();

  const domain = String(
    params.domain
  ).toUpperCase();

  const reportId = Number(
    params.reportId
  );

  const [
    response,
    setResponse,
  ] = useState<
    ReportResponse | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    expandedFindingId,
    setExpandedFindingId,
  ] = useState<
    number | null
  >(null);

  const [
    evidence,
    setEvidence,
  ] = useState<
    Record<
      number,
      FindingEvidence[]
    >
  >({});

  const [
    evidenceLoading,
    setEvidenceLoading,
  ] = useState<
    number | null
  >(null);


  const loadReport =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const data =
          await apiFetch<ReportResponse>(
            `/intelligence/reports/${reportId}`
          );

        if (
          data.report.domain_code
            .toUpperCase()
          !== domain
        ) {
          throw new Error(
            "This report belongs to a different workspace."
          );
        }

        setResponse(data);

      } catch (cause) {
        setResponse(null);

        setError(
          getMessage(
            cause,
            "Unable to load the intelligence report."
          )
        );

      } finally {
        setLoading(false);
      }
    }, [domain, reportId]);


  useEffect(() => {
    void loadReport();
  }, [loadReport]);


  async function toggleEvidence(
    findingId: number
  ) {
    if (
      expandedFindingId === findingId
    ) {
      setExpandedFindingId(null);
      return;
    }

    setExpandedFindingId(
      findingId
    );

    if (evidence[findingId]) {
      return;
    }

    setEvidenceLoading(
      findingId
    );

    try {
      const data =
        await apiFetch<EvidenceResponse>(
          `/intelligence/findings/${findingId}/evidence`
        );

      setEvidence(
        (current) => ({
          ...current,
          [findingId]:
            Array.isArray(
              data.evidence
            )
              ? data.evidence
              : [],
        })
      );

    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to load supporting evidence."
        )
      );

    } finally {
      setEvidenceLoading(null);
    }
  }


  const report =
    response?.report;

  const findings =
    response?.findings || [];

  const concepts =
    response?.concepts || [];

  const evidenceCount =
    findings.reduce(
      (total, finding) =>
        total
        + Number(
          finding.evidence_count
          || 0
        ),
      0
    );

  const highPriorityCount =
    findings.filter(
      (finding) =>
        [
          "CRITICAL",
          "HIGH",
        ].includes(
          String(
            finding.severity_level
            || ""
          ).toUpperCase()
        )
    ).length;


  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <Link
          href={
            `/workspace/${domain}/reports`
          }
          className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-500"
        >
          <ArrowLeft className="h-4 w-4" />

          Back to reports
        </Link>

        <div className="mb-8 mt-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
            {domain} Intelligence
          </p>

          <h1 className="mt-2 text-4xl font-bold text-slate-950">
            {report?.report_title
              || "Intelligence Report"}
          </h1>

          <p className="mt-3 text-slate-500">
            {report
              ? `Generated ${formatDateTime(
                  report.created_at
                )}`
              : "Loading report details..."}
          </p>
        </div>

        <WorkspaceTabs
          domain={domain}
        />

        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <ReportLoading />
        ) : !response || !report ? (
          <EmptyState
            title="Report unavailable"
            description="The requested intelligence report could not be loaded."
          />
        ) : (
          <>
            <div className="mb-8 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Findings"
                value={
                  findings.length
                }
              />

              <MetricCard
                label="Evidence Items"
                value={
                  evidenceCount
                }
              />

              <MetricCard
                label="Concepts"
                value={
                  concepts.length
                }
              />

              <MetricCard
                label="High Priority"
                value={
                  highPriorityCount
                }
              />
            </div>

            <section className="mb-8">
              <Panel
                title="Enterprise Narrative"
                subtitle="Sapientia's consolidated interpretation of the current enterprise evidence."
              >
                <div className="rounded-3xl bg-gradient-to-br from-indigo-50 via-white to-fuchsia-50 p-7">
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white">
                      <Sparkles className="h-5 w-5" />
                    </div>

                    <div>
                      <p className="whitespace-pre-wrap text-lg leading-8 text-slate-700">
                        {
                          report.summary_text
                          || (
                            "No narrative summary "
                            + "is available."
                          )
                        }
                      </p>

                      <div className="mt-5 flex flex-wrap gap-2">
                        <Badge tone="indigo">
                          {
                            report.report_type
                          }
                        </Badge>

                        <Badge tone="slate">
                          {
                            report.report_scope
                          }
                        </Badge>

                        <Badge tone="green">
                          Report #
                          {
                            report.intelligence_report_id
                          }
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </Panel>
            </section>

            <section className="mb-8">
              <Panel
                title="Intelligence Findings"
                subtitle="Each finding includes interpretation, confidence and traceable supporting evidence."
              >
                {findings.length > 0 ? (
                  <div className="space-y-5">
                    {findings.map(
                      (finding) => (
                        <FindingCard
                          key={
                            finding.intelligence_finding_id
                          }
                          finding={
                            finding
                          }
                          expanded={
                            expandedFindingId
                            === finding.intelligence_finding_id
                          }
                          evidence={
                            evidence[
                              finding.intelligence_finding_id
                            ] || []
                          }
                          evidenceLoading={
                            evidenceLoading
                            === finding.intelligence_finding_id
                          }
                          onToggle={() =>
                            void toggleEvidence(
                              finding.intelligence_finding_id
                            )
                          }
                        />
                      )
                    )}
                  </div>
                ) : (
                  <EmptyState
                    title="No findings in this report"
                    description="The intelligence engine did not produce findings for this snapshot."
                  />
                )}
              </Panel>
            </section>

            <section className="mb-8">
              <Panel
                title="Enterprise Concepts"
                subtitle="Business concepts available to the intelligence and AI layers when this report was generated."
              >
                {concepts.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
                    {concepts.map(
                      (concept) => (
                        <ConceptCard
                          key={
                            concept.enterprise_concept_id
                          }
                          concept={
                            concept
                          }
                        />
                      )
                    )}
                  </div>
                ) : (
                  <EmptyState
                    title="No enterprise concepts"
                    description="No enterprise concepts were available for this workspace."
                  />
                )}
              </Panel>
            </section>

            <section>
              <Panel
                title="Continue with AI"
                subtitle="Use this persisted intelligence report as grounded context for the AI Advisor."
              >
                <div className="flex flex-col justify-between gap-6 rounded-2xl bg-slate-950 p-6 text-white xl:flex-row xl:items-center">
                  <div className="flex items-start gap-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/10">
                      <BrainCircuit className="h-5 w-5" />
                    </div>

                    <div>
                      <h3 className="text-lg font-bold">
                        Ask Sapientia about this workspace
                      </h3>

                      <p className="mt-2 max-w-2xl leading-6 text-slate-300">
                        Ask questions grounded in the
                        latest enterprise concepts,
                        findings, evidence and
                        intelligence narrative.
                      </p>
                    </div>
                  </div>

                  <Link
                    href={
                      `/workspace/${domain}/ai`
                    }
                    className="rounded-xl bg-indigo-500 px-5 py-3 text-center font-semibold text-white hover:bg-indigo-400"
                  >
                    Open AI Advisor
                  </Link>
                </div>
              </Panel>
            </section>
          </>
        )}
      </section>
    </main>
  );
}


function FindingCard({
  finding,
  expanded,
  evidence,
  evidenceLoading,
  onToggle,
}: {
  finding: IntelligenceFinding;
  expanded: boolean;
  evidence: FindingEvidence[];
  evidenceLoading: boolean;
  onToggle: () => void;
}) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="p-6">
        <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-start">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
              {
                finding.finding_type
              }
            </p>

            <h3 className="mt-2 text-xl font-bold text-slate-950">
              {
                finding.finding_title
              }
            </h3>
          </div>

          <div className="flex flex-wrap gap-2">
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

            <Badge tone="indigo">
              {
                formatConfidence(
                  finding.confidence_score
                )
              }
            </Badge>
          </div>
        </div>

        <p className="mt-4 leading-7 text-slate-600">
          {
            finding.finding_description
          }
        </p>

        {finding.finding_interpretation && (
          <div className="mt-4 rounded-xl border border-indigo-100 bg-indigo-50 p-4">
            <p className="text-sm font-semibold text-indigo-900">
              Business interpretation
            </p>

            <p className="mt-2 leading-6 text-indigo-800">
              {
                finding.finding_interpretation
              }
            </p>
          </div>
        )}

        <button
          type="button"
          onClick={onToggle}
          className="mt-5 inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50"
        >
          <Network className="h-4 w-4" />

          {expanded
            ? "Hide evidence"
            : `View evidence (${finding.evidence_count || 0})`}
        </button>
      </div>

      {expanded && (
        <div className="border-t border-slate-200 bg-slate-50 p-6">
          {evidenceLoading ? (
            <div className="flex items-center gap-3 text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin" />

              Loading supporting evidence...
            </div>
          ) : evidence.length > 0 ? (
            <div className="space-y-3">
              {evidence.map(
                (item) => (
                  <EvidenceCard
                    key={
                      item.intelligence_evidence_id
                    }
                    evidence={
                      item
                    }
                  />
                )
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              No detailed evidence records are
              associated with this finding.
            </p>
          )}
        </div>
      )}
    </article>
  );
}


function EvidenceCard({
  evidence,
}: {
  evidence: FindingEvidence;
}) {
  const sourceLabel =
    evidence.column_name
      ? `${
          evidence.dataset_name
          || "Dataset"
        }.${evidence.column_name}`

      : evidence.dataset_name
        || evidence.document_name
        || evidence.knowledge_item_name
        || evidence.evidence_source
        || "Enterprise evidence";

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
            {evidence.dataset_id ? (
              <Database className="h-4 w-4" />
            ) : evidence.document_id ? (
              <FileText className="h-4 w-4" />
            ) : (
              <CheckCircle2 className="h-4 w-4" />
            )}
          </div>

          <div>
            <p className="font-semibold text-slate-900">
              {sourceLabel}
            </p>

            <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">
              {
                evidence.evidence_type
                || "EVIDENCE"
              }
            </p>
          </div>
        </div>

        <Badge tone="slate">
          {
            formatConfidence(
              evidence.confidence_score
            )
          }
        </Badge>
      </div>

      {evidence.evidence_text && (
        <p className="mt-3 text-sm leading-6 text-slate-600">
          {
            evidence.evidence_text
          }
        </p>
      )}
    </div>
  );
}


function ConceptCard({
  concept,
}: {
  concept: EnterpriseConcept;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-950">
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

      <p className="mt-3 leading-6 text-slate-600">
        {
          concept.concept_description
          || "No description is available."
        }
      </p>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
        <span>
          Evidence:{" "}
          {
            concept.evidence_count
            || 0
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
  );
}


function ReportLoading() {
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
      <div className="h-96 animate-pulse rounded-3xl bg-slate-200" />
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
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
      <ShieldAlert className="mx-auto h-7 w-7 text-slate-400" />

      <h3 className="mt-3 font-bold text-slate-900">
        {title}
      </h3>

      <p className="mx-auto mt-2 max-w-xl leading-6 text-slate-500">
        {description}
      </p>
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