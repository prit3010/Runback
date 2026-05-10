"use client";

import { useEffect, useMemo, useState } from "react";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import type { components } from "@/lib/api-types";
import { layoutDag } from "@/components/dag/layout";
import { PromptNode } from "@/components/dag/nodes/prompt-node";
import { ToolNode } from "@/components/dag/nodes/tool-node";
import { CheckpointNode } from "@/components/dag/nodes/checkpoint-node";
import { ErrorNode } from "@/components/dag/nodes/error-node";
import { ReplayNode } from "@/components/dag/nodes/replay-node";
import { GroupNode } from "@/components/dag/nodes/group-node";
import { SequenceEdge } from "@/components/dag/edges/sequence-edge";
import { Button } from "@/components/ui/button";

type RunDagSnapshot = components["schemas"]["RunDag"];

const nodeTypes = {
  prompt: PromptNode,
  tool: ToolNode,
  checkpoint: CheckpointNode,
  error: ErrorNode,
  replay: ReplayNode,
  group: GroupNode,
};

const edgeTypes = { sequence: SequenceEdge };

function nodeType(node: components["schemas"]["NodeSummary"]) {
  if (node.status === "failed" || node.error) return "error";
  if (["prompt", "tool", "checkpoint", "replay"].includes(node.type)) return node.type;
  return "tool";
}

export function BranchPills({
  branches,
  visibleBranches,
  onChange,
}: {
  branches: string[];
  visibleBranches: Set<string> | null;
  onChange: (branches: Set<string> | null) => void;
}) {
  if (branches.length <= 1) return null;
  return (
    <div className="flex flex-wrap gap-2 border-b p-2">
      <Button size="sm" variant={!visibleBranches ? "secondary" : "outline"} onClick={() => onChange(null)}>
        all branches
      </Button>
      {branches.map((branch) => {
        const selected = !visibleBranches || visibleBranches.has(branch);
        return (
          <Button
            key={branch}
            size="sm"
            variant={selected ? "secondary" : "outline"}
            onClick={() => {
              const next = new Set(visibleBranches ?? branches);
              if (next.has(branch)) next.delete(branch);
              else next.add(branch);
              onChange(next.size === branches.length ? null : next);
            }}
          >
            {branch}
          </Button>
        );
      })}
    </div>
  );
}

export function RunDag({ dag, onSelectNode }: { dag: RunDagSnapshot; onSelectNode?: (nodeId: string) => void }) {
  const [positions, setPositions] = useState(new Map<string, { x: number; y: number }>());
  const [visibleBranches, setVisibleBranches] = useState<Set<string> | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState(new Set<string>());
  const branches = useMemo(() => Array.from(new Set(dag.nodes.map((node) => node.branch_id))), [dag.nodes]);

  useEffect(() => {
    layoutDag(dag.nodes, dag.edges).then(setPositions).catch(() => setPositions(new Map()));
  }, [dag.nodes, dag.edges]);

  const visibleNodes = useMemo(() => {
    return dag.nodes.filter((node) => {
      if (visibleBranches && !visibleBranches.has(node.branch_id)) return false;
      if (node.group_id && collapsedGroups.has(node.group_id)) return false;
      return true;
    });
  }, [collapsedGroups, dag.nodes, visibleBranches]);

  const rfNodes: Node[] = useMemo(() => {
    const baseNodes = visibleNodes.map((node, index) => ({
      id: node.id,
      type: nodeType(node),
      position: positions.get(node.id) ?? { x: index * 260, y: (index % 4) * 140 },
      data: node,
    }));
    const groupNodes = dag.groups.map((group, index) => ({
      id: `group-${group.id}`,
      type: "group",
      position: { x: 20, y: index * 90 },
      data: {
        ...group,
        collapsed: collapsedGroups.has(group.id),
        onToggle: () =>
          setCollapsedGroups((current) => {
            const next = new Set(current);
            if (next.has(group.id)) next.delete(group.id);
            else next.add(group.id);
            return next;
          }),
      },
    }));
    return [...groupNodes, ...baseNodes];
  }, [collapsedGroups, dag.groups, positions, visibleNodes]);

  const rfEdges: Edge[] = useMemo(
    () =>
      dag.edges
        .filter((edge) => (!visibleBranches || visibleBranches.has(edge.branch_id)) && visibleNodes.some((node) => node.id === edge.source_node_id) && visibleNodes.some((node) => node.id === edge.target_node_id))
        .map((edge) => ({
          id: edge.id,
          source: edge.source_node_id,
          target: edge.target_node_id,
          type: "sequence",
          data: edge,
        })),
    [dag.edges, visibleBranches, visibleNodes],
  );

  return (
    <div className="h-[620px] overflow-hidden rounded-lg border bg-card">
      <BranchPills branches={branches} visibleBranches={visibleBranches} onChange={setVisibleBranches} />
      <ReactFlow nodes={rfNodes} edges={rfEdges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} fitView onNodeClick={(_, node) => !String(node.id).startsWith("group-") && onSelectNode?.(String(node.id))}>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
