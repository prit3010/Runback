"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getNode, getRunDag } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/format";
import { GridView } from "@/components/grid";
import { RunDag } from "@/components/dag";
import { MiniGantt } from "@/components/mini-gantt";
import { NodePanel } from "@/components/node-panel";
import { ReplayModal } from "@/components/replay-modal";
import { SideEffectLog } from "@/components/side-effect-log";
import { StatusPill } from "@/components/status-pill";
import { TabsHeader } from "@/components/tabs-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [replayOpen, setReplayOpen] = useState(false);
  const dag = useQuery({ queryKey: ["run-dag", runId], queryFn: () => getRunDag(runId) });
  const node = useQuery({ queryKey: ["node", runId, selectedNodeId], queryFn: () => selectedNodeId ? getNode(runId, selectedNodeId) : Promise.resolve(null), enabled: Boolean(selectedNodeId) });
  const selectedNode = node.data ?? dag.data?.nodes.find((item) => item.id === selectedNodeId) ?? null;

  const grid = useMemo(() => {
    const nodes = dag.data?.nodes ?? [];
    return {
      rows: nodes.map((item) => ({ id: item.id, label: item.label })),
      runs: [{ id: runId, label: runId }],
      cells: nodes.map((item) => ({ rowId: item.id, runId, nodeId: item.id, status: item.status, recoveryPolicy: item.recovery_policy })),
    };
  }, [dag.data?.nodes, runId]);

  if (!dag.data) return <EmptyCard title="Run detail" body={dag.isLoading ? "Loading run DAG..." : "No DAG returned by backend."} />;
  const run = dag.data.run;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2"><h1 className="text-2xl font-semibold">{run.id}</h1><StatusPill status={run.status} /></div>
          <p className="max-w-4xl truncate text-sm text-muted-foreground">{run.original_prompt}</p>
        </div>
        <Button disabled={!selectedNodeId} onClick={() => setReplayOpen(true)}>Replay from node</Button>
      </div>
      {(run.status as string) === "paused" && <div className="rounded-md border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm text-yellow-800">Run is paused waiting for approval.</div>}
      <div className="grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="space-y-3">
          <h2 className="text-sm font-medium">Grid</h2>
          <GridView rows={grid.rows} runs={grid.runs} cells={grid.cells} onSelectCell={(cell) => setSelectedNodeId(cell.nodeId)} />
        </aside>
        <Tabs defaultValue="graph" className="min-w-0">
          <TabsHeader tabs={[
            { value: "graph", label: "Graph" },
            { value: "tasks", label: "Task Instances" },
            { value: "events", label: "Events" },
            { value: "code", label: "Code" },
            { value: "side-effects", label: "Side-effects" },
            { value: "replays", label: "Replays" },
            { value: "details", label: "Details" },
          ]} />
          <TabsContent value="graph"><RunDag dag={dag.data} onSelectNode={setSelectedNodeId} /></TabsContent>
          <TabsContent value="tasks"><TaskTable nodes={dag.data.nodes} runId={runId} /></TabsContent>
          <TabsContent value="events"><EmptyCard title="Events" body="Live event archive is consumed through SSE and reflected in the DAG state." /></TabsContent>
          <TabsContent value="code"><EmptyCard title="Prompt" body={run.original_prompt} /></TabsContent>
          <TabsContent value="side-effects"><Card><CardHeader><CardTitle>Side-effect ledger</CardTitle></CardHeader><CardContent><SideEffectLog sideEffects={dag.data.side_effects ?? []} /></CardContent></Card></TabsContent>
          <TabsContent value="replays"><EmptyCard title="Replay history" body="Replay attempts will appear when the backend exposes a list endpoint." /></TabsContent>
          <TabsContent value="details"><EmptyCard title="Run details" body={JSON.stringify(run, null, 2)} /></TabsContent>
        </Tabs>
      </div>
      <NodePanel runId={runId} node={selectedNode} open={Boolean(selectedNodeId)} onOpenChange={(open) => !open && setSelectedNodeId(null)} />
      <ReplayModal runId={runId} nodeId={selectedNodeId} open={replayOpen} onOpenChange={setReplayOpen} />
    </div>
  );
}

function TaskTable({ nodes, runId }: { nodes: any[]; runId: string }) {
  return (
    <Card>
      <CardHeader><CardTitle>Task instances</CardTitle></CardHeader>
      <CardContent>
        <Table>
          <TableHeader><TableRow><TableHead>Node</TableHead><TableHead>Status</TableHead><TableHead>Timeline</TableHead><TableHead>Duration</TableHead></TableRow></TableHeader>
          <TableBody>{nodes.map((node) => <TableRow key={node.id}><TableCell><Link href={`/runs/${runId}/nodes/${node.id}`} className="text-blue-600 underline">{node.label}</Link></TableCell><TableCell><StatusPill status={node.status} /></TableCell><TableCell><MiniGantt startedAt={node.started_at} endedAt={node.ended_at} durationMs={node.duration_ms} policy={node.recovery_policy} /></TableCell><TableCell>{formatDuration(node.duration_ms)}</TableCell></TableRow>)}</TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

function EmptyCard({ title, body }: { title: string; body?: string }) {
  return <Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent><pre className="whitespace-pre-wrap text-sm text-muted-foreground">{body ?? "No data."}</pre></CardContent></Card>;
}
