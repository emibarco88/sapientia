"use client";

import "@xyflow/react/dist/style.css";

import { ChevronLeft, Expand, FileText, Focus, Network, RefreshCw, Route, X } from "lucide-react";
import { useMemo, useState } from "react";

import EnterpriseGraph from "@/features/explorer/components/EnterpriseGraph";
import ExplorerFiltersPanel from "@/features/explorer/components/ExplorerFiltersPanel";
import ExplorerStatistics from "@/features/explorer/components/ExplorerStatistics";
import { useEnterpriseGraph } from "@/features/explorer/hooks/useEnterpriseGraph";
import { apiFetch } from "@/lib/api";
import type {
  EnterpriseGraphResponse,
  ExplorerEdge,
  ExplorerFilters,
  ExplorerNode,
} from "@/features/explorer/types/explorer";

type TraversalNode = {
  node: {
    node_id: number;
    canonical_name: string;
    canonical_key: string;
    object_type: string;
    description?: string | null;
    business_domain?: string | null;
    confidence?: number | null;
    incoming_count: number;
    outgoing_count: number;
    evidence_count: number;
    metadata?: Record<string, unknown>;
    source?: { schema_name?: string | null; table_name?: string | null; object_id?: number | null };
  };
  depth: number;
};

type TraversalRelationship = {
  relationship_id: number;
  source_node_id: number;
  target_node_id: number;
  relationship_type: string;
  confidence: number;
  evidence_count?: number;
  reasoning?: string | null;
  metadata?: Record<string, unknown>;
};

type TraversalResponse = {
  centre_node_id: number;
  max_depth: number;
  direction: string;
  nodes: TraversalNode[];
  relationships: TraversalRelationship[];
};

const DEFAULT_FILTERS: ExplorerFilters = {
  query: "",
  minimumConfidence: 0,
  objectTypes: [],
  relationshipTypes: [],
};

