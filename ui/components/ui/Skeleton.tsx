export default function Skeleton({
  width = "100%",
  height = 16,
  className = "",
}: {
  width?: string | number;
  height?: string | number;
  className?: string;
}) {
  return (
    <span
      className={`sap-skeleton ${className}`.trim()}
      style={{ display: "block", width, height }}
      aria-hidden="true"
    />
  );
}
