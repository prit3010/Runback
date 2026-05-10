"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listFlows, listRuns } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { FilterBar } from "@/components/filter-bar";
import { RunsSparkline } from "@/components/runs-sparkline";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function FlowsPage() {
  const flows = useQuery({ queryKey: ["flows"], queryFn: () => listFlows() });
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => listRuns() });
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Flows</h1>
          <p className="text-sm text-muted-foreground">Reusable agent tasks and their recent run health.</p>
        </div>
        <Button asChild><Link href="/flows/new">New flow</Link></Button>
      </div>
      <FilterBar placeholder="Search flows" chips={["enabled", "disabled"]} />
      <Card>
        <CardHeader><CardTitle>Flow inventory</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Recent runs</TableHead>
                <TableHead>Repo</TableHead>
                <TableHead>Updated</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(flows.data ?? []).map((flow) => (
                <TableRow key={flow.id}>
                  <TableCell><Link className="font-medium text-blue-600 underline" href={`/flows/${flow.id}`}>{flow.name}</Link></TableCell>
                  <TableCell><RunsSparkline runs={(runs.data ?? []).filter((run) => run.flow_id === flow.id)} /></TableCell>
                  <TableCell className="font-mono text-xs">{flow.repo_path}</TableCell>
                  <TableCell>{formatDateTime(flow.updated_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
