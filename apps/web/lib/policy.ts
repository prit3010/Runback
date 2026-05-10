export type RecoveryPolicy = "rerun" | "reuse_cached" | "restore_checkpoint" | "requires_approval" | "unsafe" | "unknown" | string;
export type NodeStatus = "pending" | "running" | "success" | "failed" | "skipped" | "reused" | "waiting_approval" | string;

export const policyMeta: Record<string, { label: string; className: string; dot: string }> = {
  rerun: { label: "rerun", className: "border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-300", dot: "bg-policy-rerun" },
  reuse_cached: { label: "reuse cached", className: "border-purple-200 bg-purple-50 text-purple-700 dark:border-purple-900 dark:bg-purple-950 dark:text-purple-300", dot: "bg-policy-reuse" },
  restore_checkpoint: { label: "restore checkpoint", className: "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900 dark:bg-orange-950 dark:text-orange-300", dot: "bg-policy-restore" },
  requires_approval: { label: "requires approval", className: "border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-900 dark:bg-yellow-950 dark:text-yellow-300", dot: "bg-policy-approval" },
  unsafe: { label: "unsafe", className: "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300", dot: "bg-policy-unsafe" },
  unknown: { label: "unknown", className: "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300", dot: "bg-policy-unknown" },
};

export const statusMeta: Record<string, { label: string; className: string; cellClassName: string }> = {
  queued: { label: "queued", className: "bg-zinc-100 text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300", cellClassName: "bg-zinc-200 dark:bg-zinc-700" },
  pending: { label: "pending", className: "bg-zinc-100 text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300", cellClassName: "bg-zinc-200 dark:bg-zinc-700" },
  running: { label: "running", className: "bg-sky-100 text-sky-700 dark:bg-sky-950 dark:text-sky-300", cellClassName: "bg-sky-400 animate-pulse" },
  success: { label: "success", className: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300", cellClassName: "bg-emerald-500" },
  failed: { label: "failed", className: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300", cellClassName: "bg-red-500" },
  cancelled: { label: "cancelled", className: "bg-zinc-100 text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300", cellClassName: "bg-zinc-400" },
  skipped: { label: "skipped", className: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300", cellClassName: "bg-amber-400" },
  reused: { label: "reused", className: "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300", cellClassName: "bg-state-reused" },
  waiting_approval: { label: "waiting approval", className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300", cellClassName: "bg-yellow-400" },
};

export function getPolicyMeta(policy?: string | null) {
  return policyMeta[policy ?? "unknown"] ?? policyMeta.unknown;
}

export function getStatusMeta(status?: string | null) {
  return statusMeta[status ?? "pending"] ?? statusMeta.pending;
}
