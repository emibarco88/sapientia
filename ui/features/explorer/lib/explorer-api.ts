import { apiFetch } from "@/lib/api";
import type { EnterpriseGraphResponse } from "@/features/explorer/types/explorer";

export async function loadEnterpriseGraph({
  projectId,
  domain,
  minimumConfidence,
  limit = 500,
}: {
  projectId: number;
  domain: string;
  minimumConfidence: number;
  limit?: number;
}): Promise<EnterpriseGraphResponse> {
  const parameters = new URLSearchParams({
    limit: String(limit),
    minimum_confidence: minimumConfidence.toFixed(2),
  });

  return apiFetch<EnterpriseGraphResponse>(
    `/explorer/${projectId}/${encodeURIComponent(domain)}/graph?${parameters.toString()}`,
  );
}


export type KnowledgeGraphBuildResult = {
  knowledge_graph_build_run_id: number;
  project_id: number;
  business_domain: string;
  builder_version: string;
  technical_evidence_rows: number;
  objects_generated: number;
  relationships_generated: number;
  evidence_links_generated: number;
  warnings: string[];
};

export async function buildEnterpriseKnowledgeGraph({
  projectId,
  domain,
}: {
  projectId: number;
  domain: string;
}): Promise<KnowledgeGraphBuildResult> {
  return apiFetch<KnowledgeGraphBuildResult>(
    `/knowledge-graph/${projectId}/${encodeURIComponent(domain)}/build`,
    { method: "POST" },
  );
}
