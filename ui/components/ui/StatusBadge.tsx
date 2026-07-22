type StatusTone = "neutral" | "primary" | "success" | "warning" | "danger";

export default function StatusBadge({
  label,
  tone = "neutral",
}: {
  label: string;
  tone?: StatusTone;
}) {
  return (
    <span className={`sap-status-badge sap-badge-${tone}`}>
      <span className="sap-status-dot" aria-hidden="true" />
      {label}
    </span>
  );
}
