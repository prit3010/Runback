import type { Run } from "@/lib/api";
import { getStatusMeta } from "@/lib/policy";
import { cn } from "@/lib/utils";

export function RunsSparkline({ runs }: { runs: Pick<Run, "id" | "status">[] }) {
  const recent = runs.slice(-14);
  return (
    <div className="flex h-6 items-end gap-1" aria-label={`${recent.length} recent runs`}>
      {recent.map((run) => (
        <span key={run.id} title={`${run.id}: ${run.status}`} className={cn("block h-5 w-2 rounded-sm", getStatusMeta(run.status).cellClassName)} />
      ))}
    </div>
  );
}
