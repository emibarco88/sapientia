"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrainCircuit, FileText, LayoutDashboard, Network, Sparkles } from "lucide-react";

const items = (domain: string) => [
  { label: "Overview", href: `/domains/${domain}`, icon: LayoutDashboard, match: [`/domains/${domain}`, `/workspace/${domain}`] },
  { label: "Intelligence", href: `/workspace/${domain}/intelligence`, icon: Sparkles },
  { label: "Reports", href: `/workspace/${domain}/reports`, icon: FileText },
  { label: "Explorer", href: `/workspace/${domain}/explorer`, icon: Network },
  { label: "AI Advisor", href: `/workspace/${domain}/ai`, icon: BrainCircuit },
];

export function domainFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/(?:domains|workspace)\/([^/?#]+)/);
  return match ? decodeURIComponent(match[1]).toUpperCase() : null;
}

export default function DomainContextNav({ domain: suppliedDomain }: { domain?: string }) {
  const pathname = usePathname();
  const domain = (suppliedDomain || domainFromPath(pathname) || "").toUpperCase();
  if (!domain) return null;

  return (
    <div className="p2c-domain-context">
      <div className="p2c-domain-context-heading">
        <Link href={`/domains/${domain}`} className="p2c-domain-home-link">
          <span className="p2c-domain-dot" />
          <span><small>Business domain</small><strong>{domain}</strong></span>
        </Link>
        <span className="p2c-domain-context-label">Domain workspace</span>
      </div>
      <nav className="p2c-domain-tabs" aria-label={`${domain} workspace navigation`}>
        {items(domain).map(({ label, href, icon: Icon, match }) => {
          const active = match
            ? match.includes(pathname)
            : pathname.startsWith(href) ||
              (label === "Intelligence" && (
                pathname.startsWith(`/workspace/${domain}/executive-intelligence`) ||
                pathname.startsWith(`/workspace/${domain}/evolution`)
              ));
          return <Link key={label} href={href} className={active ? "is-active" : ""}><Icon size={16}/><span>{label}</span></Link>;
        })}
      </nav>
    </div>
  );
}
