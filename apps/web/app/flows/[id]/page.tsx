"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQueries, useQuery } from "@tanstack/react-query";
import { getFlow, getRunDag, listRuns } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { GridView } from "@/components/grid";
import { RunDag } from "@/components/dag";
import { StatusPill } from "@/components/status-pill";
import { TabsHeader } from "@/components/tabs-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function FlowDetailPage() {
  const params = useParams<{ id: string }>();
  const flowId = params.id;
  const flow = useQuery({ queryKey: ["flow", flowId], queryFn: () => getFlow(flowId) });
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => listRuns() });
  const flowRuns = (runs.data ?? []).filter((run) => run.flow_id === flowId).slice(0, 14);
  const dagQueries = useQueries({
    queries: flowRuns.map((run) => ({ queryKey: ["run-dag", run.id], queryFn: () => getRunDag(run.id), enabled: Boolean(run.id) })),
  });
  const dags = dagQueries.map((query) => query.data).filter(Boolean);
  const latestDag = dags[0] ?? null;
  const rows = Array.from(new Map(dags.flatMap((dag) => dag?.nodes ?? []).map((node) => [node.label, { id: node.label, label: node.label }])).values());
  const cells = dags.flatMap((dag) =>
    (dag?.nodes ?? []).map((node) => ({
      rowId: node.label,
      runId: node.run_id,
      nodeId: node.id,
      status: node.status,
      recoveryPolicy: node.recovery_policy,
    })),
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{flow.data?.name ?? flowId}</h1>
          <p className="text-sm text-muted-foreground">{flow.data?.description ?? flow.data?.repo_path ?? "Flow detail"}</p>
        </div>
        <Button>New run</Button>
      </div>
      <Tabs defaultValue="grid">
        <TabsHeader tabs={[
          { value: "grid", label: "Grid" },
          { value: "graph", label: "Graph" },
          { value: "runs", label: "Runs" },
          { value: "code", label: "Code" },
          { value: "versions", label: "Versions" },
          { value: "events", label: "Events" },
          { value: "details", label: "Details" },
        ]} />
        <TabsContent value="grid">
          <GridView rows={rows} runs={flowRuns.map((run) => ({ id: run.id, label: run.id }))} cells={cells} />
        </TabsContent>
        <TabsContent value="graph">{latestDag ? <RunDag dag={latestDag} /> : <EmptyCard title="No DAG available" />}</TabsContent>
        <TabsContent value="runs">
          <Card>
            <CardHeader><CardTitle>Runs</CardTitle></CardHeader>
            <CardContent>
              <Table>
                <TableHeader><TableRow><TableHead>ID</TableHead><TableHead>Status</TableHead><TableHead>Created</TableHead></TableRow></TableHeader>
                <TableBody>{flowRuns.map((run) => <TableRow key={run.id}><TableCell><Link href={`/runs/${run.id}`} className="font-mono text-xs text-blue-600 underline">{run.id}</Link></TableCell><TableCell><StatusPill status={run.status} /></TableCell><TableCell>{formatDateTime(run.created_at)}</TableCell></TableRow>)}</TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="code"><EmptyCard title="Prompt" body={flow.data?.description ?? "Prompt history is not exposed by the current contract."} /></TabsContent>
        <TabsContent value="versions"><EmptyCard title="Versions" body="Flow versions will populate when the backend exposes version history." /></TabsContent>
        <TabsContent value="events"><EmptyCard title="Events" body="Run events are shown on run detail pages." /></TabsContent>
        <TabsContent value="details"><EmptyCard title="Details" body={flow.data ? JSON.stringify(flow.data, null, 2) : "No flow returned."} /></TabsContent>
      </Tabs>
    </div>
  );
}

function EmptyCard({ title, body }: { title: string; body?: string }) {
  return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent><pre className="whitespace-pre-wrap text-sm text-muted-foreground">{body ?? "No data."}</pre></CardContent></Card>;
}
