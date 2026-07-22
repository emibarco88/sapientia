"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BookOpen,
  Check,
  Circle,
  Database,
  FileText,
  Lightbulb,
  MessageSquareText,
  Sparkles,
} from "lucide-react";

import Sidebar from "@/components/layout/Sidebar";
import { apiFetch, clearToken } from "@/lib/api";

type Domain = {
  business_domain_id: number;
  domain_code: string;
  domain_name: string;
  datasets: number;
  concepts: number;
  intelligence_reports: number;
};

type WorkspaceResponse = {
  domain?: {
    domain_code: string;
    domain_name: string;
    description: string | null;
    industry: string | null;
  };
  summary: {
    datasets: number;
    enterprise_concepts: number;
    findings: number;
    reports: number;
  };
  datasets: Array<{
    dataset_id: number;
    name: string;
    source_type?: string | null;
    source_system_name: string | null;
  }>;
  concepts: Array<{
    enterprise_concept_id: number;
    concept_name: string;
    concept_description: string | null;
  }>;
  findings: Array<{
    intelligence_finding_id: number;
    intelligence_report_id?: number | null;
    finding_title: string;
    finding_description: string;
    created_at: string | null;
  }>;
  latest_report: {
    intelligence_report_id: number;
    report_title: string;
    summary_text: string | null;
    created_at: string | null;
  } | null;
};

