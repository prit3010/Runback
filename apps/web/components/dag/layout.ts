import ELK from "elkjs/lib/elk.bundled.js";
import type { components } from "@/lib/api-types";

type Node = components["schemas"]["NodeSummary"];
type Edge = components["schemas"]["Edge"];

const elk = new ELK();

export async function layoutDag(nodes: Node[], edges: Edge[]) {
  const graph = {
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.spacing.nodeNode": "40",
      "elk.layered.spacing.nodeNodeBetweenLayers": "80",
    },
    children: nodes.map((node) => ({ id: node.id, width: 220, height: 92 })),
    edges: edges.map((edge) => ({ id: edge.id, sources: [edge.source_node_id], targets: [edge.target_node_id] })),
  };
  const result = await elk.layout(graph);
  return new Map((result.children ?? []).map((node) => [node.id, { x: node.x ?? 0, y: node.y ?? 0 }]));
}
