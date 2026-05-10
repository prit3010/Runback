"use client";

import type { components } from "@/lib/api-types";
import { StatusPill } from "@/components/status-pill";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from "@/components/ui/drawer";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { TabsHeader } from "@/components/tabs-header";
import { InputSection } from "@/components/node-panel/input-section";
import { OutputSection } from "@/components/node-panel/output-section";
import { ErrorSection } from "@/components/node-panel/error-section";
import { ArtifactsSection } from "@/components/node-panel/artifacts-section";
import { PolicySection } from "@/components/node-panel/policy-section";
import { OverrideDialog } from "@/components/node-panel/override-dialog";

type NodeLike = components["schemas"]["NodeDetail"] | components["schemas"]["NodeSummary"];

export function NodePanel({
  runId,
  node,
  open,
  onOpenChange,
}: {
  runId: string;
  node: NodeLike | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Drawer open={open} onOpenChange={onOpenChange} direction="right">
      <DrawerContent className="inset-y-0 left-auto right-0 mt-0 h-screen max-h-screen w-full max-w-xl rounded-none">
        {node && (
          <>
            <DrawerHeader className="border-b">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <DrawerTitle>{node.label}</DrawerTitle>
                  <p className="text-sm text-muted-foreground">{node.tool_name || node.type}</p>
                </div>
                <StatusPill status={node.status} />
              </div>
            </DrawerHeader>
            <div className="overflow-auto p-4">
              <Tabs defaultValue="output">
                <TabsHeader
                  tabs={[
                    { value: "output", label: "Output" },
                    { value: "input", label: "Input" },
                    { value: "error", label: "Error" },
                    { value: "artifacts", label: "Artifacts" },
                    { value: "policy", label: "Policy" },
                  ]}
                />
                <TabsContent value="output">
                  <OutputSection value={"output_json" in node ? node.output_json : undefined} preview={node.output_preview} />
                </TabsContent>
                <TabsContent value="input">
                  <InputSection value={"input_json" in node ? node.input_json : undefined} />
                </TabsContent>
                <TabsContent value="error">
                  <ErrorSection error={node.error} />
                </TabsContent>
                <TabsContent value="artifacts">
                  <ArtifactsSection artifacts={"artifacts" in node ? node.artifacts : []} />
                </TabsContent>
                <TabsContent value="policy" className="space-y-3">
                  <PolicySection node={node} />
                  <OverrideDialog runId={runId} nodeId={node.id} />
                </TabsContent>
              </Tabs>
            </div>
          </>
        )}
      </DrawerContent>
    </Drawer>
  );
}
