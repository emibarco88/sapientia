"use client";

import { CircleAlert, Network, RefreshCw, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import EnterpriseGraph from "@/features/explorer/components/EnterpriseGraph";
import ExplorerFiltersPanel from "@/features/explorer/components/ExplorerFiltersPanel";
import ExplorerStatistics from "@/features/explorer/components/ExplorerStatistics";
import { useEnterpriseGraph } from "@/features/explorer/hooks/useEnterpriseGraph";
import { buildEnterpriseKnowledgeGraph } from "@/features/explorer/lib/explorer-api";
import type { ExplorerFilters } from "@/features/explorer/types/explorer";

const DEFAULT_FILTERS: ExplorerFilters = {
  query: "",
  minimumConfidence: 0,
  objectTypes: [],
  relationshipTypes: [],
};

export default function EnterpriseExplorer({ projectId, domain }: { projectId: number; domain: string }) {
  const [filters, setFilters] = useState<ExplorerFilters>(DEFAULT_FILTERS);
  const [building, setBuilding] = useState(false);
  const [buildMessage, setBuildMessage] = useState("");
  const [buildError, setBuildError] = useState("");
  const { graph, loading, error, refresh } = useEnterpriseGraph({
    projectId,
    domain,
    minimumConfidence: filters.minimumConfidence,
  });

  const objectTypes = useMemo(
    () => Object.keys(graph?.summary.object_types || {}).sort(),
    [graph],
  );
  const relationshipTypes = useMemo(
    () => Object.keys(graph?.summary.relationship_types || {}).sort(),
    [graph],
  );

  const visibleGraph = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };

    const normalizedQuery = filters.query.trim().toLowerCase();
    const nodes = graph.nodes.filter((node) => {
      const typeMatches = filters.objectTypes.length === 0 || filters.objectTypes.includes(node.object_type);
      const queryMatches = !normalizedQuery || [
        node.label,
        node.canonical_key,
        node.object_type,
        node.description || "",
        node.source.schema || "",
        node.source.table || "",
      ].join(" ").toLowerCase().includes(normalizedQuery);
      return typeMatches && queryMatches;
    });

    const nodeIds = new Set(nodes.map((node) => node.id));
    const edges = graph.edges.filter((edge) => {
      const typeMatches = filters.relationshipTypes.length === 0 || filters.relationshipTypes.includes(edge.relationship_type);
      return typeMatches && nodeIds.has(edge.source) && nodeIds.has(edge.target);
    });

    return { nodes, edges };
  }, [filters, graph]);

  const visibleFindings = visibleGraph.nodes.reduce((total, node) => total + node.finding_count, 0);
  const visibleRecommendations = visibleGraph.nodes.reduce((total, node) => total + node.recommendation_count, 0);

  async function buildGraph() {
    setBuilding(true);
    setBuildError("");
    setBuildMessage("");
    try {
      const result = await buildEnterpriseKnowledgeGraph({ projectId, domain });
      setFilters(DEFAULT_FILTERS);
      setBuildMessage(
        `Built ${result.objects_generated} business objects and ${result.relationships_generated} relationships from ${result.technical_evidence_rows} evidence records.`,
      );
      await refresh();
    } catch (cause) {
      setBuildError(
        cause instanceof Error
          ? cause.message
          : "The Enterprise Knowledge Graph could not be built.",
      );
    } finally {
      setBuilding(false);
    }
  }

  return (
    <div className="enterprise-explorer-shell">
      <ExplorerStatistics
        nodes={visibleGraph.nodes.length}
        edges={visibleGraph.edges.length}
        findings={visibleFindings}
        recommendations={visibleRecommendations}
      />

      {(error || buildError) && (
        <div className="friendly-alert explorer-error" role="alert">
          <CircleAlert size={18} />
          <span>{buildError || error}</span>
          <button type="button" onClick={() => void refresh()}>Try again</button>
        </div>
      )}

      {buildMessage && (
        <div className="friendly-alert" role="status">
          <Sparkles size={18} />
          <span>{buildMessage}</span>
        </div>
      )}

      <section className="explorer-workbench">
        <ExplorerFiltersPanel
          filters={filters}
          objectTypes={objectTypes}
          relationshipTypes={relationshipTypes}
          onChange={setFilters}
          onReset={() => setFilters(DEFAULT_FILTERS)}
        />

        <div className="explorer-graph-panel">
          <div className="explorer-graph-header">
            <div>
              <span className="sap-eyebrow">Enterprise knowledge graph</span>
              <h2>{domain} business relationships</h2>
            </div>
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => void buildGraph()} disabled={building || loading}>
                <Sparkles size={15} className={building ? "explorer-spin" : ""} />
                {building ? "Building…" : "Build business graph"}
              </button>
              <button type="button" onClick={() => void refresh()} disabled={loading || building}>
                <RefreshCw size={15} className={loading ? "explorer-spin" : ""} /> Refresh
              </button>
            </div>
          </div>

          {loading || building ? (
            <div className="explorer-loading-state" aria-live="polite">
              <span><Network size={24} /></span>
              <strong>{building ? "Inferring business objects and relationships" : "Loading the enterprise graph"}</strong>
              <p>
                {building
                  ? "Sapientia is grouping technical evidence into business-level knowledge…"
                  : "Loading enterprise objects, relationships and intelligence signals…"}
              </p>
            </div>
          ) : visibleGraph.nodes.length ? (
            <EnterpriseGraph nodes={visibleGraph.nodes} edges={visibleGraph.edges} />
          ) : (
            <div className="explorer-empty-state">
              <Network size={30} />
              <h3>No business knowledge graph yet</h3>
              <p>
                Build the business graph to convert technical columns and semantic evidence into connected enterprise objects for {domain}.
              </p>
              <button type="button" onClick={() => void buildGraph()}>Build business graph</button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
