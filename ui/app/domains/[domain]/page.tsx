"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function DomainPage() {
  const params = useParams();
  const domain = String(params.domain);

  const [summary, setSummary] = useState<any>({});
  const [concepts, setConcepts] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);

  useEffect(() => {
    apiFetch(`/domains/${domain}/summary`).then(setSummary);
    apiFetch(`/concepts/${domain}`).then(setConcepts);
    apiFetch(`/intelligence/${domain}/findings`).then(setFindings);
  }, [domain]);

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <Link href="/dashboard" className="text-blue-400">← Dashboard</Link>

      <h1 className="text-4xl font-bold mt-6 mb-2">{domain}</h1>
      <p className="text-slate-400 mb-8">Enterprise Intelligence Overview</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <Metric label="Datasets" value={summary.datasets} />
        <Metric label="Semantic Columns" value={summary.semantic_columns} />
        <Metric label="Concepts" value={summary.enterprise_concepts} />
        <Metric label="Findings" value={summary.findings} />
      </div>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Enterprise Concepts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {concepts.map((concept) => (
            <div key={concept.enterprise_concept_id} className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
              <h3 className="text-xl font-semibold">{concept.concept_name}</h3>
              <p className="text-sm text-blue-300 mb-2">{concept.concept_type}</p>
              <p className="text-slate-300 mb-3">{concept.concept_description}</p>
              <p className="text-sm text-slate-400">
                Confidence: {concept.confidence_score} | Evidence: {concept.evidence_count}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-4">Latest Findings</h2>
        <div className="space-y-3">
          {findings.slice(0, 10).map((finding) => (
            <div key={finding.intelligence_finding_id} className="rounded-xl bg-slate-900 border border-slate-800 p-4">
              <p className="text-sm text-blue-300">{finding.finding_type}</p>
              <h3 className="font-semibold">{finding.finding_title}</h3>
              <p className="text-slate-400">{finding.finding_description}</p>
            </div>
          ))}
        </div>
      </section>

      <Link
        href={`/domains/${domain}/ask`}
        className="inline-block rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-500"
      >
        Ask Sapientia AI Advisor
      </Link>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
      <p className="text-slate-400 text-sm">{label}</p>
      <p className="text-3xl font-bold">{value ?? 0}</p>
    </div>
  );
}