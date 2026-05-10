import { cn } from "@/lib/utils";
import { getPolicyMeta } from "@/lib/policy";

export function PolicyBadge({ policy, compact = false, className }: { policy?: string | null; compact?: boolean; className?: string }) {
  const meta = getPolicyMeta(policy);
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium", meta.className, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", meta.dot)} />
      {compact ? policy?.slice(0, 2) ?? "uk" : meta.label}
    </span>
  );
}
