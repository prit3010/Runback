import { PolicyBadge } from "@/components/policy-badge";
import { getStatusMeta } from "@/lib/policy";
import { cn } from "@/lib/utils";

export interface GridCellData {
  rowId: string;
  runId: string;
  nodeId: string;
  status: string;
  recoveryPolicy: string;
}

export function GridCell({ cell, onSelect }: { cell?: GridCellData; onSelect?: (cell: GridCellData) => void }) {
  if (!cell) return <div className="h-8 w-12 rounded-sm border bg-muted/40" aria-label="empty cell" />;
  return (
    <button
      type="button"
      aria-label={`${cell.nodeId} in ${cell.runId}: ${cell.status}, ${cell.recoveryPolicy}`}
      onClick={() => onSelect?.(cell)}
      className={cn("relative h-8 w-12 rounded-sm border shadow-sm transition-transform hover:scale-105", getStatusMeta(cell.status).cellClassName)}
    >
      <PolicyBadge policy={cell.recoveryPolicy} compact className="absolute left-0.5 top-0.5 px-1 py-0 text-[9px]" />
    </button>
  );
}
