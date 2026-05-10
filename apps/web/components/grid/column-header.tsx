import Link from "next/link";

export function GridColumnHeader({ runId, label }: { runId: string; label: string }) {
  return (
    <Link href={`/runs/${runId}`} className="block w-12 rotate-180 truncate text-xs text-muted-foreground [writing-mode:vertical-rl]" title={label}>
      {label}
    </Link>
  );
}
