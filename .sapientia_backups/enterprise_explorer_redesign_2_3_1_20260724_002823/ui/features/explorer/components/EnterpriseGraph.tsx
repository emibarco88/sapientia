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
} from "@xyflow/react";
import { Maximize2 } from "lucide-react";
import { useEffect, useMemo } from "react";

import EnterpriseObjectNode from "@/features/explorer/components/EnterpriseObjectNode";
import { buildFlowElements } from "@/features/explorer/lib/layout";
import type { ExplorerEdge, ExplorerNode } from "@/features/explorer/types/explorer";

const nodeTypes = {
  enterpriseObject: EnterpriseObjectNode,
};

function GraphCanvas({ nodes: sourceNodes, edges: sourceEdges }: { nodes: ExplorerNode[]; edges: ExplorerEdge[] }) {
  const elements = useMemo(() => buildFlowElements(sourceNodes, sourceEdges), [sourceEdges, sourceNodes]);
  const [nodes, setNodes, onNodesChange] = useNodesState(elements.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(elements.edges);

  useEffect(() => {
    setNodes(elements.nodes);
    setEdges(elements.edges);
  }, [elements, setEdges, setNodes]);

  return (
    <div className="explorer-graph-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.22, duration: 500 }}
        minZoom={0.2}
        maxZoom={1.8}
        nodesConnectable={false}
        deleteKeyCode={null}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1.2} />
        <MiniMap pannable zoomable nodeStrokeWidth={2} />
        <Controls showInteractive={false} />
        <Panel position="top-right" className="explorer-canvas-hint">
          <Maximize2 size={13} /> Drag objects to refine the layout
        </Panel>
      </ReactFlow>
    </div>
  );
}

export default function EnterpriseGraph(props: { nodes: ExplorerNode[]; edges: ExplorerEdge[] }) {
  return (
    <ReactFlowProvider>
      <GraphCanvas {...props} />
    </ReactFlowProvider>
  );
}
