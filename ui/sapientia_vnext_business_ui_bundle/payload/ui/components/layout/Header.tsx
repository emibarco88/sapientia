"use client";

import { usePathname } from "next/navigation";
import { useEnterprise } from "@/components/enterprise/EnterpriseContext";

export default function Header() {
  const pathname = usePathname();
  const { selectedBusinessArea } = useEnterprise();
  const domainName = selectedBusinessArea?.domain_name || selectedBusinessArea?.domain_code;
  const label = pathname === "/dashboard" ? "Enterprise overview" : pathname.includes("/explorer") ? "Knowledge exploration" : pathname.endsWith("/ai") ? "AI Advisor" : pathname === "/sources" ? "Enterprise sources" : domainName || "Enterprise intelligence";

  return (
    <header className="vnext-header">
      <div><span className="vnext-header-eyebrow">Current view</span><strong>{label}</strong></div>
      {domainName && pathname !== "/dashboard" && <span className="vnext-context-pill">Context: {domainName}</span>}
    </header>
  );
}
