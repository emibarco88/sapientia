"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavigationItem = {
  label: string;
  icon: string;
  href: string;
};

type NavigationSection = {
  title: string;
  items: NavigationItem[];
};

const sections: NavigationSection[] = [
  {
    title: "Home",
    items: [
      {
        label: "Dashboard",
        icon: "🏠",
        href: "/dashboard",
      },
    ],
  },
  {
    title: "Enterprise",
    items: [
      {
        label: "Workspaces",
        icon: "🏢",
        href: "/workspaces",
      },
      {
        label: "Connectors",
        icon: "🔌",
        href: "/sources",
      },
    ],
  },
  {
    title: "AI",
    items: [
      {
        label: "Advisor",
        icon: "🤖",
        href: "/workspaces",
      },
      {
        label: "Enterprise Reasoning",
        icon: "🧠",
        href: "/workspaces",
      },
      {
        label: "Recommendations",
        icon: "💡",
        href: "/workspaces",
      },
    ],
  },
  {
    title: "Platform",
    items: [
      {
        label: "Discovery Jobs",
        icon: "🔄",
        href: "/sources",
      },
      {
        label: "Monitoring",
        icon: "📊",
        href: "/dashboard",
      },
      {
        label: "Search",
        icon: "🔎",
        href: "/dashboard",
      },
      {
        label: "Projects",
        icon: "🌐",
        href: "/dashboard",
      },
    ],
  },
  {
    title: "Administration",
    items: [
      {
        label: "Users",
        icon: "👥",
        href: "/dashboard",
      },
      {
        label: "Settings",
        icon: "⚙️",
        href: "/dashboard",
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  function isActive(item: NavigationItem): boolean {
    switch (item.label) {
      case "Dashboard":
        return pathname === "/dashboard";

      case "Workspaces":
        return (
          pathname === "/workspaces" ||
          (pathname.startsWith("/workspace/") &&
            !pathname.endsWith("/ai"))
        );

      case "Connectors":
        return pathname === "/sources";

      case "Advisor":
        return (
          pathname.startsWith("/workspace/") &&
          pathname.endsWith("/ai")
        );

      /*
       * These pages have not been implemented yet.
       * They deliberately remain inactive even though they currently
       * redirect the user to the workspace selector.
       */
      case "Enterprise Reasoning":
      case "Recommendations":
      case "Discovery Jobs":
      case "Monitoring":
      case "Search":
      case "Projects":
      case "Users":
      case "Settings":
        return false;

      default:
        return false;
    }
  }

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-72 flex-col bg-[#071333] p-6 text-white">
      <div className="mb-10">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-fuchsia-500 font-bold shadow-lg shadow-indigo-900/30">
            S
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-wide">
              SAPIENTIA
            </h1>
            <p className="text-xs text-slate-300">
              Enterprise Intelligence
            </p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 space-y-7 overflow-y-auto pr-1">
        {sections.map((section) => (
          <div key={section.title}>
            <p className="mb-3 text-xs uppercase tracking-widest text-slate-500">
              {section.title}
            </p>

            <div className="space-y-1.5">
              {section.items.map((item) => {
                const active = isActive(item);

                return (
                  <Link
                    key={`${section.title}-${item.label}`}
                    href={item.href}
                    className={`flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm transition ${
                      active
                        ? "bg-indigo-500/25 text-white"
                        : "text-slate-200 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <span className="w-5">{item.icon}</span>
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="mt-6 rounded-2xl border border-white/10 bg-white/10 p-4">
        <p className="font-semibold">Emiliano Barco</p>
        <p className="text-xs text-slate-300">Administrator</p>
      </div>
    </aside>
  );
}