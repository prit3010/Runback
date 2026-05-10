export function LogRenderer({ content }: { content?: string | null }) {
  return <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">{content || "No log preview available."}</pre>;
}
