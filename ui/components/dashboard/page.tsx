"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, clearToken } from "@/lib/api";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import RightPanel from "@/components/layout/RightPanel";
import MetricCard from "@/components/ui/MetricCard";

type Domain = {
  business_domain_id: number;
  domain_code: string;
  domain_name: string;
  datasets: number;
  concepts: number;
  intelligence_reports: number;
};

export default function DashboardPage() {
  const router = useRouter();
  const [domains, setDomains] = useState<Domain[]>([]);

  useEffect(() => {
    apiFetch("/domains")
      .then(setDomains)
      .catch(() => router.push("/"));
  }, [router]);

  const datasets = domains.reduce((sum, d) => sum + Number(d.datasets || 0), 0);
  const concepts = domains.reduce((sum, d) => sum + Number(d.concepts || 0), 0);
  const reports = domains.reduce((sum, d) => sum + Number(d.intelligence_reports || 0), 0);

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <main className="min-h-screen bg-[#f6f8fc]">
      <Sidebar />
      <RightPanel />

      <section className="ml-72 mr-96 p-10">
        <div className="flex justify-between items-start mb-10">
          <div>
            <h1 className="text-4xl font-bold text-slate-950">Good morning, Emiliano 👋</h1>
            <p className="text-slate-500 mt-2">
              Here&apos;s what&apos;s happening with your enterprise intelligence today.
            </p>
          </div>
          <button onClick={logout} className="rounded-xl bg-white border px-4 py-2 text-sm">
            Logout
          </button>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-5 mb-8">
          <MetricCard label="Business Domains" value={domains.length} delta="+1 this week" />
          <MetricCard label="Datasets" value={datasets} delta="+5 this week" />
          <MetricCard label="Enterprise Concepts" value={concepts} delta="+12 this week" />
          <MetricCard label="Reports" value={reports} delta="+3 this week" />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
          <Panel title="Top Business Domains">
            <div className="space-y-3">
              {domains.map((domain) => (
                <Link
                  key={domain.business_domain_id}
                  href={`/domains/${domain.domain_code}`}
                  className="flex items-center justify-between rounded-xl border border-slate-200 p-4 hover:border-indigo-400"
                >
                  <div>
                    <p className="font-semibold">{domain.domain_code}</p>
                    <p className="text-sm text-slate-500">{domain.domain_name}</p>
                  </div>
                  <div className="text-right text-sm text-slate-500">
                    <p>{domain.datasets} datasets</p>
                    <p>{domain.concepts} concepts</p>
                  </div>
                </Link>
              ))}
            </div>
          </Panel>

          <Panel title="AI Advisor">
            <div className="rounded-2xl bg-gradient-to-r from-indigo-50 to-fuchsia-50 p-6 mb-4">
              <p className="text-slate-700">
                Ask questions grounded in Sapientia&apos;s enterprise intelligence layer.
              </p>
            </div>
            <Link
              href="/domains/FINANCE/ask"
              className="block rounded-xl bg-indigo-600 text-white text-center py-3 font-semibold"
            >
              Ask Sapientia
            </Link>
          </Panel>
        </div>

        <Panel title="Recent Intelligence Findings">
          <div className="space-y-3">
            {[
              "Invoice validation rules identified",
              "Revenue concept linked to invoice totals",
              "Payment status governance detected",
              "General Ledger concept identified",
            ].map((item) => (
              <div key={item} className="rounded-xl bg-slate-50 border border-slate-200 p-4">
                {item}
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </main>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-3xl bg-white border border-slate-200 p-6 shadow-sm">
      <h2 className="text-xl font-bold mb-5 text-slate-900">{title}</h2>
      {children}
    </div>
  );
}