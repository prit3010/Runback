import { diffLines } from "diff";

export function DiffRenderer({ content }: { content?: string | null }) {
  return (
    <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">
      {diffLines("", content ?? "").map((part, index) => (
        <span key={index} className={part.added ? "text-emerald-600" : part.removed ? "text-red-600" : undefined}>
          {part.value}
        </span>
      ))}
    </pre>
  );
}
