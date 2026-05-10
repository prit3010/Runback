import type { components } from "@/lib/api-types";
import { DiffRenderer } from "@/components/artifact-viewer/diff-renderer";
import { JsonRenderer } from "@/components/artifact-viewer/json-renderer";
import { LogRenderer } from "@/components/artifact-viewer/log-renderer";
import { MarkdownRenderer } from "@/components/artifact-viewer/markdown-renderer";

type ArtifactLike = Partial<components["schemas"]["Artifact"]> & { content_preview?: string | null };

export function ArtifactViewer({ artifact }: { artifact: ArtifactLike }) {
  const content = artifact.content_preview ?? artifact.description ?? artifact.path ?? "";
  if (artifact.type === "json") return <JsonRenderer content={content} />;
  if (artifact.type === "diff") return <DiffRenderer content={content} />;
  if (artifact.type === "markdown") return <MarkdownRenderer content={content} />;
  return <LogRenderer content={content} />;
}
