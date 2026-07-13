"use client";

import Link from "next/link";

import {
  Check,
  Database,
  ExternalLink,
  Lightbulb,
  Loader2,
  PlugZap,
  Sparkles,
} from "lucide-react";

import {
  ReactNode,
  useCallback,
  useEffect,
  useState,
} from "react";

import { apiFetch } from "@/lib/api";


type StageStatus =
  | "PENDING"
  | "CONFIGURED"
  | "CONNECTED"
  | "RUNNING"
  | "DISCOVERING"
  | "COMPLETED"
  | "FAILED"
  | "ERROR";


type LifecycleResponse = {
  connector_id: number;
  connector_name: string;
  connector_status: string;

  domain_code: string | null;
  domain_name: string | null;

  connection: {
    status: StageStatus;
    last_tested_at: string | null;
  };

  discovery: {
    status: StageStatus;
    message: string | null;
    last_completed_at: string | null;
    datasets: number;
    columns: number;
  };

  understanding: {
    status: StageStatus;
    message: string | null;
    last_completed_at: string | null;
    semantic_columns: number;
    intelligence_links: number;
    enterprise_concepts: number;
  };

  intelligence: {
    status: StageStatus;
    message: string | null;
    last_completed_at: string | null;
  };
};


type UnderstandingResponse = {
  status: string;
  message: string;

  datasets_processed: number;
  semantic_columns: number;
  persisted_intelligence_links: number;
  persisted_concepts: number;
};


type IntelligenceResponse = {
  status: string;
  message: string;

  project_id: number;
  business_domain: string;

  intelligence_report_id:
    number | null;

  datasets_analysed: number;
  semantic_columns: number;
  knowledge_items: number;
  intelligence_links: number;
  enterprise_concepts: number;
  findings_generated: number;
  lineage_records: number;

  summary_text:
    string | null;
};


