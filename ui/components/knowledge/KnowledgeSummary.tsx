import { BookOpen, Database, FileCheck2, Network } from "lucide-react";

type KnowledgeSummaryProps = {
  concepts: number;
  datasets: number;
  evidence: number;
  findings: number;
};

const metrics = [
  { key: "concepts", label: "Business concepts", icon: BookOpen },
  { key: "datasets", label: "Information sources", icon: Database },
  { key: "evidence", label: "Evidence records", icon: FileCheck2 },
  { key: "findings", label: "Connected findings", icon: Network },
] as const;

export default function KnowledgeSummary(props: KnowledgeSummaryProps) {
  return (
    <section className="knowledge-metric-grid" aria-label="Enterprise knowledge summary">
      {metrics.map(({ key, label, icon: Icon }) => (
        <article className="knowledge-metric-card" key={key}>
          <span className="knowledge-metric-icon"><Icon size={18} aria-hidden="true" /></span>
          <div>
            <strong>{props[key]}</strong>
            <span>{label}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
