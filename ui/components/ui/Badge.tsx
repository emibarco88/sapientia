import type { ReactNode } from "react";

type BadgeTone = "neutral" | "primary" | "success" | "warning" | "danger";

export default function Badge({
  children,
  tone = "neutral",
  className = "",
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span className={`sap-badge sap-badge-${tone} ${className}`.trim()}>
      {children}
    </span>
  );
}