export default function ConnectorLifecycle({
  connectorId,
  connectorStatus,
  onTestConnection,
  onDiscoverAssets,
  onLifecycleChanged,
}: {
  connectorId: number;

  connectorStatus: string;

  onTestConnection:
    () => Promise<void>;

  onDiscoverAssets:
    () => Promise<void>;

  onLifecycleChanged?:
    () => Promise<void> | void;
}) {
  const [
    lifecycle,
    setLifecycle,
  ] = useState<
    LifecycleResponse | null
  >(null);

  const [
    activeAction,
    setActiveAction,
  ] = useState<
    | "test"
    | "discovery"
    | "understanding"
    | "intelligence"
    | null
  >(null);

  const [
    error,
    setError,
  ] = useState("");

  const [
    success,
    setSuccess,
  ] = useState("");

  const [
    understandingSummary,
    setUnderstandingSummary,
  ] = useState<
    UnderstandingResponse | null
  >(null);

  const [
    intelligenceSummary,
    setIntelligenceSummary,
  ] = useState<
    IntelligenceResponse | null
  >(null);


  const loadLifecycle =
    useCallback(async () => {
      const response =
        await apiFetch<LifecycleResponse>(
          `/sources/${connectorId}/lifecycle`
        );

      setLifecycle(response);
    }, [connectorId]);


  useEffect(() => {
    setError("");
    setSuccess("");
    setUnderstandingSummary(null);
    setIntelligenceSummary(null);

    void loadLifecycle().catch(
      (cause) => {
        setError(
          getMessage(
            cause,
            "Unable to load connector lifecycle."
          )
        );
      }
    );
  }, [loadLifecycle]);


  async function refreshAfterAction() {
    await loadLifecycle();
    await onLifecycleChanged?.();
  }


  async function runTest() {
    setActiveAction("test");
    setError("");
    setSuccess("");

    try {
      await onTestConnection();

      setSuccess(
        "Connection validated successfully."
      );

      await refreshAfterAction();

    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Connection test failed."
        )
      );

    } finally {
      setActiveAction(null);
    }
  }


  async function runDiscovery() {
    setActiveAction("discovery");
    setError("");
    setSuccess("");
    setUnderstandingSummary(null);
    setIntelligenceSummary(null);

    try {
      await onDiscoverAssets();

      setSuccess(
        "Asset discovery completed successfully."
      );

      await refreshAfterAction();

    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Asset discovery failed."
        )
      );

    } finally {
      setActiveAction(null);
    }
  }


  async function runUnderstanding() {
    setActiveAction("understanding");
    setError("");
    setSuccess("");
    setUnderstandingSummary(null);
    setIntelligenceSummary(null);

    try {
      const response =
        await apiFetch<UnderstandingResponse>(
          `/sources/${connectorId}/understanding`,
          {
            method: "POST",

            body: JSON.stringify({
              refresh_concepts: true,
            }),
          }
        );

      setUnderstandingSummary(
        response
      );

      setSuccess(
        response.message
      );

      await refreshAfterAction();

    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to build Enterprise Understanding."
        )
      );

      try {
        await loadLifecycle();
      } catch {
        // Keep the original error visible.
      }

    } finally {
      setActiveAction(null);
    }
  }


  async function runIntelligence() {
    const domainCode =
      lifecycle?.domain_code;

    if (!domainCode) {
      setError(
        "Assign the connector to a business workspace before generating intelligence."
      );

      return;
    }

    setActiveAction(
      "intelligence"
    );

    setError("");
    setSuccess("");
    setIntelligenceSummary(null);

    try {
      const response =
        await apiFetch<IntelligenceResponse>(
          `/intelligence/${domainCode}/generate`,
          {
            method: "POST",

            body: JSON.stringify({
              project_id: 1,
              persist: true,
            }),
          }
        );

      setIntelligenceSummary(
        response
      );

      setSuccess(
        response.message
      );

      await refreshAfterAction();

    } catch (cause) {
      setError(
        getMessage(
          cause,
          "Unable to generate Enterprise Intelligence."
        )
      );

      try {
        await loadLifecycle();
      } catch {
        // Keep the original error visible.
      }

    } finally {
      setActiveAction(null);
    }
  }


  const connectionStatus =
    lifecycle?.connection.status
    || connectorStatus;

  const discoveryCompleted =
    lifecycle?.discovery.status
    === "COMPLETED";

  const understandingCompleted =
    lifecycle?.understanding.status
    === "COMPLETED";

  const intelligenceCompleted =
    lifecycle?.intelligence.status
    === "COMPLETED";


  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-indigo-600">
          Enterprise Intelligence Lifecycle
        </p>

        <h3 className="mt-2 text-2xl font-bold text-slate-950">
          Turn connected data into enterprise intelligence
        </h3>

        <p className="mt-2 max-w-3xl leading-6 text-slate-600">
          Validate the source, discover its assets,
          identify business meaning, generate findings
          and prepare trusted context for the AI Advisor.
        </p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
          {success}
        </div>
      )}

      {understandingSummary && (
        <UnderstandingSummary
          result={
            understandingSummary
          }
        />
      )}

      {intelligenceSummary && (
        <IntelligenceSummary
          result={
            intelligenceSummary
          }
        />
      )}

      <div className="space-y-3">
        <LifecycleStage
          number="1"
          icon={
            <PlugZap className="h-5 w-5" />
          }
          title="Connection"
          description="Validate that Sapientia can securely access the configured source."
          status={
            connectionStatus
          }
          message={
            lifecycle?.connection
              .last_tested_at
              ? `Last tested ${formatDate(
                  lifecycle.connection
                    .last_tested_at
                )}`
              : "Connection has not been tested."
          }
          active={
            activeAction === "test"
          }
          action={
            <StageButton
              loading={
                activeAction === "test"
              }
              disabled={
                activeAction !== null
              }
              loadingLabel="Testing..."
              onClick={runTest}
            >
              Test Connection
            </StageButton>
          }
        />

        <LifecycleStage
          number="2"
          icon={
            <Database className="h-5 w-5" />
          }
          title="Asset Discovery"
          description="Discover datasets, tables, columns, metadata, lineage and profile samples."
          status={
            lifecycle?.discovery.status
            || "PENDING"
          }
          message={
            lifecycle?.discovery.message
            || (
              lifecycle?.discovery.datasets
                ? `${lifecycle.discovery.datasets} dataset(s) and ${lifecycle.discovery.columns} column(s) are active.`
                : "No assets have been discovered."
            )
          }
          active={
            activeAction === "discovery"
          }
          action={
            <StageButton
              loading={
                activeAction
                === "discovery"
              }
              loadingLabel="Discovering..."
              disabled={
                activeAction !== null
                || ![
                  "CONNECTED",
                  "COMPLETED",
                ].includes(
                  connectionStatus
                )
              }
              onClick={runDiscovery}
            >
              Discover Assets
            </StageButton>
          }
        />

        <LifecycleStage
          number="3"
          icon={
            <Lightbulb className="h-5 w-5" />
          }
          title="Enterprise Understanding"
          description="Analyse semantic meaning, connect enterprise evidence and generate reusable business concepts."
          status={
            lifecycle?.understanding
              .status
            || "PENDING"
          }
          message={
            lifecycle?.understanding
              .message
            || (
              discoveryCompleted
                ? "Ready to build Enterprise Understanding."
                : "Discover assets before building understanding."
            )
          }
          active={
            activeAction
            === "understanding"
          }
          action={
            <StageButton
              loading={
                activeAction
                === "understanding"
              }
              loadingLabel="Building..."
              disabled={
                activeAction !== null
                || !discoveryCompleted
              }
              onClick={
                runUnderstanding
              }
            >
              {understandingCompleted
                ? "Rebuild Understanding"
                : "Build Understanding"}
            </StageButton>
          }
        />

        <LifecycleStage
          number="4"
          icon={
            <Sparkles className="h-5 w-5" />
          }
          title="Enterprise Intelligence"
          description="Generate explainable findings, a business narrative, supporting evidence and AI-ready context."
          status={
            lifecycle?.intelligence
              .status
            || "PENDING"
          }
          message={
            lifecycle?.intelligence
              .message
            || (
              understandingCompleted
                ? "Ready to generate Enterprise Intelligence."
                : "Build Enterprise Understanding first."
            )
          }
          active={
            activeAction
            === "intelligence"
          }
          action={
            <StageButton
              loading={
                activeAction
                === "intelligence"
              }
              loadingLabel="Generating..."
              disabled={
                activeAction !== null
                || !understandingCompleted
                || !lifecycle?.domain_code
              }
              onClick={
                runIntelligence
              }
            >
              {intelligenceCompleted
                ? "Regenerate Intelligence"
                : "Generate Intelligence"}
            </StageButton>
          }
        />
      </div>

      {intelligenceCompleted
        && lifecycle?.domain_code && (
        <Link
          href={
            `/workspace/${lifecycle.domain_code}`
          }
          className="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-5 py-3 font-semibold text-indigo-700 transition hover:bg-indigo-100"
        >
          Open{" "}
          {
            lifecycle.domain_name
            || lifecycle.domain_code
          }{" "}
          Workspace

          <ExternalLink className="h-4 w-4" />
        </Link>
      )}
    </div>
  );
}


