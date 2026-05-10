import { marked } from "marked";

export function MarkdownRenderer({ content }: { content?: string | null }) {
  return (
    <div
      className="prose prose-sm max-w-none rounded-md border p-3 dark:prose-invert"
      dangerouslySetInnerHTML={{ __html: marked.parse(content || "No markdown preview available.") as string }}
    />
  );
}
