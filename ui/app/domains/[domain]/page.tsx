"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import Link from "next/link";
import { useParams } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import MetricCard from "@/components/ui/MetricCard";

export default function DomainPage() {
  const params = useParams();
  const domain = String(params.domain);

  const [summary, setSummary] = useState<any>({});
  const [concepts, setConcepts] = useState<any[]>([]);
  const [findings, setFindings] = useState<any[]>([]);

  useEffect(() => {
    async function loadDomain() {
      const data = await apiFetch(`/domains/${domain}/workspace`);
  
      setSummary(data.summary || {});
      setConcepts(data.concepts || []);
      setFindings(data.findings || []);
    }
  
    loadDomain().catch(console.error);
  }, [domain]);

  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <Link href="/dashboard" className="text-indigo-600 text-sm font-medium">
          ← Back to dashboard
        </Link>

        <div className="mt-6 mb-10">
          <p className="text-sm uppercase tracking-widest text-indigo-600 font-semibold">
            Business Domain
          </p>
          <h1 className="text-5xl font-bold text-slate-950 mt-2">{domain}</h1>
          <p className="text-slate-500 mt-3">
            Enterprise concepts, findings and intelligence generated from Sapientia.
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-5 mb-8">
          <MetricCard label="Datasets" value={summary.datasets ?? 0} />
          <MetricCard label="Semantic Columns" value={summary.semantic_columns ?? 0} />
          <MetricCard label="Concepts" value={summary.enterprise_concepts ?? 0} />
          <MetricCard label="Findings" value={summary.findings ?? 0} />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <Panel title="Enterprise Concepts">
            <div className="space-y-4">
              {concepts.map((concept) => (
                <div
                  key={concept.enterprise_concept_id}
                  className="rounded-2xl border border-slate-200 bg-white p-5 hover:border-indigo-300"
                >
                  <div className="flex justify-between gap-4">
                    <div>
                      <h3 className="text-xl font-bold text-slate-900">
                        {concept.concept_name}
                      </h3>
                      <p className="text-sm text-indigo-600 font-medium mt-1">
                        {concept.concept_type}
                      </p>
                    </div>
                    <span className="h-fit rounded-full bg-indigo-50 px-3 py-1 text-sm text-indigo-700">
                      {concept.confidence_score}
                    </span>
                  </div>

                  <p className="text-slate-600 mt-4 leading-6">
                    {concept.concept_description}
                  </p>

                  <p className="text-sm text-slate-400 mt-4">
                    Evidence records: {concept.evidence_count}
                  </p>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="AI Advisor">
            <div className="rounded-2xl bg-gradient-to-r from-indigo-50 to-fuchsia-50 p-6 mb-5">
              <h3 className="font-bold text-slate-900 mb-2">
                Ask about {domain}
              </h3>
              <p className="text-slate-600">
                Sapientia will answer using enterprise concepts, findings,
                fusion links and AI-ready intelligence context.
              </p>
            </div>

            <Link
              href={`/domains/${domain}/ask`}
              className="block rounded-xl bg-indigo-600 text-white text-center py-3 font-semibold hover:bg-indigo-500"
            >
              Ask Sapientia
            </Link>
          </Panel>
        </div>

        <Panel title="Enterprise Intelligence Findings">
          <div className="space-y-3">
            {findings.slice(0, 20).map((finding) => (
              <div
                key={finding.intelligence_finding_id}
                className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
              >
                <div className="flex justify-between gap-4 mb-2">
                  <p className="text-sm text-indigo-600 font-semibold">
                    {finding.finding_type}
                  </p>
                  <p className="text-xs rounded-full bg-slate-200 px-3 py-1 text-slate-600">
                    {finding.severity_level}
                  </p>
                </div>

                <h3 className="font-bold text-slate-900">
                  {finding.finding_title}
                </h3>

                <p className="text-slate-600 mt-2 leading-6">
                  {finding.finding_description}
                </p>

                {finding.finding_interpretation && (
                  <p className="text-sm text-slate-500 mt-3">
                    <span className="font-semibold">Why it matters:</span>{" "}
                    {finding.finding_interpretation}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </main>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
      <h2 className="text-xl font-bold mb-5 text-slate-900">{title}</h2>
      {children}
    </div>
  );
}