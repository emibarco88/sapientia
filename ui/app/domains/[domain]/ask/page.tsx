"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { useParams } from "next/navigation";
import Link from "next/link";

export default function AskPage() {
  const params = useParams();
  const domain = String(params.domain);

  const [question, setQuestion] = useState("Explain this business domain based on Sapientia intelligence.");
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
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <Link href={`/domains/${domain}`} className="text-blue-400">← {domain}</Link>

      <h1 className="text-4xl font-bold mt-6 mb-2">Ask Sapientia</h1>
      <p className="text-slate-400 mb-8">Grounded AI Advisor using Enterprise Intelligence</p>

      <textarea
        className="w-full min-h-32 rounded-2xl bg-slate-900 border border-slate-800 p-4 outline-none mb-4"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button
        onClick={ask}
        disabled={loading}
        className="rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-500 disabled:opacity-50"
      >
        {loading ? "Thinking..." : "Ask"}
      </button>

      {metadata && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          <Metric label="Concepts Used" value={metadata.concepts_used} />
          <Metric label="Findings Used" value={metadata.findings_used} />
          <Metric label="Fusion Links Used" value={metadata.fusion_links_used} />
          <Metric label="Fallback Used" value={String(metadata.fallback_used)} />
        </div>
      )}

      {answer && (
        <section className="mt-8 rounded-2xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-2xl font-semibold mb-4">Answer</h2>
          <p className="whitespace-pre-wrap text-slate-200 leading-7">{answer}</p>
        </section>
      )}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
      <p className="text-slate-400 text-sm">{label}</p>
      <p className="text-xl font-bold">{value ?? 0}</p>
    </div>
  );
}