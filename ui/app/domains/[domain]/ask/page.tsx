"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

type AskAdvisorResponse = {
  answer: string;
  concepts_used?: number;
  findings_used?: number;
  fusion_links_used?: number;
  fallback_used?: boolean;
  [key: string]: unknown;
};

export default function AskPage() {
  const params = useParams();
  const domain = String(params.domain);

  const [question, setQuestion] = useState(
    "Explain this business domain based on Sapientia intelligence.",
  );
  const [answer, setAnswer] = useState("");
  const [metadata, setMetadata] = useState<AskAdvisorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask() {
    setLoading(true);
    setAnswer("");
    setMetadata(null);
    setError("");

    try {
      const result = await apiFetch<AskAdvisorResponse>("/ai-advisor/ask", {
        method: "POST",
        body: JSON.stringify({
          project_id: 1,
          business_domain: domain,
          question,
        }),
      });

      setAnswer(result.answer);
      setMetadata(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Sapientia could not complete the request.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 p-8 text-white">
      <Link href={`/domains/${domain}`} className="text-blue-400">
        ← {domain}
      </Link>

      <h1 className="mb-2 mt-6 text-4xl font-bold">Ask Sapientia</h1>
      <p className="mb-8 text-slate-400">
        Grounded AI Advisor using Enterprise Intelligence
      </p>

      <textarea
        className="mb-4 min-h-32 w-full rounded-2xl border border-slate-800 bg-slate-900 p-4 outline-none"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
      />

      <button
        type="button"
        onClick={ask}
        disabled={loading || !question.trim()}
        className="rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Thinking..." : "Ask"}
      </button>

      {error && (
        <section className="mt-8 rounded-2xl border border-red-900 bg-red-950/40 p-5">
          <p className="font-semibold text-red-200">
            Sapientia could not answer the question
          </p>
          <p className="mt-2 text-sm text-red-300">{error}</p>
        </section>
      )}

      {metadata && (
        <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
          <Metric
            label="Concepts Used"
            value={metadata.concepts_used ?? 0}
          />
          <Metric
            label="Findings Used"
            value={metadata.findings_used ?? 0}
          />
          <Metric
            label="Fusion Links Used"
            value={metadata.fusion_links_used ?? 0}
          />
          <Metric
            label="Fallback Used"
            value={metadata.fallback_used ? "Yes" : "No"}
          />
        </div>
      )}

      {answer && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-2xl font-semibold">Answer</h2>
          <p className="whitespace-pre-wrap leading-7 text-slate-200">
            {answer}
          </p>
        </section>
      )}
    </main>
  );
}

function Metric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="text-xl font-bold">{value}</p>
    </div>
  );
}