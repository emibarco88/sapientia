"use client";

import { Network, Search, Sparkles } from "lucide-react";
import { useParams } from "next/navigation";
import EnterpriseExplorer from "@/features/explorer/components/EnterpriseExplorer";
import AppShell from "@/components/layout/AppShell";
import AskBar from "@/components/vnext/AskBar";

export default function EnterpriseExplorerPage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain || "").toUpperCase();
  const projectId = Number(process.env.NEXT_PUBLIC_SAPIENTIA_PROJECT_ID || "1");

  return (
    <AppShell>
      <div className="vnext-page">
        <header className="vnext-domain-hero">
          <div>
            <span className="vnext-eyebrow">Explore {domain}</span>
            <h1>Follow the evidence behind the business.</h1>
            <p>Search for a business concept first, then inspect its evidence, relationships and graph only when deeper investigation is useful.</p>
          </div>
          <span className="vnext-context-pill"><Network size={14} /> Evidence-ready knowledge</span>
        </header>
        <AskBar domain={domain} prompt={`Ask about a concept, process or relationship in ${domain}…`} />
        <section className="vnext-explorer-intro">
          <Search size={20} />
          <div><strong>Search first. Graph second.</strong><span>Select a result to reveal its business meaning, supporting evidence and connected enterprise objects.</span></div>
          <Sparkles size={17} />
        </section>
        <EnterpriseExplorer projectId={projectId} domain={domain} />
      </div>
    </AppShell>
  );
}
