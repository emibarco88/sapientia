"use client";

import { Network, Sparkles } from "lucide-react";
import { useParams } from "next/navigation";

import EnterpriseExplorer from "@/features/explorer/components/EnterpriseExplorer";
import AppShell from "@/components/layout/AppShell";
import WorkspaceTabs from "@/components/workspace/WorkspaceTabs";

export default function EnterpriseExplorerPage() {
  const params = useParams();
  const domain = String(params.domain || "").toUpperCase();
  const projectId = Number(process.env.NEXT_PUBLIC_SAPIENTIA_PROJECT_ID || "1");

  return (
    <AppShell>
      <div className="sap-page explorer-page">
        <WorkspaceTabs domain={domain} />

        <header className="sap-page-header explorer-page-header">
          <div className="sap-page-header-copy">
            <span className="sap-eyebrow">Enterprise Explorer</span>
            <h1 className="sap-page-title">Explore how {domain} works</h1>
            <p className="sap-page-description">
              Navigate enterprise objects, operational relationships and intelligence signals in one evidence-ready view.
            </p>
          </div>
          <div className="explorer-header-badge">
            <Network size={17} />
            <span><strong>Knowledge graph</strong><small>Milestone 1</small></span>
            <Sparkles size={15} />
          </div>
        </header>

        <EnterpriseExplorer projectId={projectId} domain={domain} />
      </div>
    </AppShell>
  );
}
