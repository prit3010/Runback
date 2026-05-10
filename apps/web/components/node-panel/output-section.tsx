import { JsonRenderer } from "@/components/artifact-viewer/json-renderer";

export function OutputSection({ value, preview }: { value?: unknown; preview?: string | null }) {
  return value ? <JsonRenderer content={value} /> : <pre className="rounded-md bg-muted p-3 text-xs">{preview || "No output yet."}</pre>;
}
