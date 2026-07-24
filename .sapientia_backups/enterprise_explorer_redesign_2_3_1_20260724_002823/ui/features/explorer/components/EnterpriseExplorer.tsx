"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronRight, CircleDot, Network, RefreshCw } from "lucide-react";

import { apiFetch } from "@/lib/api";

type GraphNode = {
  node_id: number;
  canonical_name: string;
  object_type: string;
  description?: string | null;
  confidence?: number | null;
  incoming_count: number;
  outgoing_count: number;
  evidence_count: number;
};

type GraphRelationship = {
  relationship_id: number;
  source_node_id: number;
  target_node_id: number;
  relationship_type: string;
  confidence: number;
};

type GraphResponse = {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
  statistics: {
    node_count: number;
    relationship_count: number;
    evidence_count: number;
  };
};

type TraversalResponse = {
  centre_node_id: number;
  max_depth: number;
  direction: string;
  nodes: Array<{ node: GraphNode; depth: number }>;
  relationships: GraphRelationship[];
};

export default function EnterpriseExplorer({ projectId, domain }: { projectId: number; domain: string }) {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<number | null>(null);
  const [traversal, setTraversal] = useState<TraversalResponse | null>(null);
  const [depth, setDepth] = useState(2);
  const [loading, setLoading] = useState(true);
  const [navigationLoading, setNavigationLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedNode = useMemo(
    () => graph?.nodes.find((node) => node.node_id === selectedNodeId) ?? null,
    [graph, selectedNodeId],
  );

  async function loadGraph() {
    setLoading(true);
    setError(null);
    try {
      const result = await apiFetch<GraphResponse>(
        `/enterprise-graph/v1/${projectId}/${encodeURIComponent(domain)}?limit=500`,
      );
      setGraph(result);
      if (result.nodes.length > 0) {
        setSelectedNodeId((current) => current ?? result.nodes[0].node_id);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load the enterprise graph.");
    } finally {
      setLoading(false);
    }
  }

  async function loadTraversal(nodeId: number, requestedDepth = depth) {
    setNavigationLoading(true);
    setError(null);
    try {
      const result = await apiFetch<TraversalResponse>(
        `/enterprise-graph/v1/${projectId}/${encodeURIComponent(domain)}/nodes/${nodeId}/traversal?max_depth=${requestedDepth}&direction=BOTH`,
      );
      setTraversal(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to navigate the enterprise graph.");
    } finally {
      setNavigationLoading(false);
    }
  }

  useEffect(() => {
    void loadGraph();
  }, [projectId, domain]);

  useEffect(() => {
    if (selectedNodeId !== null) {
      void loadTraversal(selectedNodeId);
    }
  }, [selectedNodeId]);

  if (loading) {
    return <section className="explorer-navigation-card">Loading enterprise graph…</section>;
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <section className="explorer-navigation-card">
        <h2>No graph objects available</h2>
        <p>Build enterprise understanding and the knowledge graph before opening Explorer.</p>
        {error && <p className="explorer-error">{error}</p>}
      </section>
    );
  }

  return (
    <section className="enterprise-navigation-shell">
      <div className="explorer-navigation-summary">
        <div><strong>{graph.statistics.node_count}</strong><span>Objects</span></div>
        <div><strong>{graph.statistics.relationship_count}</strong><span>Relationships</span></div>
        <div><strong>{graph.statistics.evidence_count}</strong><span>Evidence links</span></div>
        <button type="button" onClick={() => void loadGraph()} aria-label="Refresh graph">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {error && <p className="explorer-error">{error}</p>}

      <div className="enterprise-navigation-grid">
        <aside className="explorer-object-list">
          <div className="explorer-panel-title"><Network size={17} /> Enterprise objects</div>
          {graph.nodes.map((node) => (
            <button
              type="button"
              key={node.node_id}
              className={node.node_id === selectedNodeId ? "active" : ""}
              onClick={() => setSelectedNodeId(node.node_id)}
            >
              <CircleDot size={14} />
              <span><strong>{node.canonical_name}</strong><small>{node.object_type.replaceAll("_", " ")}</small></span>
              <ChevronRight size={15} />
            </button>
          ))}
        </aside>

        <main className="explorer-navigation-card">
          {selectedNode && (
            <>
              <header className="explorer-node-header">
                <div>
                  <span className="sap-eyebrow">Selected enterprise object</span>
                  <h2>{selectedNode.canonical_name}</h2>
                  <p>{selectedNode.description || "No business description has been captured yet."}</p>
                </div>
                <div className="explorer-confidence">
                  <strong>{selectedNode.confidence == null ? "—" : `${Math.round(selectedNode.confidence * 100)}%`}</strong>
                  <span>Confidence</span>
                </div>
              </header>

              <div className="explorer-depth-control">
                <span>Navigation depth</span>
                {[1, 2, 3].map((value) => (
                  <button
                    type="button"
                    key={value}
                    className={depth === value ? "active" : ""}
                    onClick={() => {
                      setDepth(value);
                      void loadTraversal(selectedNode.node_id, value);
                    }}
                  >
                    {value} hop{value > 1 ? "s" : ""}
                  </button>
                ))}
              </div>

              {navigationLoading ? (
                <p>Loading connected enterprise objects…</p>
              ) : (
                <div className="explorer-traversal-list">
                  {traversal?.nodes.filter((item) => item.node.node_id !== selectedNode.node_id).map((item) => {
                    const relationships = traversal.relationships.filter(
                      (relationship) => relationship.source_node_id === item.node.node_id || relationship.target_node_id === item.node.node_id,
                    );
                    return (
                      <button type="button" key={item.node.node_id} onClick={() => setSelectedNodeId(item.node.node_id)}>
                        <span className="explorer-hop">Hop {item.depth}</span>
                        <span className="explorer-related-name">{item.node.canonical_name}</span>
                        <span className="explorer-relationship-badges">
                          {relationships.slice(0, 3).map((relationship) => (
                            <em key={relationship.relationship_id}>{relationship.relationship_type.replaceAll("_", " ")}</em>
                          ))}
                        </span>
                        <ChevronRight size={15} />
                      </button>
                    );
                  })}
                  {traversal && traversal.nodes.length === 1 && (
                    <p>No connected objects were found within the selected depth.</p>
                  )}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </section>
  );
}
