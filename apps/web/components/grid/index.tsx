import type { CSSProperties } from "react";
import { GridColumnHeader } from "@/components/grid/column-header";
import { GridRow } from "@/components/grid/row";
import type { GridCellData } from "@/components/grid/cell";

export function GridView({
  rows,
  runs,
  cells,
  onSelectCell,
}: {
  rows: { id: string; label: string }[];
  runs: { id: string; label: string }[];
  cells: GridCellData[];
  onSelectCell?: (cell: GridCellData) => void;
}) {
  return (
    <div className="overflow-auto rounded-lg border bg-card p-3">
      <div className="grid min-w-max grid-cols-[220px_repeat(var(--run-count),48px)] gap-1 pb-2" style={{ "--run-count": runs.length } as CSSProperties}>
        <div className="text-xs font-medium text-muted-foreground">Node</div>
        {runs.map((run) => (
          <GridColumnHeader key={run.id} runId={run.id} label={run.label} />
        ))}
      </div>
      <div className="space-y-1">
        {rows.map((row) => (
          <GridRow key={row.id} label={row.label} runs={runs} cells={cells.filter((cell) => cell.rowId === row.id)} onSelectCell={onSelectCell} />
        ))}
      </div>
    </div>
  );
}
