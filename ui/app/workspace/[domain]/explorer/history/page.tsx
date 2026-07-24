"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, BrainCircuit, Database, History, RefreshCw, TrendingUp } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import { apiFetch } from "@/lib/api";

type CurrentState = {
  knowledge_version?: number | null;
  assessment_version?: number | null;
  overall_confidence?: number | null;
  freshness_status?: string | null;
};

type Overview = { current: CurrentState | null };
type TimelineItem = {
  event_type: string;
  event_id: number;
  version: number;
  event_at: string;
  title: string;
  details: Record<string, unknown>;
};

const label = (value?: string | null) =>
  (value || "UNKNOWN").replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());

export default function HistoryAndLineagePage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain || "").toUpperCase();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewResponse, timelineResponse] = await Promise.all([
        apiFetch<Overview>(`/phase3/domains/${encodeURIComponent(domain)}/overview?project_id=1`),
        apiFetch<{ timeline: TimelineItem[] }>(
          `/phase3/domains/${encodeURIComponent(domain)}/timeline?project_id=1&limit=100`,
        ),
      ]);
      setOverview(overviewResponse);
      setTimeline(timelineResponse.timeline || []);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "History and lineage could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [domain]);

  useEffect(() => {
    void load();
  }, [load]);

  const current = overview?.current;

  return (
    <AppShell>
      <div className="sap-page p3f-history-page">
        <header className="sap-page-header">
          <div className="sap-page-header-copy">
            <span className="sap-eyebrow">Explorer · History & Lineage</span>
            <h1 className="sap-page-title">Technical intelligence history</h1>
            <p className="sap-page-description">
              Inspect knowledge versions, assessment versions, freshness and historical provenance for {label(domain)}.
            </p>
          </div>
          <div className="p3f-header-actions">
            <Link className="sap-button sap-button-secondary" href={`/workspace/${domain}/explorer`}>
              <ArrowLeft size={16} /> Back to Explorer
            </Link>
            <button className="sap-button sap-button-secondary" onClick={() => void load()} disabled={loading}>
              <RefreshCw size={16} /> {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </header>

        {error && <div className="friendly-alert">{error}</div>}

        {loading ? (
          <p>Loading history and lineage…</p>
        ) : (
          <>
            <section className="p3f-technical-status-grid">
              <article>
                <Database size={20} />
                <span>Current Knowledge Version</span>
                <strong>{current?.knowledge_version ?? "—"}</strong>
              </article>
              <article>
                <BrainCircuit size={20} />
                <span>Latest Assessment Version</span>
                <strong>{current?.assessment_version ?? "—"}</strong>
              </article>
              <article>
                <TrendingUp size={20} />
                <span>Assessment confidence</span>
                <strong>
                  {current?.overall_confidence == null
                    ? "—"
                    : `${Math.round(Number(current.overall_confidence) * 100)}%`}
                </strong>
              </article>
              <article>
                <History size={20} />
                <span>Technical freshness state</span>
                <strong>{current?.freshness_status || "UNKNOWN"}</strong>
              </article>
            </section>

            <section className="p3f-history-panel">
              <div className="sap-section-header">
                <div>
                  <span className="sap-eyebrow">Temporal history</span>
                  <h2 className="sap-section-title">Knowledge and assessment lineage</h2>
                </div>
              </div>
              <div className="p3f-technical-timeline">
                {timeline.length === 0 ? (
                  <p>No knowledge or assessment history is available.</p>
                ) : (
                  timeline.map((item) => (
                    <article key={`${item.event_type}-${item.event_id}`}>
                      <span className={`p3f-timeline-marker ${item.event_type.toLowerCase()}`}>
                        {item.event_type === "KNOWLEDGE" ? <Database size={16} /> : <BrainCircuit size={16} />}
                      </span>
                      <div className="p3f-timeline-main">
                        <small>{new Date(item.event_at).toLocaleString("en-AU")}</small>
                        <strong>{item.title}</strong>
                        <span>
                          {label(item.event_type)} Version {item.version}
                        </span>
                        <details>
                          <summary>View technical metadata</summary>
                          <pre>{JSON.stringify(item.details || {}, null, 2)}</pre>
                        </details>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
