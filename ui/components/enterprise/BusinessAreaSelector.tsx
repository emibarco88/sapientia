"use client";

import { ChevronDown } from "lucide-react";

import { useEnterprise } from "@/components/enterprise/EnterpriseContext";

type BusinessAreaSelectorProps = {
  compact?: boolean;
  className?: string;
};

export default function BusinessAreaSelector({
  compact = false,
  className = "",
}: BusinessAreaSelectorProps) {
  const {
    businessAreas,
    selectedBusinessArea,
    loadingBusinessAreas,
    businessAreaError,
    selectBusinessArea,
  } = useEnterprise();

  const disabled = loadingBusinessAreas || businessAreas.length === 0;

  return (
    <div className={`business-area-control ${compact ? "business-area-control-compact" : ""} ${className}`.trim()}>
      {!compact && <span className="business-area-label">Business area</span>}
      <div className="business-area-select-wrap">
        <select
          aria-label="Select business area"
          className="business-area-select"
          disabled={disabled}
          onChange={(event) => selectBusinessArea(event.target.value)}
          value={selectedBusinessArea?.domain_code || ""}
          title={businessAreaError || "Choose the business area to explore"}
        >
          {loadingBusinessAreas && <option value="">Loading business areas…</option>}
          {!loadingBusinessAreas && businessAreas.length === 0 && (
            <option value="">No business areas available</option>
          )}
          {businessAreas.map((area) => (
            <option key={area.domain_code} value={area.domain_code}>
              {area.domain_name || area.domain_code}
            </option>
          ))}
        </select>
        <ChevronDown aria-hidden="true" className="business-area-chevron" size={15} />
      </div>
    </div>
  );
}
