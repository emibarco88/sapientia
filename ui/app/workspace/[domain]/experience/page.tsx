"use client";

import { useParams } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import WorkspaceTabs from "@/components/workspace/WorkspaceTabs";
import IntelligenceExperience from "@/components/intelligence-experience/IntelligenceExperience";

export default function IntelligenceExperiencePage() {
  const params = useParams<{ domain: string }>();
  const domain = decodeURIComponent(params.domain || "").toUpperCase();
  return <AppShell><div className="sap-page"><header className="sap-page-header"><div className="sap-page-header-copy"><span className="sap-eyebrow">The Enterprise Intelligence Platform</span><h1 className="sap-page-title">{domain} Intelligence Experience</h1><p className="sap-page-description">A connected view of what is happening, why it matters, how the business is changing and which evidence supports every conclusion.</p></div></header><WorkspaceTabs domain={domain}/><IntelligenceExperience domain={domain}/></div></AppShell>;
}
