export type RecoveryPolicy =
  | "rerun"
  | "reuse_cached"
  | "restore_checkpoint"
  | "requires_approval"
  | "unsafe"
  | "unknown";

export type NodeStatus =
  | "pending"
  | "running"
  | "success"
  | "failed"
  | "skipped"
  | "reused"
  | "waiting_approval";

export type EdgeType = "sequence" | "replay_branch" | "artifact" | "checkpoint";
export type SideEffectStatus = "pending_approval" | "executed" | "blocked" | "reused";

export interface NodeCreatedPayload {
  node_id: string;
  branch_id: string;
  group_id: string | null;
  type: string;
  label: string;
  tool_name: string | null;
  recovery_policy: RecoveryPolicy;
  status: NodeStatus;
}

export interface NodeUpdatedPayload {
  node_id: string;
  status?: NodeStatus | null;
  output_preview?: string | null;
  error?: string | null;
  duration_ms?: number | null;
  recovery_policy?: RecoveryPolicy | null;
  classification_reason?: string | null;
}

export interface EdgeCreatedPayload {
  edge_id: string;
  branch_id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: EdgeType;
}

export interface CheckpointCreatedPayload {
  checkpoint_id: string;
  branch_id: string;
  label: string;
  git_ref?: string | null;
  node_id?: string | null;
}

export interface SideEffectLoggedPayload {
  node_id: string;
  kind: string;
  idempotency_key: string;
  status: SideEffectStatus;
  external_ref?: string | null;
}

export interface ReplayCreatedPayload {
  replay_id: string;
  parent_branch_id: string;
  new_branch_id: string;
  source_node_id: string;
  source_checkpoint_id: string;
}

export interface GroupOpenedPayload {
  group_id: string;
  parent_group_id: string | null;
  label: string;
  kind: string;
}

export interface GroupClosedPayload {
  group_id: string;
  status: "success" | "failed" | "skipped";
}

export type SseEvent =
  | { type: "node.created"; run_id: string; ts: string; payload: NodeCreatedPayload }
  | { type: "node.updated"; run_id: string; ts: string; payload: NodeUpdatedPayload }
  | { type: "edge.created"; run_id: string; ts: string; payload: EdgeCreatedPayload }
  | { type: "checkpoint.created"; run_id: string; ts: string; payload: CheckpointCreatedPayload }
  | { type: "side_effect.logged"; run_id: string; ts: string; payload: SideEffectLoggedPayload }
  | { type: "replay.created"; run_id: string; ts: string; payload: ReplayCreatedPayload }
  | { type: "group.opened"; run_id: string; ts: string; payload: GroupOpenedPayload }
  | { type: "group.closed"; run_id: string; ts: string; payload: GroupClosedPayload };
