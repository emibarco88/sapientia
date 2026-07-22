"use client";

import { usePathname } from "next/navigation";

import EnterpriseSelector from "@/components/enterprise/EnterpriseSelector";

function moduleName(pathname: string) {
  if (pathname === "/dashboard") return "Overview";
  if (pathname === "/sources") return "Data Sources";
  if (pathname.includes("/reports")) return "Enterprise Intelligence";
  if (pathname.endsWith("/ai") || pathname.endsWith("/ask")) return "AI Advisor";
  if (pathname.includes("/workspace/") || pathname.includes("/domains/")) return "Enterprise Knowledge";
  return "Enterprise Intelligence Platform";
}

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="enterprise-header">
      <div className="enterprise-header-context">
        <EnterpriseSelector compact />
        <span className="enterprise-header-separator" aria-hidden="true" />
        <div>
          <span className="enterprise-header-kicker">Current capability</span>
          <strong className="enterprise-header-module">{moduleName(pathname)}</strong>
        </div>
      </div>
      <span className="enterprise-header-area-note">Business area selected from the sidebar</span>
    </header>
  );
}
