import type { Edge, Node } from "@xyflow/react";

import type { ExplorerEdge, ExplorerNode } from "@/features/explorer/types/explorer";

export type ExplorerFlowNodeData = ExplorerNode & {
  [key: string]: unknown;
};

function stableHash(value: string): number {
  return Array.from(value).reduce(
    (result, character) => ((result << 5) - result + character.charCodeAt(0)) | 0,
    0,
  );
}

export function buildFlowElements(
  nodes: ExplorerNode[],
  edges: ExplorerEdge[],
): {
  nodes: Node<ExplorerFlowNodeData>[];
  edges: Edge[];
} {
  const columns = Math.max(1, Math.ceil(Math.sqrt(nodes.length)));
  const horizontalGap = 270;
  const verticalGap = 170;

  const flowNodes: Node<ExplorerFlowNodeData>[] = nodes.map((node, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    const offset = Math.abs(stableHash(node.object_type || "UNKNOWN")) % 45;

    return {
      id: node.id,
      type: "enterpriseObject",
      position: {
        x: column * horizontalGap + (row % 2 === 0 ? 0 : 60),
        y: row * verticalGap + offset,
      },
      data: {
        ...node,
      },
      draggable: true,
      selectable: true,
    };
  });

  const flowEdges: Edge[] = edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    type: "smoothstep",
    animated: edge.confidence >= 0.85,
    selectable: true,
    data: edge,
    style: {
      strokeWidth: Math.max(1.2, 1.2 + edge.confidence * 1.8),
    },
    labelStyle: {
      fontSize: 10,
      fontWeight: 650,
    },
  }));

  return { nodes: flowNodes, edges: flowEdges };
}
