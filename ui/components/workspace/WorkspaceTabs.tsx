"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  BrainCircuit,
  Database,
  FileText,
  LayoutDashboard,
  Lightbulb,
  Sparkles,
} from "lucide-react";


type WorkspaceTab = {
  label: string;
  href: string;
  icon: React.ReactNode;
  exact?: boolean;
};


export default function WorkspaceTabs({
  domain,
}: {
  domain: string;
}) {
  const pathname = usePathname();

  const basePath =
    `/workspace/${domain}`;

  const tabs: WorkspaceTab[] = [
    {
      label: "Overview",
      href: basePath,
      icon: (
        <LayoutDashboard className="h-4 w-4" />
      ),
      exact: true,
    },
    {
      label: "Assets",
      href: `${basePath}#assets`,
      icon: (
        <Database className="h-4 w-4" />
      ),
    },
    {
      label: "Understanding",
      href: `${basePath}#understanding`,
      icon: (
        <Lightbulb className="h-4 w-4" />
      ),
    },
    {
      label: "Intelligence",
      href: `${basePath}#intelligence`,
      icon: (
        <Sparkles className="h-4 w-4" />
      ),
    },
    {
      label: "Reports",
      href: `${basePath}/reports`,
      icon: (
        <FileText className="h-4 w-4" />
      ),
    },
    {
      label: "AI Advisor",
      href: `${basePath}/ai`,
      icon: (
        <BrainCircuit className="h-4 w-4" />
      ),
    },
  ];

  return (
    <nav className="mb-8 overflow-x-auto">
      <div className="flex min-w-max gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
        {tabs.map((tab) => {
          const cleanHref =
            tab.href.split("#")[0];

          const active = tab.exact
            ? pathname === cleanHref
            : (
                cleanHref !== basePath
                && pathname.startsWith(
                  cleanHref
                )
              );

          return (
            <Link
              key={tab.label}
              href={tab.href}
              className={[
                "inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition",

                active
                  ? "bg-slate-950 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
              ].join(" ")}
            >
              {tab.icon}
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}