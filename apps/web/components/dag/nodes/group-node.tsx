import { ChevronDown, ChevronRight } from "lucide-react";
import { StatusPill } from "@/components/status-pill";

export function GroupNode({ data }: { data: any }) {
  return (
    <button type="button" onClick={data.onToggle} className="flex min-w-56 items-center gap-2 rounded-lg border border-dashed bg-card px-3 py-2 text-left shadow-sm">
      {data.collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      <span className="min-w-0 flex-1 truncate text-sm font-medium">{data.label}</span>
      <StatusPill status={data.status} />
    </button>
  );
}
