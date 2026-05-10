import type { CSSProperties } from "react";
import { GridCell, type GridCellData } from "@/components/grid/cell";

export function GridRow({
  label,
  runs,
  cells,
  onSelectCell,
}: {
  label: string;
  runs: { id: string; label: string }[];
  cells: GridCellData[];
  onSelectCell?: (cell: GridCellData) => void;
}) {
  return (
    <div className="grid min-w-max grid-cols-[220px_repeat(var(--run-count),48px)] gap-1" style={{ "--run-count": runs.length } as CSSProperties}>
      <div className="truncate py-1 pr-2 text-sm" title={label}>
        {label}
      </div>
      {runs.map((run) => (
        <GridCell key={run.id} cell={cells.find((cell) => cell.runId === run.id)} onSelect={onSelectCell} />
      ))}
    </div>
  );
}
