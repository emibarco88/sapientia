export type PhysicalEvidenceAsset = {
  node_id: number;
  label: string;
  object_type: string;
  schema: string | null;
  table: string | null;
  object_id: number | null;
  confidence: number;
};

export type ExplorerNode = {
  id: string;
  enterprise_object_id: number;
  label: string;
  canonical_key: string;
  object_type: string;
  description: string | null;
  business_domain: string | null;
  confidence: number;
  incoming_count: number;
  outgoing_count: number;
  finding_count: number;
  recommendation_count: number;
  source: {
    schema: string | null;
    table: string | null;
    object_id: number | null;
  };
  metadata: Record<string, unknown>;
  semantic_level?: "BUSINESS" | "CANONICAL" | "TECHNICAL";
  member_node_ids?: number[];
  evidence_assets?: PhysicalEvidenceAsset[];
};

export type ExplorerEdge = {
  id: string;
  operational_relationship_id: number;
  source: string;
  target: string;
  relationship_type: string;
  label: string;
  confidence: number;
  evidence_count: number;
  discovery_class: string | null;
  generation_method: string | null;
  reasoning: string | null;
  metadata: Record<string, unknown>;
};

export type ExplorerSummary = {
  node_count: number;
  edge_count: number;
  finding_count: number;
  recommendation_count: number;
  object_types: Record<string, number>;
  relationship_types: Record<string, number>;
};

export type EnterpriseGraphResponse = {
  project_id: number;
  business_domain: string;
  summary: ExplorerSummary;
  nodes: ExplorerNode[];
  edges: ExplorerEdge[];
};

export type ExplorerFilters = {
  query: string;
  minimumConfidence: number;
  objectTypes: string[];
  relationshipTypes: string[];
};
