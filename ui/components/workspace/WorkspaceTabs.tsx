"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type WorkspaceTab = {
  label: string;
  href: (domain: string) => string;
  match: (pathname: string, domain: string) => boolean;
};

const tabs: WorkspaceTab[] = [
  {
    label: "Overview",
    href: (domain) => `/workspace/${domain}`,
    match: (pathname, domain) =>
      pathname === `/workspace/${domain}`,
  },
  {
    label: "Knowledge",
    href: (domain) => `/workspace/${domain}#knowledge`,
    match: () => false,
  },
  {
    label: "Understanding",
    href: (domain) => `/workspace/${domain}#understanding`,
    match: () => false,
  },
  {
    label: "Intelligence",
    href: (domain) => `/workspace/${domain}#intelligence`,
    match: () => false,
  },
  {
    label: "AI Advisor",
    href: (domain) => `/workspace/${domain}/ai`,
    match: (pathname, domain) =>
      pathname === `/workspace/${domain}/ai`,
  },
  {
    label: "Reports",
    href: (domain) => `/workspace/${domain}#reports`,
    match: () => false,
  },
  {
    label: "Sources",
    href: (domain) => `/workspace/${domain}#sources`,
    match: () => false,
  },
];

export default function WorkspaceTabs({
  domain,
}: {
  domain: string;
}) {
  const pathname = usePathname();

  return (
    <div className="sticky top-0 z-20 mb-8 border-b border-slate-200 bg-[#f6f8fc]/90 backdrop-blur">
      <div className="flex gap-2 overflow-x-auto">
        {tabs.map((tab) => {
          const active = tab.match(pathname, domain);

          return (
            <Link
              key={tab.label}
              href={tab.href(domain)}
              className={`whitespace-nowrap border-b-2 px-4 py-4 text-sm font-medium transition ${
                active
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-slate-500 hover:border-indigo-300 hover:text-indigo-600"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}