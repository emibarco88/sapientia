import type { ReactNode } from "react";

export default function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="sap-section-header">
      <div>
        <h2 className="sap-section-title">{title}</h2>
        {description ? <p className="sap-section-description">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
