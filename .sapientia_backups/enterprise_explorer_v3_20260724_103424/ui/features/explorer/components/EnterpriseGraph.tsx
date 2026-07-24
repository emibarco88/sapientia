"use client";

import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  type NodeMouseHandler,
} from "@xyflow/react";
import { Maximize2 } from "lucide-react";
import { useEffect, useMemo } from "react";

import EnterpriseObjectNode from "@/features/explorer/components/EnterpriseObjectNode";
import { buildFlowElements } from "@/features/explorer/lib/layout";
import type { ExplorerEdge, ExplorerNode } from "@/features/explorer/types/explorer";

const nodeTypes = { enterpriseObject: EnterpriseObjectNode };

function GraphCanvas({
  nodes: sourceNodes,
  edges: sourceEdges,
  selectedNodeId,
  onNodeSelect,
}: {
  nodes: ExplorerNode[];
  edges: ExplorerEdge[];
  selectedNodeId: number | null;
  onNodeSelect: (node: ExplorerNode) => void;
}) {
  const elements = useMemo(() => buildFlowElements(sourceNodes, sourceEdges), [sourceEdges, sourceNodes]);
  const [nodes, setNodes, onNodesChange] = useNodesState(elements.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(elements.edges);

  useEffect(() => {
    setNodes(elements.nodes.map((node) => ({
      ...node,
      selected: Number(node.id) === selectedNodeId,
    })));
    setEdges(elements.edges);
  }, [elements, selectedNodeId, setEdges, setNodes]);

  const handleNodeClick: NodeMouseHandler = (_event, flowNode) => {
    const explorerNode = sourceNodes.find((node) => node.id === flowNode.id);
    if (explorerNode) onNodeSelect(explorerNode);
  };

  return (
    <div className="explorer-graph-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.24, duration: 450 }}
        minZoom={0.16}
        maxZoom={2}
        nodesConnectable={false}
        deleteKeyCode={null}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1.2} />
        <MiniMap pannable zoomable nodeStrokeWidth={2} />
        <Controls showInteractive={false} />
        <Panel position="top-right" className="explorer-canvas-hint">
          <Maximize2 size={13} /> Select a node to explore its neighbourhood
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default function EnterpriseGraph(props: {
  nodes: ExplorerNode[];
  edges: ExplorerEdge[];
  selectedNodeId: number | null;
  onNodeSelect: (node: ExplorerNode) => void;
}) {
  return (
    <ReactFlowProvider>
      <GraphCanvas {...props} />
    </ReactFlowProvider>
  );
}
