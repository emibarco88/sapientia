import type { ReactNode } from "react";

export default function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <section className="sap-empty-state">
      <div className="sap-empty-state-content">
        {icon ? <span className="sap-empty-state-icon">{icon}</span> : null}
        <h3>{title}</h3>
        <p>{description}</p>
        {action}
      </div>
    </section>
  );
}
