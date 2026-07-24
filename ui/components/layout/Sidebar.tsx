"use client";

import { Building2, Database, LogOut, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEnterprise } from "@/components/enterprise/EnterpriseContext";
import { clearToken } from "@/lib/api";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { businessAreas, loadingBusinessAreas, selectBusinessArea } = useEnterprise();

  return (
    <aside className="vnext-sidebar">
      <div>
        <Link href="/dashboard" className="vnext-brand">
          <span className="vnext-brand-mark">S</span>
          <span><strong>Sapientia</strong><small>Enterprise Intelligence</small></span>
        </Link>
        <nav className="vnext-primary-nav" aria-label="Primary navigation">
          <Link href="/dashboard" className={pathname === "/dashboard" ? "is-active" : ""}><Building2 size={18}/> Enterprise</Link>
        </nav>
        <div className="vnext-nav-label">Business domains</div>
        <nav className="vnext-domain-nav" aria-label="Business domains">
          {loadingBusinessAreas && <span className="vnext-nav-muted">Loading domains…</span>}
          {businessAreas.map((area) => {
            const active = pathname.startsWith(`/domains/${area.domain_code}`) || pathname.startsWith(`/workspace/${area.domain_code}`);
            return <button key={area.domain_code} type="button" className={active ? "is-active" : ""} onClick={() => selectBusinessArea(area.domain_code)}><span className="vnext-domain-dot"/><span>{area.domain_name || area.domain_code}</span></button>;
          })}
        </nav>
        <div className="vnext-nav-label">Platform</div>
        <nav className="vnext-secondary-nav" aria-label="Platform navigation">
          <Link href="/sources" className={pathname === "/sources" ? "is-active" : ""}><Database size={18}/> Sources</Link>
          <Link href="/platform" className={pathname === "/platform" ? "is-active" : ""}><Settings size={18}/> Administration</Link>
        </nav>
      </div>
      <button className="vnext-signout" type="button" onClick={() => { clearToken(); router.push("/"); }}><LogOut size={17}/> Sign out</button>
    </aside>
  );
}
