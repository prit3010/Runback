"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listRuns } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { FilterBar } from "@/components/filter-bar";
import { StatusPill } from "@/components/status-pill";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function RunsPage() {
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => listRuns() });
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Runs</h1>
        <p className="text-sm text-muted-foreground">Every ad-hoc, scheduled, and registered flow execution.</p>
      </div>
      <FilterBar placeholder="Search runs" chips={["running", "failed", "success", "queued"]} />
      <Card>
        <CardHeader>
          <CardTitle>Run history</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Kind</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Prompt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(runs.data ?? []).map((run) => (
                <TableRow key={run.id}>
                  <TableCell><Link className="font-mono text-xs text-blue-600 underline" href={`/runs/${run.id}`}>{run.id}</Link></TableCell>
                  <TableCell><StatusPill status={run.status} /></TableCell>
                  <TableCell>{run.run_kind}</TableCell>
                  <TableCell>{formatDateTime(run.created_at)}</TableCell>
                  <TableCell className="max-w-lg truncate">{run.original_prompt}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
