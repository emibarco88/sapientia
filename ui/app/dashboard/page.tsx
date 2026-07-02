"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, clearToken } from "@/lib/api";
import { useRouter } from "next/navigation";

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

  function logout() {
    clearToken();
    router.push("/");
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold">Sapientia</h1>
          <p className="text-slate-400">Enterprise Intelligence Dashboard</p>
        </div>
        <button onClick={logout} className="rounded-lg bg-slate-800 px-4 py-2">
          Logout
        </button>
      </div>

      <h2 className="text-2xl font-semibold mb-4">Business Domains</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {domains.map((domain) => (
          <Link
            key={domain.business_domain_id}
            href={`/domains/${domain.domain_code}`}
            className="rounded-2xl bg-slate-900 border border-slate-800 p-6 hover:border-blue-500"
          >
            <h3 className="text-xl font-semibold">{domain.domain_code}</h3>
            <p className="text-slate-400 mb-4">{domain.domain_name}</p>

            <div className="text-sm text-slate-300 space-y-1">
              <p>Datasets: {domain.datasets}</p>
              <p>Concepts: {domain.concepts}</p>
              <p>Reports: {domain.intelligence_reports}</p>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}