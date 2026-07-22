import type { ReactNode } from "react";

export default function PageHeader({
  eyebrow,
  label,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  label?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  const resolvedEyebrow = eyebrow ?? label;

  return (
    <header className="sap-page-header">
      <div className="sap-page-header-copy">
        {resolvedEyebrow ? <span className="sap-eyebrow">{resolvedEyebrow}</span> : null}
        <h1 className="sap-page-title">{title}</h1>
        {description ? <p className="sap-page-description">{description}</p> : null}
      </div>
      {actions}
    </header>
  );
}
