export function JsonRenderer({ content }: { content?: unknown }) {
  const value = typeof content === "string" ? content : JSON.stringify(content ?? {}, null, 2);
  return <pre className="max-h-80 overflow-auto rounded-md bg-muted p-3 text-xs">{value}</pre>;
}