function normalise(value: string): string {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function traversalToGraph(traversal: TraversalResponse, fallback: EnterpriseGraphResponse): Pick<EnterpriseGraphResponse, "nodes" | "edges"> {
  const fallbackById = new Map(fallback.nodes.map((node) => [node.enterprise_object_id, node]));
  const nodes: ExplorerNode[] = traversal.nodes.map(({ node }) => fallbackById.get(node.node_id) ?? ({
    id: String(node.node_id),
    enterprise_object_id: node.node_id,
    label: node.canonical_name,
    canonical_key: node.canonical_key,
    object_type: node.object_type,
    description: node.description ?? null,
    business_domain: node.business_domain ?? fallback.business_domain,
    confidence: Number(node.confidence ?? 0),
    incoming_count: node.incoming_count,
    outgoing_count: node.outgoing_count,
    finding_count: Number(node.metadata?.finding_count ?? 0),
    recommendation_count: Number(node.metadata?.recommendation_count ?? 0),
    source: {
      schema: node.source?.schema_name ?? null,
      table: node.source?.table_name ?? null,
      object_id: node.source?.object_id ?? null,
    },
    metadata: node.metadata ?? {},
  }));

  const edges: ExplorerEdge[] = traversal.relationships.map((edge) => ({
    id: String(edge.relationship_id),
    operational_relationship_id: edge.relationship_id,
    source: String(edge.source_node_id),
    target: String(edge.target_node_id),
    relationship_type: edge.relationship_type,
    label: normalise(edge.relationship_type),
    confidence: Number(edge.confidence ?? 0),
    evidence_count: Number(edge.evidence_count ?? 0),
    discovery_class: null,
    generation_method: null,
    reasoning: edge.reasoning ?? null,
    metadata: edge.metadata ?? {},
  }));
  return { nodes, edges };
}

export default function EnterpriseExplorer({ projectId, domain }: { projectId: number; domain: string }) {
  const [filters, setFilters] = useState<ExplorerFilters>(DEFAULT_FILTERS);
  const [selectedNode, setSelectedNode] = useState<ExplorerNode | null>(null);
  const [focusedGraph, setFocusedGraph] = useState<Pick<EnterpriseGraphResponse, "nodes" | "edges"> | null>(null);
  const [depth, setDepth] = useState(2);
  const [traversalLoading, setTraversalLoading] = useState(false);
  const [navigationError, setNavigationError] = useState("");

  const { graph, loading, error, refresh } = useEnterpriseGraph({
    projectId,
    domain,
    minimumConfidence: filters.minimumConfidence,
  });

  const objectTypes = useMemo(() => Object.keys(graph?.summary.object_types ?? {}).sort(), [graph]);
  const relationshipTypes = useMemo(() => Object.keys(graph?.summary.relationship_types ?? {}).sort(), [graph]);

  const visibleGraph = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };
    const base = focusedGraph ?? graph;
    const query = filters.query.trim().toLowerCase();
    const allowedNodes = base.nodes.filter((node) => {
      const matchesQuery = !query || [node.label, node.canonical_key, node.description ?? "", node.object_type]
        .some((value) => value.toLowerCase().includes(query));
      const matchesType = filters.objectTypes.length === 0 || filters.objectTypes.includes(node.object_type);
      return matchesQuery && matchesType;
    });
    const ids = new Set(allowedNodes.map((node) => node.id));
    const edges = base.edges.filter((edge) =>
      ids.has(edge.source)
      && ids.has(edge.target)
      && edge.confidence >= filters.minimumConfidence
      && (filters.relationshipTypes.length === 0 || filters.relationshipTypes.includes(edge.relationship_type)),
    );
    return { nodes: allowedNodes, edges };
  }, [filters, focusedGraph, graph]);

  async function focusNeighbourhood(node: ExplorerNode, requestedDepth = depth) {
    if (!graph) return;
    setTraversalLoading(true);
    setNavigationError("");
    try {
      const result = await apiFetch<TraversalResponse>(
        `/enterprise-graph/v1/${projectId}/${encodeURIComponent(domain)}/nodes/${node.enterprise_object_id}/traversal?max_depth=${requestedDepth}&direction=BOTH&minimum_confidence=${filters.minimumConfidence.toFixed(2)}`,
      );
      setFocusedGraph(traversalToGraph(result, graph));
    } catch (cause) {
      setNavigationError(cause instanceof Error ? cause.message : "Unable to load the selected neighbourhood.");
    } finally {
      setTraversalLoading(false);
    }
  }

  function selectNode(node: ExplorerNode) {
    setSelectedNode(node);
  }

  function resetView() {
    setFocusedGraph(null);
    setNavigationError("");
  }

  if (loading) {
    return <section className="explorer-loading-state"><span className="explorer-spin"><RefreshCw /></span><strong>Loading enterprise graph</strong><p>Preparing enterprise objects, relationships and evidence.</p></section>;
  }

  if (!graph || graph.nodes.length === 0) {
    return <section className="explorer-empty-state"><Network size={28} /><h3>No enterprise graph available</h3><p>Build enterprise understanding and the knowledge graph before opening Explorer.</p>{error && <p className="explorer-error">{error}</p>}</section>;
  }

  return (
    <section className="enterprise-explorer-shell">
      <ExplorerStatistics
        nodes={graph.summary.node_count}
        edges={graph.summary.edge_count}
        findings={graph.summary.finding_count}
        recommendations={graph.summary.recommendation_count}
      />

      {(error || navigationError) && <p className="explorer-error">{error || navigationError}</p>}

      <div className={`explorer-workbench ${selectedNode ? "explorer-has-detail" : ""}`}>
        <ExplorerFiltersPanel
          filters={filters}
          objectTypes={objectTypes}
          relationshipTypes={relationshipTypes}
          onChange={setFilters}
          onReset={() => setFilters(DEFAULT_FILTERS)}
        />

        <main className="explorer-graph-panel">
          <div className="explorer-graph-toolbar">
            <div>
              <strong>{focusedGraph ? "Focused neighbourhood" : "Enterprise graph"}</strong>
              <span>{visibleGraph.nodes.length} objects · {visibleGraph.edges.length} relationships</span>
            </div>
            <div className="explorer-toolbar-actions">
              {focusedGraph && <button type="button" onClick={resetView}><ChevronLeft size={14} /> Full graph</button>}
              <button type="button" onClick={() => void refresh()}><RefreshCw size={14} /> Refresh</button>
            </div>
          </div>

          {traversalLoading && <div className="explorer-navigation-overlay"><RefreshCw className="explorer-spin" size={20} /><span>Building neighbourhood…</span></div>}

          {visibleGraph.nodes.length > 0 ? (
            <EnterpriseGraph
              nodes={visibleGraph.nodes}
              edges={visibleGraph.edges}
              selectedNodeId={selectedNode?.enterprise_object_id ?? null}
              onNodeSelect={selectNode}
            />
          ) : (
            <div className="explorer-empty-state"><Focus size={26} /><h3>No objects match these filters</h3><p>Reset the filters or return to the full graph.</p></div>
          )}
        </main>

        {selectedNode && (
          <aside className="explorer-detail-panel">
            <button className="explorer-detail-close" type="button" onClick={() => setSelectedNode(null)} aria-label="Close object details"><X size={16} /></button>
            <span className="sap-eyebrow">Selected enterprise object</span>
            <h2>{selectedNode.label}</h2>
            <span className="explorer-object-type">{normalise(selectedNode.object_type)}</span>
            <p>{selectedNode.description || "No business description has been captured yet."}</p>

            <div className="explorer-detail-metrics">
              <div><strong>{Math.round(selectedNode.confidence * 100)}%</strong><span>Confidence</span></div>
              <div><strong>{selectedNode.incoming_count}</strong><span>Incoming</span></div>
              <div><strong>{selectedNode.outgoing_count}</strong><span>Outgoing</span></div>
            </div>

            <section className="explorer-detail-section">
              <h3><Route size={15} /> Explore neighbourhood</h3>
              <div className="explorer-depth-buttons">
                {[1, 2, 3].map((value) => <button key={value} type="button" className={depth === value ? "active" : ""} onClick={() => setDepth(value)}>{value} hop{value > 1 ? "s" : ""}</button>)}
              </div>
              <button className="explorer-primary-action" type="button" onClick={() => void focusNeighbourhood(selectedNode)} disabled={traversalLoading}><Expand size={15} /> Focus graph on this object</button>
            </section>

            <section className="explorer-detail-section">
              <h3><FileText size={15} /> Source and evidence</h3>
              <dl>
                <div><dt>Schema</dt><dd>{selectedNode.source.schema || "—"}</dd></div>
                <div><dt>Table</dt><dd>{selectedNode.source.table || "—"}</dd></div>
                <div><dt>Findings</dt><dd>{selectedNode.finding_count}</dd></div>
                <div><dt>Recommendations</dt><dd>{selectedNode.recommendation_count}</dd></div>
              </dl>
            </section>
          </aside>
        )}
      </div>
    </section>
  );
}
