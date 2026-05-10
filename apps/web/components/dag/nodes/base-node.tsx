import { Handle, Position } from "@xyflow/react";
import { PolicyBadge } from "@/components/policy-badge";
import { StatusPill } from "@/components/status-pill";
import { MiniGantt } from "@/components/mini-gantt";
import { cn } from "@/lib/utils";

export function BaseNode({ data, tone = "border-zinc-300" }: { data: any; tone?: string }) {
  return (
    <div className={cn("relative w-56 rounded-lg border bg-card p-3 text-card-foreground shadow-sm", tone)}>
      <Handle type="target" position={Position.Left} />
      <PolicyBadge policy={data.recovery_policy} compact className="absolute left-2 top-2" />
      <div className="mb-2 flex justify-end">
        <StatusPill status={data.status} />
      </div>
      <div className="truncate text-sm font-medium" title={data.label}>
        {data.label}
      </div>
      <div className="mt-1 truncate text-xs text-muted-foreground">{data.tool_name || data.type}</div>
      <div className="mt-3">
        <MiniGantt durationMs={data.duration_ms} policy={data.recovery_policy} startedAt={data.started_at} endedAt={data.ended_at} />
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
