import type { components } from "@/lib/api-types";
import { ArtifactViewer } from "@/components/artifact-viewer";

export function ArtifactsSection({ artifacts = [] }: { artifacts?: components["schemas"]["Artifact"][] }) {
  if (artifacts.length === 0) return <p className="text-sm text-muted-foreground">No artifacts recorded.</p>;
  return (
    <div className="space-y-3">
      {artifacts.map((artifact) => (
        <div key={artifact.id} className="space-y-2">
          <div className="text-sm font-medium">{artifact.description || artifact.path || artifact.type}</div>
          <ArtifactViewer artifact={artifact} />
        </div>
      ))}
    </div>
  );
}
