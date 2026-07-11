"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import Sidebar from "@/components/layout/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import PageHeader from "@/components/ui/PageHeader";
import Panel from "@/components/ui/Panel";
import MetricCard from "@/components/ui/MetricCard";
import { apiFetch } from "@/lib/api";

export default function WorkspaceAIPage() {
  const params = useParams();
  const domain = String(params.domain);

  const [question, setQuestion] = useState(
    "Explain this business domain based on Sapientia intelligence."
  );
  const [answer, setAnswer] = useState("");
  const [metadata, setMetadata] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    setAnswer("");

    try {
      const result = await apiFetch("/ai-advisor/ask", {
        method: "POST",
        body: JSON.stringify({
          project_id: 1,
          business_domain: domain,
          question,
        }),
      });

      setAnswer(result.answer);
      setMetadata(result);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <Link
          href={`/workspace/${domain}`}
          className="text-sm font-medium text-indigo-600"
        >
          ← Back to {domain} workspace
        </Link>

        <div className="mt-6">
          <PageHeader
            label="Sapientia AI"
            title={`${domain} AI Advisor`}
            description="Ask questions grounded in Sapientia enterprise concepts, findings, fusion links and intelligence context."
          />
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <Panel
              title="Ask Sapientia"
              subtitle="The AI Advisor uses Sapientia's intelligence layer, not raw source data."
            >
              <textarea
                className="mb-4 min-h-40 w-full rounded-2xl border border-slate-200 bg-white p-4 text-slate-900 outline-none focus:border-indigo-400"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />

              <button
                onClick={ask}
                disabled={loading}
                className="rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {loading ? "Thinking..." : "Ask Sapientia"}
              </button>

              {answer && (
                <div className="mt-8 rounded-3xl border border-slate-200 bg-slate-50 p-6">
                  <h2 className="mb-4 text-2xl font-bold text-slate-950">
                    Answer
                  </h2>
                  <p className="whitespace-pre-wrap leading-7 text-slate-700">
                    {answer}
                  </p>
                </div>
              )}
            </Panel>
          </div>

          <div>
            <Panel
              title="Grounding"
              subtitle="Context used by the AI Advisor."
            >
              <div className="space-y-4">
                <MetricCard
                  label="Concepts Used"
                  value={metadata?.concepts_used ?? 0}
                />
                <MetricCard
                  label="Findings Used"
                  value={metadata?.findings_used ?? 0}
                />
                <MetricCard
                  label="Fusion Links Used"
                  value={metadata?.fusion_links_used ?? 0}
                />
              </div>

              {metadata && (
                <div className="mt-5 rounded-2xl bg-indigo-50 p-4 text-sm text-indigo-900">
                  <p>
                    Retrieval mode:{" "}
                    <span className="font-semibold">
                      {metadata.retrieval_mode}
                    </span>
                  </p>
                  <p className="mt-1">
                    Fallback used:{" "}
                    <span className="font-semibold">
                      {String(metadata.fallback_used)}
                    </span>
                  </p>
                </div>
              )}
            </Panel>
          </div>
        </div>
      </section>
    </main>
  );
}