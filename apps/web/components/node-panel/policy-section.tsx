import type { components } from "@/lib/api-types";
import { PolicyBadge } from "@/components/policy-badge";

export function PolicySection({ node }: { node: components["schemas"]["NodeDetail"] | components["schemas"]["NodeSummary"] }) {
  return (
    <div className="space-y-2 rounded-md border p-3">
      <PolicyBadge policy={node.recovery_policy} />
      {"classification_reason" in node && node.classification_reason ? (
        <p className="text-sm text-muted-foreground">{node.classification_reason}</p>
      ) : (
        <p className="text-sm text-muted-foreground">No classifier reason recorded.</p>
      )}
    </div>
  );
}
