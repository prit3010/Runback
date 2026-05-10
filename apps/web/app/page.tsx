"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listFlows, listRunners, listRuns } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusPill } from "@/components/status-pill";
import { HealthRow } from "@/components/health-row";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const runs = useQuery({ queryKey: ["runs"], queryFn: () => listRuns() });
  const flows = useQuery({ queryKey: ["flows"], queryFn: () => listFlows() });
  const runners = useQuery({ queryKey: ["runners"], queryFn: () => listRunners() });
  const recentRuns = runs.data?.slice(0, 8) ?? [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Run health, recent execution, and flow inventory.</p>
        </div>
        <Button asChild>
          <Link href="/flows/new">New flow</Link>
        </Button>
      </div>
      <HealthRow runners={runners.data ?? []} />
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Runs</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{runs.data?.length ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Flows</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{flows.data?.length ?? 0}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Runners</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{runners.data?.length ?? 0}</CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Recent runs</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Prompt</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentRuns.map((run) => (
                <TableRow key={run.id}>
                  <TableCell>
                    <Link className="font-mono text-xs text-blue-600 underline" href={`/runs/${run.id}`}>
                      {run.id}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <StatusPill status={run.status} />
                  </TableCell>
                  <TableCell>{formatDateTime(run.started_at ?? run.created_at)}</TableCell>
                  <TableCell className="max-w-md truncate">{run.original_prompt}</TableCell>
                </TableRow>
              ))}
              {recentRuns.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-muted-foreground">No runs yet.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