function UnderstandingSummary({
  result,
}: {
  result: UnderstandingResponse;
}) {
  return (
    <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-5">
      <p className="text-sm font-semibold uppercase tracking-widest text-emerald-700">
        Understanding summary
      </p>

      <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <SummaryMetric
          label="Datasets"
          value={
            result.datasets_processed
          }
        />

        <SummaryMetric
          label="Semantic Columns"
          value={
            result.semantic_columns
          }
        />

        <SummaryMetric
          label="Evidence Links"
          value={
            result.persisted_intelligence_links
          }
        />

        <SummaryMetric
          label="Concepts"
          value={
            result.persisted_concepts
          }
        />
      </div>
    </div>
  );
}


function IntelligenceSummary({
  result,
}: {
  result: IntelligenceResponse;
}) {
  return (
    <div className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-widest text-indigo-700">
            Intelligence summary
          </p>

          {result.summary_text && (
            <p className="mt-2 max-w-3xl leading-6 text-indigo-950">
              {result.summary_text}
            </p>
          )}
        </div>

        {result.intelligence_report_id && (
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-indigo-700">
            Report #
            {
              result.intelligence_report_id
            }
          </span>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <SummaryMetric
          label="Datasets"
          value={
            result.datasets_analysed
          }
        />

        <SummaryMetric
          label="Concepts"
          value={
            result.enterprise_concepts
          }
        />

        <SummaryMetric
          label="Findings"
          value={
            result.findings_generated
          }
        />

        <SummaryMetric
          label="Evidence Links"
          value={
            result.intelligence_links
          }
        />
      </div>
    </div>
  );
}


function SummaryMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-white/80 bg-white p-3">
      <p className="text-xs uppercase tracking-wide text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-xl font-bold text-slate-950">
        {value}
      </p>
    </div>
  );
}


