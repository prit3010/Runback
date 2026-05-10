"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getNode } from "@/lib/api";
import { StatusPill } from "@/components/status-pill";
import { InputSection } from "@/components/node-panel/input-section";
import { OutputSection } from "@/components/node-panel/output-section";
import { ErrorSection } from "@/components/node-panel/error-section";
import { ArtifactsSection } from "@/components/node-panel/artifacts-section";
import { PolicySection } from "@/components/node-panel/policy-section";
import { OverrideDialog } from "@/components/node-panel/override-dialog";
import { TabsHeader } from "@/components/tabs-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent } from "@/components/ui/tabs";

export default function NodeDetailPage() {
  const params = useParams<{ id: string; nodeId: string }>();
  const node = useQuery({ queryKey: ["node", params.id, params.nodeId], queryFn: () => getNode(params.id, params.nodeId) });
  if (!node.data) return <Card><CardHeader><CardTitle>Node detail</CardTitle></CardHeader><CardContent className="text-sm text-muted-foreground">Loading node detail...</CardContent></Card>;
  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div><h1 className="text-2xl font-semibold">{node.data.label}</h1><p className="text-sm text-muted-foreground">{node.data.tool_name || node.data.type}</p></div>
        <StatusPill status={node.data.status} />
      </div>
      <Tabs defaultValue="output">
        <TabsHeader tabs={[
          { value: "output", label: "Output" },
          { value: "input", label: "Input" },
          { value: "error", label: "Error" },
          { value: "artifacts", label: "Artifacts" },
          { value: "policy", label: "Policy" },
          { value: "logs", label: "Logs" },
        ]} />
        <TabsContent value="output"><OutputSection value={node.data.output_json} preview={node.data.output_preview} /></TabsContent>
        <TabsContent value="input"><InputSection value={node.data.input_json} /></TabsContent>
        <TabsContent value="error"><ErrorSection error={node.data.error} /></TabsContent>
        <TabsContent value="artifacts"><ArtifactsSection artifacts={node.data.artifacts} /></TabsContent>
        <TabsContent value="policy" className="space-y-3"><PolicySection node={node.data} /><OverrideDialog runId={params.id} nodeId={params.nodeId} /></TabsContent>
        <TabsContent value="logs"><pre className="rounded-md bg-muted p-3 text-xs">{JSON.stringify(node.data, null, 2)}</pre></TabsContent>
      </Tabs>
    </div>
  );
}
