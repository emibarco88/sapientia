"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Building2,
  Database,
  Lightbulb,
  MessageSquareText,
} from "lucide-react";

import { apiFetch } from "@/lib/api";

type Domain = {
  domain_code: string;
};

type NavigationItem = {
  label: string;
  href: string;
  icon: React.ReactNode;
  active: (pathname: string) => boolean;
};

export default function Sidebar() {
  const pathname = usePathname();
  const [domainCode, setDomainCode] = useState<string | null>(null);

  useEffect(() => {
    async function loadEnterprise() {
      try {
        const domains = await apiFetch<Domain[]>("/domains");
        const firstDomain = Array.isArray(domains) ? domains[0] : null;
        setDomainCode(firstDomain?.domain_code?.toUpperCase() || null);
      } catch {
        setDomainCode(null);
      }
    }

    void loadEnterprise();
  }, []);

  const items = useMemo<NavigationItem[]>(() => {
    const enterprisePath = domainCode
      ? `/workspace/${domainCode}`
      : "/dashboard";

    return [
      {
        label: "Enterprise",
        href: "/dashboard",
        icon: <Building2 className="h-5 w-5" />,
        active: (currentPath) => currentPath === "/dashboard",
      },
      {
        label: "Knowledge",
        href: `${enterprisePath}#understanding`,
        icon: <BookOpen className="h-5 w-5" />,
        active: (currentPath) =>
          currentPath.startsWith("/workspace/") &&
          !currentPath.includes("/reports") &&
          !currentPath.endsWith("/ai"),
      },
      {
        label: "Insights",
        href: domainCode
          ? `/workspace/${domainCode}/reports`
          : "/dashboard",
        icon: <Lightbulb className="h-5 w-5" />,
        active: (currentPath) => currentPath.includes("/reports"),
      },
      {
        label: "Enterprise Agent",
        href: domainCode
          ? `/workspace/${domainCode}/ai`
          : "/dashboard",
        icon: <MessageSquareText className="h-5 w-5" />,
        active: (currentPath) => currentPath.endsWith("/ai"),
      },
      {
        label: "Data Sources",
        href: "/sources",
        icon: <Database className="h-5 w-5" />,
        active: (currentPath) => currentPath === "/sources",
      },
    ];
  }, [domainCode]);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white px-5 py-6">
      <Link href="/dashboard" className="flex items-center gap-3 px-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-sm font-semibold text-white">
          S
        </div>
        <div>
          <p className="text-sm font-semibold tracking-[0.2em] text-slate-950">
            SAPIENTIA
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            Enterprise Intelligence
          </p>
        </div>
      </Link>

      <nav className="mt-12 space-y-1.5">
        {items.map((item) => {
          const active = item.active(pathname);

          return (
            <Link
              key={item.label}
              href={item.href}
              className={[
                "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition",
                active
                  ? "bg-slate-950 text-white"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
              ].join(" ")}
            >
              {item.icon}
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-2xl bg-slate-50 p-4">
        <p className="text-sm font-semibold text-slate-900">Emiliano Barco</p>
        <p className="mt-1 text-xs text-slate-500">Enterprise administrator</p>
      </div>
    </aside>
  );
}
