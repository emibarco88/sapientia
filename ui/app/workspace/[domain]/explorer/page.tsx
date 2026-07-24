"use client";

import Link from "next/link";
import { History, Network } from "lucide-react";
import { useParams } from "next/navigation";
import EnterpriseExplorer from "@/features/explorer/components/EnterpriseExplorer";
import AppShell from "@/components/layout/AppShell";

export default function EnterpriseExplorerPage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain || "").toUpperCase();
  const projectId = Number(process.env.NEXT_PUBLIC_SAPIENTIA_PROJECT_ID || "1");

  return (
    <AppShell>
      <div className="vnext-page">
        <header className="vnext-domain-hero p3g-explorer-header">
          <div>
            <span className="vnext-eyebrow">Explore {domain}</span>
            <h1>Explore business knowledge and evidence.</h1>
            <p>
              Search enterprise concepts and inspect their evidence, relationships and connected business objects.
            </p>
          </div>
          <div className="p3g-explorer-header-actions">
            <span className="vnext-context-pill"><Network size={14} /> Evidence-ready knowledge</span>
            <Link className="p3g-history-link" href={`/workspace/${domain}/explorer/history`}>
              <History size={14} /> History &amp; lineage
            </Link>
          </div>
        </header>

        <EnterpriseExplorer projectId={projectId} domain={domain} />
      </div>
    </AppShell>
  );
}
