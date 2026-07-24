import type { EnterpriseGraphResponse, ExplorerEdge, ExplorerNode, PhysicalEvidenceAsset } from "@/features/explorer/types/explorer";

const BUSINESS_TYPES = new Set(["BUSINESS_CONCEPT", "BUSINESS_ENTITY", "BUSINESS_METRIC", "BUSINESS_PROCESS"]);
const TECHNICAL_TYPES = new Set(["COLUMN", "TABLE", "DATASET", "FIELD", "TECHNICAL_ASSET"]);

function key(value: string): string {
  return value.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function evidenceFor(node: ExplorerNode): PhysicalEvidenceAsset {
  return {
    node_id: node.enterprise_object_id,
    label: node.label,
    object_type: node.object_type,
    schema: node.source.schema,
    table: node.source.table,
    object_id: node.source.object_id,
    confidence: node.confidence,
  };
}

export function isBusinessNode(node: ExplorerNode): boolean {
  return BUSINESS_TYPES.has(node.object_type);
}

export function projectSemanticGraph(graph: EnterpriseGraphResponse): EnterpriseGraphResponse {
  const groups = new Map<string, ExplorerNode[]>();
  const passthrough: ExplorerNode[] = [];

  for (const node of graph.nodes) {
    if (TECHNICAL_TYPES.has(node.object_type)) {
      const semanticKey = key(node.label || node.canonical_key);
      const groupKey = `CANONICAL_FIELD:${semanticKey}`;
      groups.set(groupKey, [...(groups.get(groupKey) ?? []), node]);
    } else {
      passthrough.push({ ...node, semantic_level: "BUSINESS", member_node_ids: [node.enterprise_object_id], evidence_assets: [] });
    }
  }

  const canonicalNodes: ExplorerNode[] = [...groups.entries()].map(([groupKey, members]) => {
    const representative = [...members].sort((a, b) => b.confidence - a.confidence)[0];
    const confidence = members.reduce((sum, member) => sum + member.confidence, 0) / members.length;
    return {
      ...representative,
      id: groupKey,
      label: representative.label,
      canonical_key: groupKey,
      object_type: "CANONICAL_FIELD",
      description: `Canonical enterprise field supported by ${members.length} physical asset${members.length === 1 ? "" : "s"}.`,
      confidence,
      incoming_count: members.reduce((sum, member) => sum + member.incoming_count, 0),
      outgoing_count: members.reduce((sum, member) => sum + member.outgoing_count, 0),
      finding_count: members.reduce((sum, member) => sum + member.finding_count, 0),
      recommendation_count: members.reduce((sum, member) => sum + member.recommendation_count, 0),
      source: { schema: null, table: null, object_id: null },
      semantic_level: "CANONICAL",
      member_node_ids: members.map((member) => member.enterprise_object_id),
      evidence_assets: members.map(evidenceFor),
      metadata: { ...representative.metadata, physical_asset_count: members.length },
    };
  });

  const projectedNodes = [...passthrough, ...canonicalNodes];
  const projectedIdByOriginal = new Map<string, string>();
  passthrough.forEach((node) => projectedIdByOriginal.set(String(node.enterprise_object_id), node.id));
  groups.forEach((members, groupKey) => members.forEach((member) => projectedIdByOriginal.set(String(member.enterprise_object_id), groupKey)));

  const edgeMap = new Map<string, ExplorerEdge>();
  for (const edge of graph.edges) {
    const source = projectedIdByOriginal.get(edge.source);
    const target = projectedIdByOriginal.get(edge.target);
    if (!source || !target || source === target) continue;
    const edgeKey = `${source}|${edge.relationship_type}|${target}`;
    const existing = edgeMap.get(edgeKey);
    if (existing) {
      existing.evidence_count += Math.max(1, edge.evidence_count);
      existing.confidence = Math.max(existing.confidence, edge.confidence);
      existing.metadata = { ...existing.metadata, consolidated_relationship_count: Number(existing.metadata.consolidated_relationship_count ?? 1) + 1 };
    } else {
      edgeMap.set(edgeKey, {
        ...edge,
        id: `semantic:${edgeKey}`,
        source,
        target,
        evidence_count: Math.max(1, edge.evidence_count),
        metadata: { ...edge.metadata, consolidated_relationship_count: 1 },
      });
    }
  }

  const edges = [...edgeMap.values()];
  const objectTypes = projectedNodes.reduce<Record<string, number>>((result, node) => {
    result[node.object_type] = (result[node.object_type] ?? 0) + 1;
    return result;
  }, {});
  const relationshipTypes = edges.reduce<Record<string, number>>((result, edge) => {
    result[edge.relationship_type] = (result[edge.relationship_type] ?? 0) + 1;
    return result;
  }, {});

  return {
    ...graph,
    nodes: projectedNodes,
    edges,
    summary: { ...graph.summary, node_count: projectedNodes.length, edge_count: edges.length, object_types: objectTypes, relationship_types: relationshipTypes },
  };
}

export function businessFirstView(graph: EnterpriseGraphResponse): Pick<EnterpriseGraphResponse, "nodes" | "edges"> {
  let ids = new Set(graph.nodes.filter(isBusinessNode).map((node) => node.id));
  if (ids.size === 0) ids = new Set(graph.nodes.filter((node) => node.object_type === "CANONICAL_FIELD").slice(0, 12).map((node) => node.id));
  const edges = graph.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
  return { nodes: graph.nodes.filter((node) => ids.has(node.id)), edges };
}

export function neighbourhood(graph: EnterpriseGraphResponse, centreId: string, depth: number): Pick<EnterpriseGraphResponse, "nodes" | "edges"> {
  const visible = new Set<string>([centreId]);
  let frontier = new Set<string>([centreId]);
  for (let level = 0; level < depth; level += 1) {
    const next = new Set<string>();
    graph.edges.forEach((edge) => {
      if (frontier.has(edge.source)) next.add(edge.target);
      if (frontier.has(edge.target)) next.add(edge.source);
    });
    next.forEach((id) => visible.add(id));
    frontier = next;
  }
  return {
    nodes: graph.nodes.filter((node) => visible.has(node.id)),
    edges: graph.edges.filter((edge) => visible.has(edge.source) && visible.has(edge.target)),
  };
}