function LifecycleStage({
  number,
  icon,
  title,
  description,
  status,
  message,
  active,
  action,
}: {
  number: string;
  icon: ReactNode;
  title: string;
  description: string;
  status: StageStatus | string;
  message: string;
  active?: boolean;
  action: ReactNode;
}) {
  const completed =
    status === "COMPLETED"
    || status === "CONNECTED";

  const failed =
    status === "FAILED"
    || status === "ERROR";

  return (
    <div
      className={[
        "rounded-2xl border p-5 transition",

        active
          ? "border-indigo-400 bg-indigo-50 shadow-sm"
          : completed
            ? "border-emerald-200 bg-emerald-50/40"
            : failed
              ? "border-red-200 bg-red-50/40"
              : "border-slate-200 bg-white",
      ].join(" ")}
    >
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
        <div className="flex gap-4">
          <div
            className={[
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",

              active
                ? "bg-indigo-600 text-white"
                : completed
                  ? "bg-emerald-100 text-emerald-700"
                  : failed
                    ? "bg-red-100 text-red-700"
                    : "bg-slate-100 text-slate-500",
            ].join(" ")}
          >
            {active ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : completed ? (
              <Check className="h-5 w-5" />
            ) : (
              icon
            )}
          </div>

          <div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="text-xs font-bold uppercase tracking-widest text-slate-400">
                Step {number}
              </span>

              <StatusLabel
                status={status}
              />
            </div>

            <h4 className="mt-1 text-lg font-bold text-slate-950">
              {title}
            </h4>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
              {description}
            </p>

            <p className="mt-2 text-sm font-medium text-slate-500">
              {message}
            </p>
          </div>
        </div>

        <div className="shrink-0">
          {action}
        </div>
      </div>
    </div>
  );
}


function StageButton({
  children,
  loading = false,
  loadingLabel = "Processing...",
  disabled = false,
  onClick,
}: {
  children: ReactNode;
  loading?: boolean;
  loadingLabel?: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="inline-flex min-w-48 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300"
    >
      {loading && (
        <Loader2 className="h-4 w-4 animate-spin" />
      )}

      {loading
        ? loadingLabel
        : children}
    </button>
  );
}


function StatusLabel({
  status,
}: {
  status: string;
}) {
  const normalised =
    status || "PENDING";

  const classes =
    normalised === "COMPLETED"
    || normalised === "CONNECTED"
      ? "bg-emerald-100 text-emerald-700"
      : normalised === "RUNNING"
        || normalised === "DISCOVERING"
        ? "bg-indigo-100 text-indigo-700"
        : normalised === "FAILED"
          || normalised === "ERROR"
          ? "bg-red-100 text-red-700"
          : "bg-slate-100 text-slate-600";

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${classes}`}
    >
      {normalised}
    </span>
  );
}


function formatDate(
  value: string
): string {
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