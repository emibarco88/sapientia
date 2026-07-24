"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  Activity,
  Boxes,
  CircleDollarSign,
  FileText,
  Lightbulb,
  Network,
  Workflow,
} from "lucide-react";

import type { ExplorerFlowNodeData } from "@/features/explorer/lib/layout";

function humanise(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function ObjectIcon({ objectType }: { objectType: string }) {
  if (objectType === "BUSINESS_METRIC") return <CircleDollarSign size={15} aria-hidden="true" />;
  if (objectType === "BUSINESS_PROCESS") return <Workflow size={15} aria-hidden="true" />;
  if (objectType === "BUSINESS_CONCEPT") return <Network size={15} aria-hidden="true" />;
  return <Boxes size={15} aria-hidden="true" />;
}

export default function EnterpriseObjectNode({ data, selected }: NodeProps) {
  const nodeData = data as ExplorerFlowNodeData;
  const sourceLabel = [nodeData.source?.schema, nodeData.source?.table]
    .filter(Boolean)
    .join(".");

  return (
    <article className={`explorer-node ${selected ? "explorer-node-selected" : ""}`}>
      <Handle type="target" position={Position.Left} className="explorer-node-handle" />
      <div className="explorer-node-heading">
        <span className="explorer-node-icon"><ObjectIcon objectType={nodeData.object_type} /></span>
        <div>
          <span>{humanise(nodeData.object_type || "Enterprise object")}</span>
          <strong title={nodeData.label}>{nodeData.label}</strong>
        </div>
      </div>
      <div className="explorer-node-meta">
        <span><Activity size={12} /> {Math.round((nodeData.confidence || 0) * 100)}%</span>
        <span><FileText size={12} /> {nodeData.finding_count || 0}</span>
        <span><Lightbulb size={12} /> {nodeData.recommendation_count || 0}</span>
      </div>
      {sourceLabel && <small title={sourceLabel}>{sourceLabel}</small>}
      <Handle type="source" position={Position.Right} className="explorer-node-handle" />
    </article>
  );
}
