import type { Runner } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { cn } from "@/lib/utils";

function HealthPill({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 rounded-md border px-3 py-1 text-xs", ok ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950" : "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950")}>
      <span className={cn("h-2 w-2 rounded-full", ok ? "bg-emerald-500" : "bg-red-500")} />
      <span className="font-medium">{label}</span>
      <span className="text-muted-foreground">{detail}</span>
    </span>
  );
}

export function HealthRow({ runners = [] }: { runners?: Runner[] }) {
  const activeRunner = runners.find((runner) => runner.status === "online" || runner.status === "idle" || runner.status === "running") ?? runners[0];
  return (
    <div className="flex flex-wrap gap-2">
      <HealthPill label="Backend" ok detail="REST ready" />
      <HealthPill label="Runner" ok={Boolean(activeRunner)} detail={activeRunner ? timeAgo(activeRunner.last_heartbeat_at) : "offline"} />
      <HealthPill label="Claude" ok={Boolean(activeRunner?.claude_code_available)} detail={activeRunner?.version ?? "unknown"} />
    </div>
  );
}
