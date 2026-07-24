"use client";

import "@xyflow/react/dist/style.css";
import { ChevronLeft, Database, Expand, Eye, FileText, Focus, Network, RefreshCw, Route, X } from "lucide-react";
import { useMemo, useState } from "react";

import EnterpriseGraph from "@/features/explorer/components/EnterpriseGraph";
import ExplorerFiltersPanel from "@/features/explorer/components/ExplorerFiltersPanel";
import ExplorerStatistics from "@/features/explorer/components/ExplorerStatistics";
import { useEnterpriseGraph } from "@/features/explorer/hooks/useEnterpriseGraph";
import { businessFirstView, neighbourhood, projectSemanticGraph } from "@/features/explorer/lib/semantic-projection";
import type { ExplorerFilters, ExplorerNode } from "@/features/explorer/types/explorer";

const DEFAULT_FILTERS: ExplorerFilters = { query: "", minimumConfidence: 0, objectTypes: [], relationshipTypes: [] };
const humanise = (value: string) => value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());

export default function EnterpriseExplorer({ projectId, domain }: { projectId: number; domain: string }) {
  const [filters, setFilters] = useState<ExplorerFilters>(DEFAULT_FILTERS);
  const [selectedNode, setSelectedNode] = useState<ExplorerNode | null>(null);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [depth, setDepth] = useState(1);
  const [showTechnical, setShowTechnical] = useState(false);
  const { graph: rawGraph, loading, error, refresh } = useEnterpriseGraph({ projectId, domain, minimumConfidence: filters.minimumConfidence });

  const graph = useMemo(() => rawGraph ? projectSemanticGraph(rawGraph) : null, [rawGraph]);
  const objectTypes = useMemo(() => Object.keys(graph?.summary.object_types ?? {}).sort(), [graph]);
  const relationshipTypes = useMemo(() => Object.keys(graph?.summary.relationship_types ?? {}).sort(), [graph]);

  const baseGraph = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };
    if (focusedNodeId) return neighbourhood(graph, focusedNodeId, depth);
    if (showTechnical) return { nodes: graph.nodes, edges: graph.edges };
    return businessFirstView(graph);
  }, [depth, focusedNodeId, graph, showTechnical]);

  const visibleGraph = useMemo(() => {
    const query = filters.query.trim().toLowerCase();
    const nodes = baseGraph.nodes.filter((node) => {
      const matchesQuery = !query || [node.label, node.canonical_key, node.description ?? "", node.object_type].some((value) => value.toLowerCase().includes(query));
      const matchesType = filters.objectTypes.length === 0 || filters.objectTypes.includes(node.object_type);
      return matchesQuery && matchesType && node.confidence >= filters.minimumConfidence;
    });
    const ids = new Set(nodes.map((node) => node.id));
    const edges = baseGraph.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target) && edge.confidence >= filters.minimumConfidence && (filters.relationshipTypes.length === 0 || filters.relationshipTypes.includes(edge.relationship_type)));
    return { nodes, edges };
  }, [baseGraph, filters]);

  function focus(node: ExplorerNode) {
    setFocusedNodeId(node.id);
    setSelectedNode(node);
  }

  function resetBusinessView() {
    setFocusedNodeId(null);
    setShowTechnical(false);
  }

  if (loading) return <section className="explorer-loading-state"><span className="explorer-spin"><RefreshCw /></span><strong>Loading enterprise graph</strong><p>Building the business-first semantic view.</p></section>;
  if (!graph || graph.nodes.length === 0) return <section className="explorer-empty-state"><Network size={28} /><h3>No enterprise graph available</h3><p>Build enterprise understanding and the knowledge graph before opening Explorer.</p>{error && <p className="explorer-error">{error}</p>}</section>;

  const evidence = selectedNode?.evidence_assets ?? [];

  return <section className="enterprise-explorer-shell">
    <ExplorerStatistics nodes={graph.summary.node_count} edges={graph.summary.edge_count} findings={graph.summary.finding_count} recommendations={graph.summary.recommendation_count} />
    {error && <p className="explorer-error">{error}</p>}
    <div className={`explorer-workbench ${selectedNode ? "explorer-has-detail" : ""}`}>
      <ExplorerFiltersPanel filters={filters} objectTypes={objectTypes} relationshipTypes={relationshipTypes} onChange={setFilters} onReset={() => setFilters(DEFAULT_FILTERS)} />
      <main className="explorer-graph-panel">
        <div className="explorer-graph-toolbar">
          <div><strong>{focusedNodeId ? "Concept neighbourhood" : showTechnical ? "Full semantic and technical graph" : "Business view"}</strong><span>{visibleGraph.nodes.length} objects · {visibleGraph.edges.length} relationships · {rawGraph?.nodes.length ?? 0} source objects consolidated</span></div>
          <div className="explorer-toolbar-actions">
            {(focusedNodeId || showTechnical) && <button type="button" onClick={resetBusinessView}><ChevronLeft size={14} /> Business view</button>}
            <button type="button" onClick={() => { setFocusedNodeId(null); setShowTechnical((value) => !value); }}><Database size={14} /> {showTechnical ? "Hide technical" : "Technical view"}</button>
            <button type="button" onClick={() => void refresh()}><RefreshCw size={14} /> Refresh</button>
          </div>
        </div>
        {visibleGraph.nodes.length ? <EnterpriseGraph nodes={visibleGraph.nodes} edges={visibleGraph.edges} selectedNodeId={selectedNode?.id ?? null} onNodeSelect={setSelectedNode} /> : <div className="explorer-empty-state"><Focus size={26} /><h3>No objects match this view</h3><p>Open the technical view or reset filters.</p></div>}
      </main>
      {selectedNode && <aside className="explorer-detail-panel">
        <button className="explorer-detail-close" type="button" onClick={() => setSelectedNode(null)} aria-label="Close object details"><X size={16} /></button>
        <span className="sap-eyebrow">{selectedNode.semantic_level === "CANONICAL" ? "Canonical enterprise meaning" : "Business object"}</span>
        <h2>{selectedNode.label}</h2>
        <span className="explorer-object-type">{humanise(selectedNode.object_type)}</span>
        <p>{selectedNode.description || "No business description has been captured yet."}</p>
        <div className="explorer-detail-metrics">
          <div><strong>{Math.round(selectedNode.confidence * 100)}%</strong><span>Confidence</span></div>
          <div><strong>{evidence.length || selectedNode.incoming_count}</strong><span>{evidence.length ? "Evidence" : "Incoming"}</span></div>
          <div><strong>{selectedNode.outgoing_count}</strong><span>Outgoing</span></div>
        </div>
        <section className="explorer-detail-section">
          <h3><Route size={15} /> Progressive exploration</h3>
          <div className="explorer-depth-buttons">{[1,2,3].map((value) => <button key={value} type="button" className={depth === value ? "active" : ""} onClick={() => setDepth(value)}>{value} hop{value > 1 ? "s" : ""}</button>)}</div>
          <button className="explorer-primary-action" type="button" onClick={() => focus(selectedNode)}><Expand size={15} /> Expand this neighbourhood</button>
        </section>
        <section className="explorer-detail-section">
          <h3><Eye size={15} /> Evidence and provenance</h3>
          {evidence.length ? <div className="explorer-evidence-list">{evidence.map((asset) => <article key={asset.node_id}><div><FileText size={14}/><span><strong>{asset.label}</strong><small>{[asset.schema, asset.table].filter(Boolean).join(".") || humanise(asset.object_type)}</small></span></div><em>{Math.round(asset.confidence * 100)}%</em></article>)}</div> : <dl><div><dt>Schema</dt><dd>{selectedNode.source.schema || "—"}</dd></div><div><dt>Table</dt><dd>{selectedNode.source.table || "—"}</dd></div><div><dt>Findings</dt><dd>{selectedNode.finding_count}</dd></div><div><dt>Recommendations</dt><dd>{selectedNode.recommendation_count}</dd></div></dl>}
        </section>
      </aside>}
    </div>
  </section>;
}
