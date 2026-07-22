"use client";

import Link from "next/link";

import {
  ArrowRight,
  FileText,
  ShieldAlert,
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
  report_scope: string;
  report_type: string;
  report_title: string;
  summary_text: string | null;
  created_at: string;

  findings: number;
  evidence_items: number;
  high_priority_findings: number;
};


export default function ReportsPage() {
  const params = useParams();

  const domain = String(
    params.domain
  ).toUpperCase();

  const [
    reports,
    setReports,
  ] = useState<
    IntelligenceReport[]
  >([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  const loadReports =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const response =
          await apiFetch<
            IntelligenceReport[]
          >(
            `/intelligence/${domain}/reports`
          );

        setReports(
          Array.isArray(response)
            ? response
            : []
        );

      } catch (cause) {
        setReports([]);

        setError(
          getMessage(
            cause,
            "Unable to load intelligence reports."
          )
        );

      } finally {
        setLoading(false);
      }
    }, [domain]);


  useEffect(() => {
    void loadReports();
  }, [loadReports]);


  const totalFindings =
    reports.reduce(
      (total, report) =>
        total
        + Number(
          report.findings || 0
        ),
      0
    );

  const totalEvidence =
    reports.reduce(
      (total, report) =>
        total
        + Number(
          report.evidence_items || 0
        ),
      0
    );

  const highPriorityFindings =
    reports.reduce(
      (total, report) =>
        total
        + Number(
          report.high_priority_findings
          || 0
        ),
      0
    );


  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <Link
          href={`/workspace/${domain}`}
          className="text-sm font-semibold text-indigo-600 hover:text-indigo-500"
        >
          ← Back to workspace
        </Link>

        <div className="mb-8 mt-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
            {domain} Workspace
          </p>

          <h1 className="mt-2 text-4xl font-bold text-slate-950">
            Intelligence Reports
          </h1>

          <p className="mt-3 max-w-3xl leading-7 text-slate-600">
            Explore generated business narratives,
            findings, supporting evidence and
            intelligence history for {domain}.
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

        <div className="mb-8 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Reports"
            value={
              reports.length
            }
          />

          <MetricCard
            label="Findings"
            value={
              totalFindings
            }
          />

          <MetricCard
            label="Evidence Items"
            value={
              totalEvidence
            }
          />

          <MetricCard
            label="High Priority"
            value={
              highPriorityFindings
            }
          />
        </div>

        <Panel
          title="Report History"
          subtitle="Every intelligence generation is preserved as a historical enterprise snapshot."
        >
          {loading ? (
            <ReportsLoading />
          ) : reports.length > 0 ? (
            <div className="space-y-4">
              {reports.map(
                (report, index) => (
                  <Link
                    key={
                      report.intelligence_report_id
                    }
                    href={
                      `/workspace/${domain}/reports/${report.intelligence_report_id}`
                    }
                    className="group block rounded-2xl border border-slate-200 bg-white p-6 transition hover:border-indigo-300 hover:shadow-sm"
                  >
                    <div className="flex flex-col justify-between gap-6 xl:flex-row xl:items-start">
                      <div className="flex gap-4">
                        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
                          <FileText className="h-5 w-5" />
                        </div>

                        <div>
                          <div className="flex flex-wrap items-center gap-3">
                            <h2 className="text-xl font-bold text-slate-950">
                              {
                                report.report_title
                              }
                            </h2>

                            {index === 0 && (
                              <Badge tone="green">
                                Latest
                              </Badge>
                            )}
                          </div>

                          <p className="mt-2 max-w-3xl line-clamp-3 leading-6 text-slate-600">
                            {
                              report.summary_text
                              || (
                                "No narrative summary "
                                + "is available."
                              )
                            }
                          </p>

                          <p className="mt-3 text-sm text-slate-400">
                            Generated{" "}
                            {
                              formatDateTime(
                                report.created_at
                              )
                            }
                          </p>
                        </div>
                      </div>

                      <div className="flex shrink-0 flex-wrap gap-3">
                        <ReportMetric
                          label="Findings"
                          value={
                            report.findings
                            || 0
                          }
                        />

                        <ReportMetric
                          label="Evidence"
                          value={
                            report.evidence_items
                            || 0
                          }
                        />

                        {Number(
                          report.high_priority_findings
                          || 0
                        ) > 0 && (
                          <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">
                            <ShieldAlert className="h-4 w-4" />

                            {
                              report.high_priority_findings
                            }{" "}
                            priority
                          </div>
                        )}

                        <div className="flex items-center text-indigo-600">
                          <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" />
                        </div>
                      </div>
                    </div>
                  </Link>
                )
              )}
            </div>
          ) : (
            <EmptyState
              title="No intelligence reports"
              description="Generate Enterprise Intelligence from an active connector to create the first report."
            />
          )}
        </Panel>
      </section>
    </main>
  );
}


function ReportMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl bg-slate-50 px-3 py-2 text-center">
      <p className="text-xs uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-1 font-bold text-slate-950">
        {value}
      </p>
    </div>
  );
}


function ReportsLoading() {
  return (
    <div className="space-y-4">
      {Array.from({
        length: 3,
      }).map((_, index) => (
        <div
          key={index}
          className="h-40 animate-pulse rounded-2xl bg-slate-200"
        />
      ))}
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
      <h3 className="font-bold text-slate-900">
        {title}
      </h3>

      <p className="mx-auto mt-2 max-w-xl leading-6 text-slate-500">
        {description}
      </p>
    </div>
  );
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