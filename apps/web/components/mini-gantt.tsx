import { formatDuration } from "@/lib/format";
import { getPolicyMeta } from "@/lib/policy";
import { cn } from "@/lib/utils";

export function MiniGantt({
  startedAt,
  endedAt,
  durationMs,
  policy,
}: {
  startedAt?: string | null;
  endedAt?: string | null;
  durationMs?: number | null;
  policy?: string | null;
}) {
  const width = durationMs == null ? 12 : Math.min(100, Math.max(8, durationMs / 500));
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-32 rounded-full bg-muted">
        <div className={cn("h-2 rounded-full", getPolicyMeta(policy).dot)} style={{ width: `${width}%` }} title={`${startedAt ?? ""} - ${endedAt ?? ""}`} />
      </div>
      <span className="w-12 text-xs text-muted-foreground">{formatDuration(durationMs)}</span>
    </div>
  );
}
