import type {
  EdgeType,
  NodeStatus,
  RecoveryPolicy,
  SideEffectStatus,
  SseEvent,
} from "@/lib/sse-types";
import type { components } from "@/lib/api-types";

export type DagNode = components["schemas"]["NodeSummary"] & {
  recovery_policy: RecoveryPolicy | string;
  status: NodeStatus | string;
  classification_reason?: string | null;
};

export interface DagEdge {
  id: string;
  run_id: string;
  branch_id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: EdgeType | string;
}

export interface DagGroup {
  id: string;
  run_id: string;
  parent_group_id?: string | null;
  label: string;
  kind: string;
  status: string;
  collapsed?: boolean;
}

export interface DagCheckpoint {
  id: string;
  run_id: string;
  branch_id: string;
  node_id?: string | null;
  label: string;
  git_ref?: string | null;
}

export interface DagSideEffect {
  node_id: string;
  kind: string;
  idempotency_key: string;
  status: SideEffectStatus | string;
  external_ref?: string | null;
}

export interface DagState {
  runId: string;
  nodes: Record<string, DagNode>;
  edges: Record<string, DagEdge>;
  checkpoints: Record<string, DagCheckpoint>;
  groups: Record<string, DagGroup>;
  sideEffects: DagSideEffect[];
  branches: string[];
}

export function createEmptyDagState(runId: string): DagState {
  return {
    runId,
    nodes: {},
    edges: {},
    checkpoints: {},
    groups: {},
    sideEffects: [],
    branches: [],
  };
}

function addBranch(state: DagState, branchId: string) {
  return state.branches.includes(branchId) ? state.branches : [...state.branches, branchId];
}

export function dagReducer(state: DagState, event: SseEvent): DagState {
  switch (event.type) {
    case "node.created": {
      const node: DagNode = {
        id: event.payload.node_id,
        run_id: event.run_id,
        branch_id: event.payload.branch_id,
        group_id: event.payload.group_id,
        type: event.payload.type,
        label: event.payload.label,
        tool_name: event.payload.tool_name,
        status: event.payload.status,
        recovery_policy: event.payload.recovery_policy,
      };
      return {
        ...state,
        nodes: { ...state.nodes, [node.id]: { ...state.nodes[node.id], ...node } },
        branches: addBranch(state, node.branch_id),
      };
    }
    case "node.updated": {
      const existing = state.nodes[event.payload.node_id];
      if (!existing) return state;
      return {
        ...state,
        nodes: {
          ...state.nodes,
          [event.payload.node_id]: {
            ...existing,
            status: event.payload.status ?? existing.status,
            output_preview: event.payload.output_preview ?? existing.output_preview,
            error: event.payload.error ?? existing.error,
            duration_ms: event.payload.duration_ms ?? existing.duration_ms,
            recovery_policy: event.payload.recovery_policy ?? existing.recovery_policy,
            classification_reason: event.payload.classification_reason ?? existing.classification_reason,
          },
        },
      };
    }
    case "edge.created": {
      const edge: DagEdge = {
        id: event.payload.edge_id,
        run_id: event.run_id,
        branch_id: event.payload.branch_id,
        source_node_id: event.payload.source_node_id,
        target_node_id: event.payload.target_node_id,
        edge_type: event.payload.edge_type,
      };
      return { ...state, edges: { ...state.edges, [edge.id]: edge }, branches: addBranch(state, edge.branch_id) };
    }
    case "checkpoint.created": {
      const checkpoint: DagCheckpoint = {
        id: event.payload.checkpoint_id,
        run_id: event.run_id,
        branch_id: event.payload.branch_id,
        label: event.payload.label,
        git_ref: event.payload.git_ref,
        node_id: event.payload.node_id,
      };
      return {
        ...state,
        checkpoints: { ...state.checkpoints, [checkpoint.id]: checkpoint },
        branches: addBranch(state, checkpoint.branch_id),
      };
    }
    case "side_effect.logged":
      return { ...state, sideEffects: [...state.sideEffects, event.payload] };
    case "replay.created":
      return { ...state, branches: addBranch({ ...state, branches: addBranch(state, event.payload.parent_branch_id) }, event.payload.new_branch_id) };
    case "group.opened":
      return {
        ...state,
        groups: {
          ...state.groups,
          [event.payload.group_id]: {
            id: event.payload.group_id,
            run_id: event.run_id,
            parent_group_id: event.payload.parent_group_id,
            label: event.payload.label,
            kind: event.payload.kind,
            status: "running",
            collapsed: false,
          },
        },
      };
    case "group.closed": {
      const existing = state.groups[event.payload.group_id];
      if (!existing) return state;
      return { ...state, groups: { ...state.groups, [event.payload.group_id]: { ...existing, status: event.payload.status } } };
    }
    default:
      return state;
  }
}
