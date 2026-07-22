"use client";

import { Building2 } from "lucide-react";

import { useEnterprise } from "@/components/enterprise/EnterpriseContext";

export default function EnterpriseSelector({ compact = false }: { compact?: boolean }) {
  const { enterpriseName } = useEnterprise();

  return (
    <div className={`enterprise-identity ${compact ? "enterprise-identity-compact" : ""}`}>
      <span className="enterprise-identity-icon">
        <Building2 aria-hidden="true" size={16} />
      </span>
      <span className="enterprise-identity-copy">
        {!compact && <small>Enterprise</small>}
        <strong>{enterpriseName}</strong>
      </span>
    </div>
  );
}
