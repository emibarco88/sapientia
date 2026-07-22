import type { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
  padding?: "none" | "sm" | "md" | "lg";
  interactive?: boolean;
};

export default function Card({
  children,
  className = "",
  padding = "md",
  interactive = false,
}: CardProps) {
  const classes = [
    "sap-card",
    padding !== "none" ? `sap-card-padding-${padding}` : "",
    interactive ? "sap-card-interactive" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <section className={classes}>{children}</section>;
}

export function CardHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="sap-card-header">
      <div>
        <h2 className="sap-card-title">{title}</h2>
        {description ? <p className="sap-card-description">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
