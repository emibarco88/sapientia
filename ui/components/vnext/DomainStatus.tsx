export function healthLabel(findings: number, risks: number) {
  if (risks > 2) return { label: "Needs attention", tone: "attention" };
  if (risks > 0 || findings > 5) return { label: "Review advised", tone: "review" };
  return { label: "Stable", tone: "stable" };
}
