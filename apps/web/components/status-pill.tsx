import { cn } from "@/lib/utils";
import { getStatusMeta } from "@/lib/policy";

export function StatusPill({ status, className }: { status?: string | null; className?: string }) {
  const meta = getStatusMeta(status);
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium", meta.className, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", status === "running" ? "animate-pulse bg-sky-500" : "bg-current")} />
      {meta.label}
    </span>
  );
}