export default function EnterpriseOverviewPage() {
  const router = useRouter();
  const [domain, setDomain] = useState<Domain | null>(null);
  const [workspace, setWorkspace] = useState<WorkspaceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadEnterprise() {
      setLoading(true);
      setError("");

      try {
        const domains = await apiFetch<Domain[]>("/domains");
        const activeDomain = Array.isArray(domains) ? domains[0] : null;

        if (!activeDomain) {
          setDomain(null);
          setWorkspace(null);
          return;
        }

        const workspaceData = await apiFetch<WorkspaceResponse>(
          `/domains/${activeDomain.domain_code}/workspace`
        );

        setDomain(activeDomain);
        setWorkspace(workspaceData);
      } catch (cause) {
        console.error("Failed to load enterprise overview:", cause);
        setError("Sapientia could not load your enterprise at the moment.");
      } finally {
        setLoading(false);
      }
    }

    void loadEnterprise();
  }, []);

  const domainCode = domain?.domain_code?.toUpperCase() || "";
  const enterpriseName =
    workspace?.domain?.domain_name || domain?.domain_name || "Your Enterprise";

  const journey = useMemo(() => {
    const hasSources = Number(workspace?.summary.datasets || 0) > 0;
    const hasUnderstanding =
      Number(workspace?.summary.enterprise_concepts || 0) > 0;
    const hasIntelligence =
      Number(workspace?.summary.findings || 0) > 0 || Boolean(workspace?.latest_report);

    return [
      {
        label: "Connect data sources",
        description: "Bring together the information that explains your business.",
        complete: hasSources,
        href: "/sources",
        icon: <Database className="h-5 w-5" />,
      },
      {
        label: "Discover your enterprise",
        description: "Identify the business information available to Sapientia.",
        complete: hasSources,
        href: domainCode ? `/workspace/${domainCode}#assets` : "/sources",
        icon: <Sparkles className="h-5 w-5" />,
      },
      {
        label: "Learn your business",
        description: "Build a shared understanding of business concepts and meaning.",
        complete: hasUnderstanding,
        href: domainCode ? `/workspace/${domainCode}#understanding` : "/dashboard",
        icon: <BookOpen className="h-5 w-5" />,
      },
      {
        label: "Generate intelligence",
        description: "Create evidence-backed findings and business insights.",
        complete: hasIntelligence,
        href: domainCode ? `/workspace/${domainCode}#intelligence` : "/dashboard",
        icon: <Lightbulb className="h-5 w-5" />,
      },
    ];
  }, [domainCode, workspace]);

  const completedSteps = journey.filter((step) => step.complete).length;
  const enterpriseReady = completedSteps === journey.length;

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <main className="min-h-screen bg-[#f7f8fa]">
      <Sidebar />

      <section className="ml-64 min-h-screen px-8 py-8 lg:px-12 xl:px-16">
        <header className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">Enterprise</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
              {enterpriseName}
            </h1>
          </div>

          <button
            onClick={logout}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-950"
          >
            Sign out
          </button>
        </header>

        <div className="mx-auto mt-10 max-w-7xl">
          {loading ? (
            <EnterpriseLoading />
          ) : error ? (
            <EmptyEnterprise title="Enterprise unavailable" description={error} />
          ) : !domain || !workspace ? (
            <EmptyEnterprise
              title="Welcome to Sapientia"
              description="Connect your first data source to begin building an understanding of your enterprise."
              actionHref="/sources"
              actionLabel="Connect a data source"
            />
          ) : (
            <>
              <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm">
                <div className="grid gap-8 p-8 lg:grid-cols-[1.4fr_0.6fr] lg:p-10">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700">
                      <span className="h-2 w-2 rounded-full bg-emerald-500" />
                      {enterpriseReady ? "Enterprise ready" : "Building enterprise understanding"}
                    </div>

                    <h2 className="mt-6 max-w-3xl text-4xl font-semibold tracking-[-0.03em] text-slate-950 lg:text-5xl">
                      {enterpriseReady
                        ? "Sapientia understands your enterprise."
                        : "Sapientia is learning how your business works."}
                    </h2>

                    <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
                      {workspace.domain?.description ||
                        "Your enterprise information, business knowledge and intelligence are brought together in one clear, evidence-backed view."}
                    </p>

                    <div className="mt-8 flex flex-wrap gap-3">
                      <Link
                        href={`/workspace/${domainCode}/ai`}
                        className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                      >
                        Open Enterprise Agent
                        <ArrowRight className="h-4 w-4" />
                      </Link>

                      {workspace.latest_report && (
                        <Link
                          href={`/workspace/${domainCode}/reports/${workspace.latest_report.intelligence_report_id}`}
                          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-950"
                        >
                          View latest insight
                        </Link>
                      )}
                    </div>
                  </div>

                  <div className="rounded-3xl bg-slate-950 p-6 text-white">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
                      <MessageSquareText className="h-5 w-5" />
                    </div>
                    <p className="mt-6 text-sm font-medium text-slate-300">
                      Enterprise Intelligence Agent
                    </p>
                    <h3 className="mt-2 text-2xl font-semibold">
                      {enterpriseReady ? "Ready to help" : "Preparing your context"}
                    </h3>
                    <p className="mt-3 text-sm leading-6 text-slate-300">
                      Ask questions about your business and receive answers grounded in enterprise knowledge and evidence.
                    </p>
                    <Link
                      href={`/workspace/${domainCode}/ai`}
                      className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-white"
                    >
                      Ask a business question
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>
              </section>

              <section className="mt-8 grid gap-8 xl:grid-cols-[1.25fr_0.75fr]">
                <div className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
                  <div className="flex items-end justify-between gap-6">
                    <div>
                      <p className="text-sm font-medium text-slate-500">Enterprise journey</p>
                      <h2 className="mt-1 text-2xl font-semibold text-slate-950">
                        From information to intelligence
                      </h2>
                    </div>
                    <p className="text-sm text-slate-500">
                      {completedSteps} of {journey.length} complete
                    </p>
                  </div>

                  <div className="mt-7 h-1.5 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-slate-950 transition-all"
                      style={{ width: `${(completedSteps / journey.length) * 100}%` }}
                    />
                  </div>

                  <div className="mt-6 divide-y divide-slate-100">
                    {journey.map((step) => (
                      <Link
                        key={step.label}
                        href={step.href}
                        className="group flex items-start gap-4 py-5 first:pt-2 last:pb-1"
                      >
                        <div
                          className={[
                            "mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
                            step.complete
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-slate-100 text-slate-500",
                          ].join(" ")}
                        >
                          {step.complete ? <Check className="h-5 w-5" /> : step.icon}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-4">
                            <h3 className="font-semibold text-slate-950">{step.label}</h3>
                            <ArrowRight className="h-4 w-4 text-slate-300 transition group-hover:translate-x-1 group-hover:text-slate-600" />
                          </div>
                          <p className="mt-1 text-sm leading-6 text-slate-500">
                            {step.description}
                          </p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>

                <div className="space-y-8">
                  <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
                    <p className="text-sm font-medium text-slate-500">Enterprise knowledge</p>
                    <h2 className="mt-1 text-2xl font-semibold text-slate-950">
                      What Sapientia understands
                    </h2>

                    <div className="mt-6 flex flex-wrap gap-2">
                      {getKnowledgeAreas(workspace).map((area) => (
                        <span
                          key={area}
                          className="rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700"
                        >
                          {area}
                        </span>
                      ))}
                    </div>

                    <Link
                      href={`/workspace/${domainCode}#understanding`}
                      className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-950"
                    >
                      Explore enterprise knowledge
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </section>

                  <section className="rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
                    <p className="text-sm font-medium text-slate-500">Latest intelligence</p>
                    {workspace.latest_report ? (
                      <>
                        <h2 className="mt-2 text-xl font-semibold text-slate-950">
                          {workspace.latest_report.report_title}
                        </h2>
                        <p className="mt-3 line-clamp-4 text-sm leading-6 text-slate-600">
                          {workspace.latest_report.summary_text ||
                            "A new enterprise intelligence report is ready to explore."}
                        </p>
                        <Link
                          href={`/workspace/${domainCode}/reports/${workspace.latest_report.intelligence_report_id}`}
                          className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-950"
                        >
                          View report and evidence
                          <ArrowRight className="h-4 w-4" />
                        </Link>
                      </>
                    ) : (
                      <>
                        <h2 className="mt-2 text-xl font-semibold text-slate-950">
                          Intelligence is being prepared
                        </h2>
                        <p className="mt-3 text-sm leading-6 text-slate-600">
                          Complete the enterprise journey to generate your first evidence-backed insight.
                        </p>
                      </>
                    )}
                  </section>
                </div>
              </section>

              <section className="mt-8 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
                <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
                  <div>
                    <p className="text-sm font-medium text-slate-500">Recent activity</p>
                    <h2 className="mt-1 text-2xl font-semibold text-slate-950">
                      What has changed in your enterprise
                    </h2>
                  </div>
                  <Link
                    href={`/workspace/${domainCode}/reports`}
                    className="inline-flex items-center gap-2 text-sm font-semibold text-slate-950"
                  >
                    View all insights
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  {getRecentActivity(workspace).map((activity) => (
                    <div key={activity.title} className="rounded-2xl bg-slate-50 p-5">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-slate-700 shadow-sm">
                        {activity.icon}
                      </div>
                      <h3 className="mt-4 font-semibold text-slate-950">{activity.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        {activity.description}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function getKnowledgeAreas(workspace: WorkspaceResponse): string[] {
  const conceptNames = workspace.concepts
    .map((concept) => concept.concept_name)
    .filter(Boolean)
    .slice(0, 6);

  if (conceptNames.length > 0) {
    return conceptNames;
  }

  const sourceNames = workspace.datasets
    .map((dataset) => dataset.source_system_name || dataset.source_type)
    .filter((value): value is string => Boolean(value))
    .slice(0, 6);

  return sourceNames.length > 0
    ? Array.from(new Set(sourceNames))
    : ["Business information", "Documents", "Enterprise context"];
}

function getRecentActivity(workspace: WorkspaceResponse) {
  const findings = workspace.findings.slice(0, 3).map((finding) => ({
    title: finding.finding_title,
    description: finding.finding_description,
    icon: <Lightbulb className="h-4 w-4" />,
  }));

  if (findings.length > 0) {
    return findings;
  }

  return [
    {
      title: "Enterprise information connected",
      description: "Sapientia can access the business information available in this enterprise.",
      icon: <Database className="h-4 w-4" />,
    },
    {
      title: "Business knowledge prepared",
      description: "Concepts and business meaning are being brought together into one context.",
      icon: <BookOpen className="h-4 w-4" />,
    },
    {
      title: "Intelligence ready to generate",
      description: "Create evidence-backed findings once your enterprise understanding is complete.",
      icon: <FileText className="h-4 w-4" />,
    },
  ];
}

function EnterpriseLoading() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-80 rounded-[2rem] bg-white" />
      <div className="grid gap-8 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="h-[34rem] rounded-[2rem] bg-white" />
        <div className="space-y-8">
          <div className="h-60 rounded-[2rem] bg-white" />
          <div className="h-60 rounded-[2rem] bg-white" />
        </div>
      </div>
    </div>
  );
}

function EmptyEnterprise({
  title,
  description,
  actionHref,
  actionLabel,
}: {
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white px-8 py-20 text-center shadow-sm">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
        <Circle className="h-6 w-6" />
      </div>
      <h2 className="mt-6 text-3xl font-semibold text-slate-950">{title}</h2>
      <p className="mx-auto mt-3 max-w-xl text-slate-600">{description}</p>
      {actionHref && actionLabel && (
        <Link
          href={actionHref}
          className="mt-7 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white"
        >
          {actionLabel}
          <ArrowRight className="h-4 w-4" />
        </Link>
      )}
    </section>
  );
}
