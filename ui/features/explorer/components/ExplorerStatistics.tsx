import { GitBranch, Lightbulb, Network, Sparkles } from "lucide-react";

export default function ExplorerStatistics({
  nodes,
  edges,
  findings,
  recommendations,
}: {
  nodes: number;
  edges: number;
  findings: number;
  recommendations: number;
}) {
  const metrics = [
    { label: "Objects", value: nodes, icon: Network },
    { label: "Relationships", value: edges, icon: GitBranch },
    { label: "Findings", value: findings, icon: Sparkles },
    { label: "Recommendations", value: recommendations, icon: Lightbulb },
  ];

  return (
    <section className="explorer-statistics" aria-label="Enterprise graph statistics">
      {metrics.map(({ label, value, icon: Icon }) => (
        <article key={label}>
          <span><Icon size={16} aria-hidden="true" /></span>
          <div><strong>{value}</strong><small>{label}</small></div>
        </article>
      ))}
    </section>
  );
}
