"use client";

import {
  BookOpen,
  Building2,
  Database,
  FileBarChart,
  LogOut,
  MessageSquareText,
  Network,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo } from "react";

import BusinessAreaSelector from "@/components/enterprise/BusinessAreaSelector";
import { useEnterprise } from "@/components/enterprise/EnterpriseContext";
import { clearToken } from "@/lib/api";

type NavigationItem = {
  label: string;
  shortLabel: string;
  href: string;
  icon: typeof Building2;
  match: (pathname: string) => boolean;
};

function getInitials(value: string) {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "SU";
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { enterpriseName, selectedBusinessArea } = useEnterprise();

  const navigation = useMemo<NavigationItem[]>(() => {
    const code = selectedBusinessArea?.domain_code ?? "";
    const knowledgeHref = code ? `/workspace/${code}` : "/workspaces";
    const intelligenceHref = code ? `/workspace/${code}/reports` : "/workspaces";
    const explorerHref = code ? `/workspace/${code}/explorer` : "/workspaces";
    const agentHref = code ? `/workspace/${code}/ai` : "/workspaces";

    return [
      {
        label: "Overview",
        shortLabel: "Overview",
        href: "/dashboard",
        icon: Building2,
        match: (value) => value === "/dashboard",
      },
      {
        label: "Knowledge",
        shortLabel: "Knowledge",
        href: knowledgeHref,
        icon: BookOpen,
        match: (value) =>
          /^\/workspace\/[^/]+$/.test(value) ||
          (/^\/domains\/[^/]+$/.test(value) && !value.endsWith("/ask")),
      },
      {
        label: "Enterprise Explorer",
        shortLabel: "Explorer",
        href: explorerHref,
        icon: Network,
        match: (value) => value.includes("/explorer"),
      },
      {
        label: "Intelligence",
        shortLabel: "Insights",
        href: intelligenceHref,
        icon: FileBarChart,
        match: (value) => value.includes("/reports"),
      },
      {
        label: "AI Advisor",
        shortLabel: "AI",
        href: agentHref,
        icon: MessageSquareText,
        match: (value) => value.endsWith("/ai") || value.endsWith("/ask"),
      },
      {
        label: "Data Sources",
        shortLabel: "Data",
        href: "/sources",
        icon: Database,
        match: (value) => value === "/sources",
      },
    ];
  }, [selectedBusinessArea]);

  function logout() {
    clearToken();
    router.push("/");
  }

  const accountName = "Sapientia User";

  return (
    <aside className="app-sidebar">
      <div>
        <Link href="/dashboard" className="brand-link" aria-label="Sapientia home">
          <span className="brand-mark">S</span>
          <span>
            <strong>Sapientia</strong>
            <small>Enterprise Intelligence</small>
          </span>
        </Link>

        <div className="sidebar-context" aria-label="Active enterprise context">
          <span className="sidebar-context-label">Enterprise</span>
          <span className="sidebar-context-name" title={enterpriseName}>
            {enterpriseName}
          </span>
          <BusinessAreaSelector compact className="sidebar-business-area" />
        </div>

        <nav className="sidebar-navigation" aria-label="Enterprise navigation">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = item.match(pathname);

            return (
              <Link
                href={item.href}
                className={`sidebar-link ${active ? "sidebar-link-active" : ""}`}
                key={item.label}
                aria-current={active ? "page" : undefined}
              >
                <Icon size={18} aria-hidden="true" />
                <span className="sidebar-label-full">{item.label}</span>
                <span className="sidebar-label-short">{item.shortLabel}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-profile">
          <span className="profile-avatar">{getInitials(accountName)}</span>
          <span>
            <strong>{accountName}</strong>
            <small>Administrator</small>
          </span>
        </div>

        <button className="sidebar-logout" onClick={logout} type="button">
          <LogOut size={17} aria-hidden="true" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
